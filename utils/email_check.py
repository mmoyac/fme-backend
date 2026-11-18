"""Validación del correo del cliente en el checkout de la tienda.

Tres capas, sin fricción para el cliente:
1. Formato real (email_validator, no solo "tiene @").
2. Dominio que existe y recibe correo (DNS MX/A). Si el DNS no responde a tiempo, NO se bloquea la compra.
3. Sugerencia de corrección de errores de tipeo en dominios comunes ("gmial.com" → "gmail.com"). Ojo: varios dominios
   con typo existen y tienen MX (p. ej. gmial.com), así que la capa 2 no los atrapa; por eso la sugerencia.

No prueba que el correo sea del cliente (eso exigiría un código de verificación).
"""
from email_validator import EmailNotValidError, EmailSyntaxError, EmailUndeliverableError, validate_email

TIMEOUT_DNS_S = 4

DOMINIOS_COMUNES = (
    "gmail.com", "hotmail.com", "hotmail.es", "hotmail.cl", "outlook.com", "outlook.es", "live.com", "live.cl",
    "yahoo.com", "yahoo.es", "yahoo.cl", "icloud.com", "me.com", "msn.com", "protonmail.com", "proton.me",
)
# Errores frecuentes que no siempre quedan a distancia 1-2 (o que lo están de dos dominios válidos)
TYPOS_CONOCIDOS = {
    "gmail.cl": "gmail.com", "gmail.co": "gmail.com", "gmai.com": "gmail.com", "gmial.com": "gmail.com",
    "gamil.com": "gmail.com", "gmal.com": "gmail.com", "gnail.com": "gmail.com", "gmail.con": "gmail.com",
    "hotmal.com": "hotmail.com", "hotmial.com": "hotmail.com", "hotmai.com": "hotmail.com", "hotmail.con": "hotmail.com",
    "outlok.com": "outlook.com", "outllok.com": "outlook.com", "yaho.com": "yahoo.com", "yahoo.con": "yahoo.com",
    "icloud.con": "icloud.com", "iclod.com": "icloud.com",
}


def _distancia(a: str, b: str) -> int:
    """Levenshtein (dominios cortos: basta la versión simple)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def sugerir_dominio(dominio: str) -> str | None:
    d = dominio.lower()
    if d in DOMINIOS_COMUNES:
        return None
    if d in TYPOS_CONOCIDOS:
        return TYPOS_CONOCIDOS[d]
    candidatos = sorted((_distancia(d, c), c) for c in DOMINIOS_COMUNES)
    dist, mejor = candidatos[0]
    if dist <= 2 and (len(candidatos) < 2 or candidatos[1][0] > dist):   # sin empate: sugerencia inequívoca
        return mejor
    return None


def validar_email_cliente(email: str, verificar_dominio: bool = True) -> dict:
    """{valido, email (normalizado), error, sugerencia}. `error` y `sugerencia` en español, aptos para el cliente."""
    texto = (email or "").strip()
    if not texto:
        return {"valido": False, "email": texto, "error": "Ingresa tu correo electrónico", "sugerencia": None}
    try:
        r = validate_email(texto, check_deliverability=verificar_dominio, timeout=TIMEOUT_DNS_S)
        normalizado = r.normalized
    except EmailUndeliverableError:
        dominio = texto.rsplit("@", 1)[-1]
        sug = sugerir_dominio(dominio)
        return {"valido": False, "email": texto,
                "error": f"El dominio «{dominio}» no existe o no recibe correos. Revisa que esté bien escrito.",
                "sugerencia": f"{texto.rsplit('@', 1)[0]}@{sug}" if sug else None}
    except EmailSyntaxError:
        return {"valido": False, "email": texto,
                "error": "El correo no tiene un formato válido (ejemplo: nombre@gmail.com)", "sugerencia": None}
    except EmailNotValidError:
        return {"valido": False, "email": texto, "error": "El correo no es válido", "sugerencia": None}
    except Exception:   # noqa: BLE001  DNS caído u otro problema de red: no se bloquea la compra por eso
        normalizado = texto
    local, dominio = normalizado.rsplit("@", 1)
    dominio = dominio.lower()
    sug = sugerir_dominio(dominio)
    return {"valido": True, "email": f"{local}@{dominio}", "error": None,
            "sugerencia": f"{local}@{sug}" if sug else None}
