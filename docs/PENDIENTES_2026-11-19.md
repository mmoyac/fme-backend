# Pendientes tras el deploy del 2026-11-19

Deploy que sube a producción (push a `main` de fme-backend, fme-backoffice y fme-landing):

| Change OpenSpec | Repo | Qué trae |
|---|---|---|
| `add-delivery-por-comuna` | fme-backend (+ backoffice, landing) | Retiro o delivery por comuna en el checkout, tarifas por comuna, autocompletar de dirección con Mapbox, modo demo de pasarelas |
| `add-etiquetas-desde-produccion` | fme-backoffice | Botón 🏷️ en OP finalizada para imprimir etiquetas nutricionales (lote OP-<id>) |
| `add-control-etiquetas-op` | fme-backend (+ backoffice) | Marca manual "etiquetas impresas" en la OP, badge y filtro "Etiquetas" en Producción |
| `add-formato-etiqueta-75x62` | fme-backoffice (+ backend) | Diseño de etiqueta del cliente (`docs/etiquetado/etiqueta.jpeg`) en 75 × 62 y 100 × 62 mm, sellos a tamaño legal, datos de etiqueta por tenant |
| (sin change) | fme-backoffice | Modal de detalle de Solicitudes con scroll; filtros en la lista de Producción |

Migraciones que se aplican solas en el deploy: `d5a1c7e3f9b2` (tarifas de delivery), `e7b3d9a1c5f2` (etiquetas impresas en OP), `f2c8a4e6b1d3` (origen, comuna y logo de etiqueta en `configuracion_landing`).

## 1. Configuración en producción (después del deploy)

- [x] **Tenant 1 (Masas Estación) → Configuración → Landing** (cargado vía API el 2026-11-19, con razón social, resolución, teléfono +56 9 3933 8558 y dirección Barros Luco 1980 local 5 tomados de etiqueta.jpeg):
  - Origen (etiqueta): `Producto Chileno`
  - Comuna (pie de etiqueta): `Santiago, Lampa`
  - Logo para etiquetas: subir `fme-backend/docs/etiquetado/logo-etiqueta-masas-estacion.png` (versión B/N sacada del archivo de P-touch). Sin esto la etiqueta sale sin logo: el `logo_url` actual (`/logo.png`) es una ruta del sitio landing que el backoffice no puede abrir.
- [ ] **Tarifas de delivery**: cargar las comunas y costos en Mantenedores → Tarifas de delivery. Sin tarifas, el checkout no ofrece delivery a esa comuna.
- [ ] **Mapbox** (opcional): secreto de GitHub `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` en el repo fme-landing (build) y `MAPBOX_ACCESS_TOKEN` en el `.env` del VPS (backend). Sin ellos no hay autocompletar y las direcciones quedan "no verificadas".
- [ ] **Modo demo de pasarelas** (opcional): `PASARELAS_CLAVE_DEMO` en el `.env` del VPS. Vacía = desactivado.

## 1b. Pasarelas y modo demo (actualizado 2026-11-19)

- [ ] **Pasarela de producción**: el tenant 1 solo tiene Khipu en ambiente INTEGRACIÓN, que en prod no se ofrece (por eso el checkout no muestra pasarela). Cargar credenciales de producción de Khipu (u otra) en Configuración → Pasarelas de pago con ambiente PRODUCCIÓN.
- [ ] **Demo en prod**: en el VPS (`/root/docker/masas-estacion`) agregar `PASARELAS_CLAVE_DEMO` al `.env`, recrear el backend y abrir `https://www.masasestacion.cl/?demo=<clave>`. Pagar con DemoBank (clave 1234) y cancelar el pedido después. Quitar la clave al terminar.
- [ ] **Interruptor "Permitir pedidos sin pago en línea"** (change `add-interruptor-pedido-sin-pago`, sin subir aún): apagarlo para el tenant 1 en prod solo cuando haya pasarela de producción; si no, la tienda no recibe pedidos web.

## 2. Pruebas pendientes

- [ ] **Etiquetas, impresión real** en la Brother QL-820NWB (tarea 4.2 de `add-formato-etiqueta-75x62`): comparar con la etiqueta de P-touch, ajustar tamaño de letra/márgenes si hace falta y comprobar que el lector lee el código de barras.
- [ ] **Etiquetas, criterio legal**: que el asesor sanitario del cliente confirme el tamaño de sellos usado (1,5 cm en 75 × 62; 2,0 cm en 100 × 62, Manual MINSAL pág. 30) y que el área de la etiqueta corresponde a la cara principal del envase.
- [ ] **Delivery, tareas 6.1 y 6.2** de `add-delivery-por-comuna`: pago con DemoBank de un pedido con delivery en modo producción + demo; y que Cobranza muestre productos + delivery en un pedido "sin pagar ahora".
- [ ] **Control de etiquetas**: el caso "marcar una OP no finalizada → 400" no se probó (no había OP abiertas en local).
- [ ] **Etiquetas, regla < 3 g de grasa por porción** (sin desglose obligatorio de grasas): no se probó con datos reales.

## 3. Reglas de etiquetas acordadas con el usuario

- El formato 75 × 62 mm (rollo continuo de 62 mm) es el del ejemplo del cliente; el 62 × 100 (DK-11202) usa el mismo diseño adaptado.
- Sellos "ALTO EN" a tamaño legal según el área de la etiqueta, **máximo 2 por fila, pegados a la derecha**, tabla debajo. Nunca 3–4 en fila horizontal.
- 4 sellos caben en 75 × 62 (tabla compacta). En 100 × 62 los sellos son de 2 cm y 3–4 no caben: la impresión se bloquea y pide usar 75 × 62.
- Vencimiento en blanco para completar a mano; lote y elaboración se completan solo si se imprime desde una OP.
- La tabla siempre muestra azúcares totales y grasas trans (obligatorios, Manual pág. 19).
- Marca "etiquetas impresas" manual (no automática al generar el PDF).

## 4. Seguridad (urgente)

- [ ] **Cambiar la contraseña de `admin@fme.cl` en producción**: hoy es `admin` y está escrita en varios scripts de `fme-backend/scripts/`. Se usó el 2026-11-18 para leer una solicitud de prod y funcionó.
- [ ] Sacar credenciales y tokens de los scripts (ej. `scripts/copiar_paletas_colores.py` tiene un token de prod en el código) y leerlos desde variables de entorno.

## 5. Changes OpenSpec sin archivar

No archivar sin el OK del usuario tras probar en prod:
`add-delivery-por-comuna`, `add-control-etiquetas-op` (fme-backend); `add-etiquetas-desde-produccion`, `add-formato-etiqueta-75x62` (fme-backoffice).

## 6. Archivos que quedaron fuera del commit (a decidir)

- `fme-backend/fix_pedido_124.sql` — SQL puntual, no versionado.
- `fme-backend/docs/masas estacion sofware sugerencias.docx` y `docs/resumen reunion 16-11-26.docx` — documentos del cliente.
- `fme-backend/static/uploads/landing/logo_1_*.png` — logo subido en el entorno local (en prod se sube desde la pantalla).

## 7. Notas del entorno local

- Si `fme-backend`/`fme-postgres` se detienen (reinicio de Docker/PC), el backoffice da `ECONNREFUSED`: `docker start fme-postgres fme-backend`.
- La recarga automática del backend a veces queda trabada en "Waiting for connections to close" al cambiar `models.py`: `docker restart fme-backend`.
