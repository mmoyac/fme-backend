"""
Servicio para manejo de tenants y detección automática por dominio.
"""
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.models import Tenant


def validar_tenant_activo(tenant: Tenant) -> None:
    """
    Valida que el tenant esté activo.
    
    Args:
        tenant: Tenant a validar
        
    Raises:
        HTTPException: Si el tenant está inactivo
    """
    if not tenant or not tenant.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está suspendida. Por favor contacta a soporte para más información."
        )


def get_tenant_from_request(request: Request, db: Session) -> Optional[Tenant]:
    """
    Detecta el tenant actual basándose en el dominio de la petición.
    
    Soporta:
    - Dominios completos: masasestacion.cl, www.masasestacion.cl
    - Subdominios: elolivo.masasestacion.cl, admin.masasestacion.cl
    - Subdominios SaaS: masasestacion.effitech.cl, elolivo.effitech.cl
    - Desarrollo local: masasestacion.local, elolivo.local
    - Header X-Forwarded-Host para proxies/desarrollo
    - Fallback: localhost → tenant_id=1
    
    Args:
        request: Request de FastAPI con headers
        db: Sesión de base de datos
        
    Returns:
        Tenant encontrado o None
    """
    # Obtener hostname: primero X-Forwarded-Host, luego Host
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
    hostname = host.split(":")[0]  # Remover puerto si existe
    
    print(f"🔍 Detectando tenant desde hostname: {hostname}")
    
    # 1. Intentar match exacto por dominio_principal
    tenant = db.query(Tenant).filter(
        Tenant.dominio_principal == hostname
    ).first()
    
    if tenant:
        print(f"✅ Tenant encontrado por dominio exacto: {tenant.nombre} (ID: {tenant.id})")
        return tenant
    
    # 1b. Si tiene www, intentar sin www (www.masasestacion.cl → masasestacion.cl)
    if hostname.startswith('www.'):
        hostname_sin_www = hostname[4:]  # Remover 'www.'
        tenant = db.query(Tenant).filter(
            Tenant.dominio_principal == hostname_sin_www
        ).first()
        
        if tenant:
            print(f"✅ Tenant encontrado por dominio sin www: {tenant.nombre} (ID: {tenant.id})")
            return tenant
    
    # 1c. Si empieza con prefijo administrativo (admin., api., backoffice.), extraer dominio base
    # Ej: admin.elolivo.lexastech.cl → buscar por elolivo.lexastech.cl
    parts = hostname.split('.')
    if len(parts) >= 3 and parts[0] in ['admin', 'api', 'www', 'backoffice']:
        dominio_base = '.'.join(parts[1:])  # Remover primer segmento
        tenant = db.query(Tenant).filter(
            Tenant.dominio_principal == dominio_base
        ).first()
        
        if tenant:
            print(f"✅ Tenant encontrado por dominio base (sin prefijo {parts[0]}): {tenant.nombre} (ID: {tenant.id})")
            return tenant
    
    # 2. Si es localhost, retornar tenant por defecto (Masas Estación)
    if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
        tenant = db.query(Tenant).filter(Tenant.id == 1).first()
        print(f"🏠 Localhost detectado, usando tenant por defecto: {tenant.nombre if tenant else 'None'}")
        return tenant
    
    # 3. Para desarrollo local (.local), buscar por primer segmento
    # Ej: masasestacion.local → buscar tenant con codigo='masas-estacion'
    # Ej: admin.elolivo.local → extraer 'elolivo' y buscar por codigo='elolivo'
    if hostname.endswith('.local'):
        codigo = hostname.replace('.local', '')
        
        # Si empieza con 'admin.', 'api.', etc., extraer el segundo segmento
        if '.' in codigo:
            parts = codigo.split('.')
            if parts[0] in ['admin', 'api', 'www', 'backoffice']:
                codigo = parts[1] if len(parts) > 1 else codigo
        
        tenant = db.query(Tenant).filter(
            Tenant.codigo == codigo.replace('.', '-')
        ).first()
        
        # Fallback: buscar por subdomain si no se encontró por codigo
        if not tenant:
            tenant = db.query(Tenant).filter(
                Tenant.subdomain == codigo
            ).first()
        
        if tenant:
            print(f"✅ Tenant encontrado por desarrollo .local: {tenant.nombre} (ID: {tenant.id})")
            return tenant
    
    # 4. Buscar por subdominio
    # Ej: elolivo.masasestacion.cl → buscar tenant con subdomain='elolivo'
    parts = hostname.split('.')
    if len(parts) >= 3:  # subdominio.dominio.tld
        subdomain = parts[0]
        tenant = db.query(Tenant).filter(
            Tenant.subdomain == subdomain
        ).first()
        
        if tenant:
            print(f"✅ Tenant encontrado por subdominio: {tenant.nombre} (ID: {tenant.id})")
            return tenant
    
    # 5. Si no se encontró tenant, lanzar error explícito
    from fastapi import HTTPException
    print(f"❌ Dominio no registrado: {hostname}. Lanzando error 404.")
    raise HTTPException(status_code=404, detail=f"Dominio '{hostname}' no registrado como tenant.")


