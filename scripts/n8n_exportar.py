"""Exporta los workflows de n8n a `n8n/workflows/` (versionados en este repo).

Uso (desde fme-backend, con el Python del host; no necesita el venv):
    python scripts/n8n_exportar.py            # exporta/actualiza todos los que no estén excluidos
    python scripts/n8n_exportar.py --podar    # además borra archivos de workflows que ya no existen en n8n
    python scripts/n8n_exportar.py --verificar  # no escribe; sale con código 1 si el repo no está al día

Credenciales de la API de n8n (en este orden):
  1. variables de entorno N8N_API_URL y N8N_API_KEY
  2. ~/.claude.json → mcpServers.n8n-effi4tech.env (la config del MCP de n8n)

Reglas:
- Se exportan TODOS los workflows salvo los listados en `n8n/excluir.json` (otros productos con su propio repo).
  Un workflow nuevo queda incluido automáticamente.
- Secretos: los valores de headers/parámetros cuyo nombre parece clave (api key, token, authorization, password,
  secret) se reemplazan por `__SECRETO__:<nombre>` y se avisa. Las credenciales de n8n (SMTP, Gemini, etc.) viajan
  solo como referencia {id, name}, nunca su contenido. Al reimportar hay que volver a poner esos valores en n8n.
- Formato estable para que los diffs muestren solo cambios reales: sin fechas ni versionId, claves ordenadas.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "n8n"
DIR_WORKFLOWS = RAIZ / "workflows"
ARCHIVO_EXCLUIR = RAIZ / "excluir.json"
CAMPOS = ("id", "name", "active", "nodes", "connections", "settings", "pinData", "tags")
RE_SECRETO = re.compile(r"(api[-_ ]?key|token|secret|password|passwd|authorization|bearer|x-api-key)", re.I)
MARCADOR = "__SECRETO__"


def credenciales() -> tuple[str, str]:
    url, key = os.getenv("N8N_API_URL"), os.getenv("N8N_API_KEY")
    if not (url and key):
        cfg = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
        env = cfg.get("mcpServers", {}).get("n8n-effi4tech", {}).get("env", {})
        url, key = url or env.get("N8N_API_URL"), key or env.get("N8N_API_KEY")
    if not (url and key):
        sys.exit("Falta N8N_API_URL / N8N_API_KEY (variables de entorno o MCP n8n-effi4tech en ~/.claude.json)")
    return url.rstrip("/") + "/api/v1", key


def api(base: str, key: str, ruta: str) -> dict:
    req = urllib.request.Request(base + ruta, headers={"X-N8N-API-KEY": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def listar(base: str, key: str) -> list[dict]:
    salida, cursor = [], None
    while True:
        d = api(base, key, "/workflows?limit=100" + (f"&cursor={cursor}" if cursor else ""))
        salida += d.get("data", [])
        cursor = d.get("nextCursor")
        if not cursor:
            return salida


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60] or "workflow"


def ocultar_secretos(obj, ruta: str, avisos: list[str]):
    """Reemplaza valores sensibles en parámetros de nodos. Devuelve el objeto modificado."""
    if isinstance(obj, dict):
        # pares {name: "X-API-Key", value: "..."} (headers, query params, body params)
        if isinstance(obj.get("name"), str) and "value" in obj and RE_SECRETO.search(obj["name"]):
            v = obj["value"]
            if isinstance(v, str) and v and not v.startswith("={{") and not v.startswith(MARCADOR):
                obj["value"] = f"{MARCADOR}:{obj['name']}"
                avisos.append(f"{ruta}: {obj['name']}")
        for k, v in list(obj.items()):
            if (isinstance(v, str) and v and RE_SECRETO.search(k) and not v.startswith("={{")
                    and not v.startswith(MARCADOR) and k not in ("name", "type", "authentication")):
                obj[k] = f"{MARCADOR}:{k}"
                avisos.append(f"{ruta}.{k}")
            else:
                ocultar_secretos(v, f"{ruta}.{k}", avisos)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            ocultar_secretos(x, f"{ruta}[{i}]", avisos)
    return obj


def normalizar(wf: dict, avisos: list[str]) -> dict:
    d = {k: wf[k] for k in CAMPOS if k in wf and wf[k] not in (None, {}, [])}
    if "tags" in d:
        d["tags"] = sorted(t["name"] for t in d["tags"])
    for n in d.get("nodes", []):
        n.pop("id", None)   # cambia al reimportar; n8n conecta por nombre
        ocultar_secretos(n.get("parameters", {}), n.get("name", "?"), avisos)
    d.get("settings", {}).pop("availableInMCP", None)
    return d


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--podar", action="store_true", help="borra archivos de workflows que ya no existen en n8n")
    ap.add_argument("--verificar", action="store_true", help="no escribe; código 1 si hay diferencias")
    args = ap.parse_args()

    base, key = credenciales()
    excluidos = {e["id"]: e for e in json.loads(ARCHIVO_EXCLUIR.read_text(encoding="utf-8"))} \
        if ARCHIVO_EXCLUIR.exists() else {}
    DIR_WORKFLOWS.mkdir(parents=True, exist_ok=True)
    existentes = {p.name: p for p in DIR_WORKFLOWS.glob("*.json")}
    escritos, cambios = set(), 0

    for resumen in sorted(listar(base, key), key=lambda w: w["name"]):
        if resumen["id"] in excluidos:
            print(f"  · excluido  {resumen['name']} ({resumen['id']}): {excluidos[resumen['id']].get('motivo', '')}")
            continue
        avisos: list[str] = []
        wf = normalizar(api(base, key, f"/workflows/{resumen['id']}"), avisos)
        nombre = f"{slug(wf['name'])}--{wf['id']}.json"
        texto = json.dumps(wf, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        destino = DIR_WORKFLOWS / nombre
        previo = destino.read_text(encoding="utf-8") if destino.exists() else None
        # si el workflow cambió de nombre, el archivo viejo con el mismo id se reemplaza
        viejos = [p for n, p in existentes.items() if n.endswith(f"--{wf['id']}.json") and n != nombre]
        estado = "sin cambios" if previo == texto and not viejos else ("nuevo" if previo is None else "actualizado")
        if estado != "sin cambios":
            cambios += 1
            if not args.verificar:
                destino.write_text(texto, encoding="utf-8")
                for p in viejos:
                    p.unlink()
        escritos.add(nombre)
        marca = "✓" if wf.get("active") else "○"
        print(f"  {marca} {estado:12} {nombre}")
        for a in avisos:
            print(f"      ⚠ secreto ocultado en {a}")

    huerfanos = [p for n, p in existentes.items() if n not in escritos and p.exists()]
    for p in huerfanos:
        if args.podar and not args.verificar:
            p.unlink()
            print(f"  ✗ borrado      {p.name} (ya no existe en n8n)")
        else:
            print(f"  ? huérfano     {p.name} (no existe en n8n; usa --podar para borrarlo)")
    cambios += len(huerfanos) if args.podar else 0

    if args.verificar:
        print("\nRepo al día con n8n." if cambios == 0 else f"\n{cambios} workflow(s) difieren de n8n: ejecuta el export.")
        sys.exit(1 if cambios else 0)
    print(f"\nListo: {len(escritos)} workflows en {DIR_WORKFLOWS.relative_to(RAIZ.parent)} ({cambios} con cambios).")


if __name__ == "__main__":
    main()
