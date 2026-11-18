## 1. Baseline (documentación de lo existente)
- [x] 1.1 Inventario de workflows y contratos de webhooks (design.md)
- [x] 1.2 Spec `integracion-n8n` (envío fire-and-forget, payloads, verificación crítica, flujos n8n→FME, versionado, secretos)
- [x] 1.4 Regla de registro: todo workflow nuevo/modificado/eliminado se registra en la spec `integracion-n8n` vía change (requisito en la spec + reglas en `openspec/config.yaml` + `CLAUDE.md` + `n8n/README.md`)
- [x] 1.3 Versionado implementado: `scripts/n8n_exportar.py`, `n8n/workflows/` (9 workflows), `n8n/excluir.json`, `n8n/README.md`, regla en `CLAUDE.md`

## 2. Deuda (changes futuros, no en este)
- [ ] 2.1 URLs de webhooks desde variables de entorno (hoy escritas en `services/webhook_service.py`)
- [ ] 2.2 Mover la API key del nodo HTTP de "Limpieza Notificaciones" a una credencial n8n *Header Auth*
- [ ] 2.3 Reintentos o registro persistente de envíos fallidos a n8n
- [ ] 2.4 `seguimiento_url` por tenant (hoy fija a `seguimiento.lexastech.cl`)

## 3. Cierre
- [ ] 3.1 Revisión del usuario y archivo del change (`openspec archive document-integracion-n8n`) → crea `openspec/specs/integracion-n8n/spec.md`
