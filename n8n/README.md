# Workflows de n8n (FME)

Copia versionada de los workflows de n8n (`https://n8n.effi4tech.cl`) que usa FME: correos transaccionales,
código de verificación del checkout, limpieza de notificaciones, agente de chat.
**n8n es la fuente de ejecución; este directorio es el respaldo y el historial de cambios.**

## Regla

Todo workflow que se cree o modifique en n8n se exporta y se commitea en el mismo cambio que lo usa:

```bash
python scripts/n8n_exportar.py            # exporta/actualiza (incluye automáticamente los workflows nuevos)
python scripts/n8n_exportar.py --podar    # además borra los que ya no existen en n8n
python scripts/n8n_exportar.py --verificar  # solo revisa si el repo está al día (código 1 si no)
```

Además, cada workflow nuevo o modificado **debe quedar registrado en la spec `integracion-n8n`** (`openspec/specs/integracion-n8n/spec.md`) con un change de OpenSpec: nombre, ID, disparador, dirección, payload y si es crítico.

El script usa `N8N_API_URL`/`N8N_API_KEY`, o si no están, la config del MCP `n8n-effi4tech` en `~/.claude.json`.

## Contenido

| Archivo | Para qué | Lo dispara |
|---|---|---|
| `email-confirmacion-compra-clientes--8k3qYK9sfm1NEA1R` | Correo de pedido confirmado/pagado | `services/webhook_service.py` → `pedido-confirmado` |
| `email-entrega-pedido-clientes--AqmOmlWJETP1WGAZ` | Correo de pedido entregado | hoja de ruta → `pedido-entregado` |
| `fme-codigo-de-verificacion-de-correo--VxFbcw9rerVw1ByA` | Código de 6 dígitos del checkout. **Crítico**: sin él la tienda no crea pedidos | `services/verificacion_email.py` → `verificacion-email` |
| `masas-estacion-email-cotizacion-*` | Correos de cotización creada / enviada / aceptada | `routers/cotizaciones.py` |
| `limpieza-notificaciones-fme-backend--utisRGKMxY1kKAjJ` | Cron nocturno → `DELETE /api/notifications/cleanup` | n8n (cron) |
| `masas-estacion-agente-chat--n26TaZhlycsY7xcA` | Agente de chat con IA (Gemini) | chat de n8n |
| `masas-estacion-catalogo-de-productos--Ojcal1wIkrB0i1C5` | Webhook de catálogo (inactivo) | — |

`excluir.json` lista los workflows del mismo n8n que pertenecen a otros productos (EffiCheck, Effiguard) y no se
exportan aquí.

## Secretos

- Las credenciales de n8n (SMTP, Gemini, …) se exportan solo como referencia `{id, name}`; su contenido nunca sale
  de n8n.
- Si un nodo tiene una clave escrita a mano (p. ej. header `X-API-Key`), el export la reemplaza por
  `__SECRETO__:<nombre>`. **Al reimportar un workflow hay que volver a poner ese valor en n8n.** Mejor aún: mover
  esas claves a una credencial de n8n (tipo *Header Auth*) para que no estén en los nodos.

## Restaurar / importar

En n8n: *Workflows → Import from file* con el JSON. Luego revisar credenciales (por nombre), reemplazar los
`__SECRETO__` y activar. El `id` del archivo es el del workflow original; al importar en otra instancia se
asigna uno nuevo.