def get_tenant_id_from_request(request: Request, db: Session) -> int:
    """
    Obtiene el tenant_id desde la petición.
    Wrapper conveniente que retorna el ID directamente.
    
    Args:
        request: Request de FastAPI
        db: Sesión de base de datos
        
    Returns:
        tenant_id (default: 1 si no se encuentra)
    """
    tenant = get_tenant_from_request(request, db)
    return tenant.id if tenant else 1


def obtener_siguiente_numero_pedido(db: Session, tenant_id: int) -> str:
    """
    Genera el siguiente número de pedido único para el tenant.
    
    Formato: {CODIGO}-{AÑO}-{CORRELATIVO:05d}
    Ejemplos: MASAS-ESTACION-2026-00001, EL-OLIVO-2026-00042
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        
    Returns:
        Número de pedido formateado (ej: "MASAS-ESTACION-2026-00001")
        
    Raises:
        ValueError: Si el tenant no existe
    """
    # Incrementar correlativo atómicamente usando UPDATE ... RETURNING
    query = text("""
        UPDATE tenants
        SET correlativo_pedido = correlativo_pedido + 1
        WHERE id = :tenant_id
        RETURNING codigo, correlativo_pedido
    """)
    
    result = db.execute(query, {"tenant_id": tenant_id})
    row = result.fetchone()
    
    if not row:
        raise ValueError(f"Tenant con ID {tenant_id} no existe")
    
    codigo_tenant = row[0]  # codigo del tenant (ej: 'masas-estacion')
    correlativo = row[1]     # nuevo correlativo (ej: 1, 2, 3...)
    
    # Obtener año actual
    year = datetime.now().year
    
    # Usar el codigo completo en uppercase (garantiza unicidad ya que codigo es UNIQUE en tenants)
    prefijo = codigo_tenant.upper()
    
    # Formatear numero_pedido
    numero_pedido = f"{prefijo}-{year}-{correlativo:05d}"
    
    db.commit()  # Confirmar el UPDATE

    print(f"✅ Número de pedido generado: {numero_pedido} (Tenant: {codigo_tenant})")

    return numero_pedido


def obtener_siguiente_numero_cotizacion(db: Session, tenant_id: int) -> str:
    """
    Genera el siguiente número de cotización único para el tenant.

    Formato: {CODIGO}-COT-{AÑO}-{CORRELATIVO:05d}
    Ejemplo: MASAS-ESTACION-COT-2026-00001
    """
    query = text("""
        UPDATE tenants
        SET correlativo_cotizacion = correlativo_cotizacion + 1
        WHERE id = :tenant_id
        RETURNING codigo, correlativo_cotizacion
    """)
    result = db.execute(query, {"tenant_id": tenant_id})
    row = result.fetchone()
    if not row:
        raise ValueError(f"Tenant con ID {tenant_id} no existe")

    prefijo = row[0].upper()
    correlativo = row[1]
    year = datetime.now().year
    numero = f"{prefijo}-COT-{year}-{correlativo:05d}"
    db.commit()
    return numero


def obtener_siguiente_numero_ot(db: Session, tenant_id: int) -> str:
    """
    Genera el siguiente número de Orden de Trabajo único para el tenant.

    Formato: {CODIGO}-OT-{AÑO}-{CORRELATIVO:05d}
    Ejemplo: MASAS-ESTACION-OT-2026-00001
    """
    query = text("""
        UPDATE tenants
        SET correlativo_ot = correlativo_ot + 1
        WHERE id = :tenant_id
        RETURNING codigo, correlativo_ot
    """)
    result = db.execute(query, {"tenant_id": tenant_id})
    row = result.fetchone()
    if not row:
        raise ValueError(f"Tenant con ID {tenant_id} no existe")

    prefijo = row[0].upper()
    correlativo = row[1]
    year = datetime.now().year
    numero = f"{prefijo}-OT-{year}-{correlativo:05d}"
    db.commit()
    return numero
