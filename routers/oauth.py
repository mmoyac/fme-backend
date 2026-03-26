"""
Router para autenticación OAuth (Google, etc.).
Flujo: frontend redirige a /api/auth/google/login → Google → /api/auth/google/callback → frontend con token
"""
import os
import json
import base64
from datetime import timedelta
from urllib.parse import urlparse, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User, UserOAuthAccount, Tenant, Role
from utils.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from services import tenant_service

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google/login")
async def google_login(frontend_url: str = "http://localhost:3001"):
    """
    Inicia el flujo OAuth con Google.
    El frontend llama a este endpoint pasando su propia URL base para que
    el callback sepa dónde redirigir con el token.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth no está configurado en este servidor")

    state_data = {"frontend_url": frontend_url}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    })

    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db),
):
    """
    Callback de Google OAuth.
    1. Intercambia el code por tokens con Google.
    2. Obtiene el perfil del usuario.
    3. Busca o crea el usuario en la BD.
    4. Genera nuestro JWT y redirige al frontend con él.
    """
    # Decodificar state para obtener el frontend_url
    frontend_url = "http://localhost:3001"
    if state:
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
            frontend_url = state_data.get("frontend_url", frontend_url)
        except Exception:
            pass

    callback_base = f"{frontend_url}/auth/callback"

    # Google reportó un error (ej: usuario canceló)
    if error or not code:
        return RedirectResponse(f"{callback_base}?error={error or 'cancelled'}")

    # Intercambiar code → access_token con Google
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_res = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
            if token_res.status_code != 200:
                return RedirectResponse(f"{callback_base}?error=token_exchange_failed")

            token_data = token_res.json()

            # Obtener perfil del usuario desde Google
            userinfo_res = await client.get(GOOGLE_USERINFO_URL, headers={
                "Authorization": f"Bearer {token_data['access_token']}"
            })
            if userinfo_res.status_code != 200:
                return RedirectResponse(f"{callback_base}?error=userinfo_failed")

            userinfo = userinfo_res.json()
    except httpx.TimeoutException:
        return RedirectResponse(f"{callback_base}?error=google_timeout")
    except httpx.RequestError:
        return RedirectResponse(f"{callback_base}?error=google_unreachable")

    google_id = userinfo.get("id")
    email = userinfo.get("email")
    nombre = userinfo.get("name") or email

    if not google_id or not email:
        return RedirectResponse(f"{callback_base}?error=invalid_userinfo")

    # Buscar si ya existe la cuenta OAuth vinculada
    oauth_account = db.query(UserOAuthAccount).filter(
        UserOAuthAccount.provider == "google",
        UserOAuthAccount.provider_id == google_id,
    ).first()

    if oauth_account:
        # Usuario ya vinculó Google antes → login directo
        user = oauth_account.user
        if not user or not user.is_active:
            return RedirectResponse(f"{callback_base}?error=user_inactive")
    else:
        # Primera vez con Google: detectar tenant por hostname del frontend
        parsed = urlparse(frontend_url)
        hostname = parsed.hostname or "localhost"

        tenant = _get_tenant_from_hostname(hostname, db)
        if not tenant:
            return RedirectResponse(f"{callback_base}?error=tenant_not_found")

        try:
            tenant_service.validar_tenant_activo(tenant)
        except Exception:
            return RedirectResponse(f"{callback_base}?error=tenant_inactive")

        # El usuario DEBE existir previamente en el sistema (creado por un admin)
        user = db.query(User).filter(
            User.email == email,
            User.tenant_id == tenant.id,
        ).first()

        if not user:
            return RedirectResponse(f"{callback_base}?error=user_not_registered")

        if not user.is_active:
            return RedirectResponse(f"{callback_base}?error=user_inactive")

        # Vincular Google a la cuenta existente (solo la primera vez)
        oauth_account = UserOAuthAccount(
            user_id=user.id,
            provider="google",
            provider_id=google_id,
            email=email,
        )
        db.add(oauth_account)
        db.commit()
        db.refresh(user)

    # Generar JWT igual que en login normal
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.nombre if user.role else None,
            "tenant_id": user.tenant_id,
            "is_superadmin": user.is_superadmin,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return RedirectResponse(f"{callback_base}?token={access_token}")


def _get_tenant_from_hostname(hostname: str, db: Session):
    """Detecta tenant por hostname (igual que tenant_service pero recibe string directo)."""
    from database.models import Tenant

    # Match exacto
    tenant = db.query(Tenant).filter(Tenant.dominio_principal == hostname).first()
    if tenant:
        return tenant

    # Sin www
    if hostname.startswith("www."):
        tenant = db.query(Tenant).filter(Tenant.dominio_principal == hostname[4:]).first()
        if tenant:
            return tenant

    # Sin prefijo admin/api/backoffice
    parts = hostname.split(".")
    if len(parts) >= 3 and parts[0] in ("admin", "api", "backoffice"):
        tenant = db.query(Tenant).filter(Tenant.dominio_principal == ".".join(parts[1:])).first()
        if tenant:
            return tenant

    # Por subdominio
    if len(parts) >= 2:
        subdomain = parts[0]
        tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
        if tenant:
            return tenant

    # Fallback: localhost → tenant 1
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        return db.query(Tenant).filter(Tenant.id == 1).first()

    return None
