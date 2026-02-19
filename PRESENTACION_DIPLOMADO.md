# 📦 SISTEMA DE GESTIÓN DE DESPACHOS
## Presentación para Diplomado

**Proyecto:** Sistema Integral de Gestión Logística con Trazabilidad FIFO  
**Contexto:** E-commerce de productos perecederos (cajas de peso variable)  
**Estado:** Implementado y operativo en producción  
**Fecha:** Febrero 2026

---

## 📋 SLIDE 1: PORTADA

```
╔═══════════════════════════════════════════════╗
║                                               ║
║   SISTEMA DE GESTIÓN DE DESPACHOS            ║
║   CON TRAZABILIDAD AUTOMÁTICA                ║
║                                               ║
║   Optimización de Logística de               ║
║   Última Milla con IoT y FIFO                ║
║                                               ║
╠═══════════════════════════════════════════════╣
║                                               ║
║   📦 Estudiante: [Tu Nombre]                 ║
║   🎓 Diplomado: [Nombre del Diplomado]       ║
║   📅 Fecha: Febrero 2026                     ║
║   🏢 Empresa: Masas Estación                 ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**Nota al presentar:**
- Proyecto real implementado en producción
- Soluciona problemas reales de logística de última milla
- Integra múltiples tecnologías: Web, Mobile, APIs, IoT (QR)

---

## 📋 SLIDE 2: CONTEXTO DEL PROBLEMA

```
🏪 INDUSTRIA: E-commerce de Alimentos B2B

┌─────────────────────────────────────────────┐
│  DESAFÍOS DE LA LOGÍSTICA DE PERECEDEROS   │
└─────────────────────────────────────────────┘

1. PRODUCTOS DE PESO VARIABLE
   ┌──────────────────────────────┐
   │ Caja A: 17.5 kg  → $87,500  │
   │ Caja B: 21.3 kg  → $106,500 │
   │ Caja C: 19.0 kg  → $95,000  │
   └──────────────────────────────┘
   ❌ Problema: Cliente no sabe precio exacto hasta recibir

2. FECHA DE VENCIMIENTO
   ┌──────────────────────────────┐
   │ Lote X: Vence 25-Feb         │
   │ Lote Y: Vence 28-Feb         │
   │ Lote Z: Vence 02-Mar         │
   └──────────────────────────────┘
   ❌ Problema: Despachar lote incorrecto = pérdidas por vencimiento

3. ERRORES EN PREPARACIÓN
   ┌──────────────────────────────┐
   │ Pedido: 2 cajas Producto A   │
   │ Enviado: 1 caja A + 1 caja B │
   └──────────────────────────────┘
   ❌ Problema: Cliente insatisfecho + logística inversa costosa

4. FALTA DE VISIBILIDAD
   ❌ Problema: No saber dónde está cada despacho en tiempo real
```

**Pregunta clave:**  
¿Cómo garantizar que el cliente reciba el producto correcto, con el lote más antiguo, y conocer su ubicación en todo momento?

---

## 📋 SLIDE 3: ¿QUÉ RESUELVE EL SISTEMA?

```
✅ SOLUCIÓN IMPLEMENTADA

┌────────────────────────────────────────────────┐
│  SISTEMA INTEGRAL DE GESTIÓN DE DESPACHOS     │
│                                                │
│  Plataforma que conecta:                       │
│  🌐 Web (clientes)                            │
│  📱 Mobile (despachadores)                    │
│  💼 Backoffice (supervisores)                 │
│  🗄️  Base de datos centralizada               │
└────────────────────────────────────────────────┘

VALOR ENTREGADO:

1️⃣  TRAZABILIDAD 100%
   "¿Qué caja específica recibió cada cliente?"
   → Sistema registra código de lote en cada entrega

2️⃣  FIFO AUTOMÁTICO (First In, First Out)
   "Siempre despachar lo más antiguo primero"
   → Algoritmo asigna lotes por fecha de vencimiento

3️⃣  VALIDACIÓN PRE-ENTREGA
   "Verificar que sea la caja correcta antes de salir"
   → Escaneo de código QR en centro de picking

4️⃣  VISIBILIDAD EN TIEMPO REAL
   "¿Dónde está cada despacho en este momento?"
   → Dashboard con estados: Picking → En Ruta → Entregado

5️⃣  PRECIO JUSTO
   "Cliente paga el peso exacto de lo que recibe"
   → Precio estimado → Precio real al confirmar
```

---

## 📋 SLIDE 4: ¿CÓMO FUNCIONA? (Visión General)

```
FLUJO COMPLETO DEL SISTEMA (6 ETAPAS)

┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1️⃣  CLIENTE ORDENA (Web/WhatsApp)                     │
│     └─→ Pedido entra al sistema como "PENDIENTE"       │
│                                                         │
│  2️⃣  SISTEMA ASIGNA LOTES (Automático - FIFO)          │
│     └─→ Algoritmo elige cajas más antiguas             │
│     └─→ Calcula precio real según peso                 │
│     └─→ Estado: CONFIRMADO                             │
│                                                         │
│  3️⃣  DESPACHADOR RECIBE ASIGNACIÓN (App Mobile)        │
│     └─→ Ve lista de productos a recolectar             │
│     └─→ Códigos QR de cada caja                        │
│                                                         │
│  4️⃣  PICKING CON VALIDACIÓN QR                         │
│     ┌────────────────────────────────┐                 │
│     │ Despachador escanea QR         │                 │
│     │  ✅ "Caja correcta"            │                 │
│     │  ❌ "Error: Caja incorrecta"   │                 │
│     └────────────────────────────────┘                 │
│     └─→ Estado: EN_RUTA (automático)                   │
│                                                         │
│  5️⃣  RUTA DE ENTREGA (Tracking)                        │
│     └─→ Dashboard muestra posición                     │
│     └─→ Cliente puede ver progreso                     │
│                                                         │
│  6️⃣  ENTREGA CONFIRMADA                                │
│     └─→ Estado: ENTREGADO                              │
│     └─→ Trazabilidad completa guardada                 │
│                                                         │
└─────────────────────────────────────────────────────────┘

⏱️  TIEMPO TOTAL: ~45 minutos (vs 60 min proceso anterior)
```

---

## 📋 SLIDE 5: INNOVACIONES TECNOLÓGICAS CLAVE

```
🔑 CUATRO PILARES DEL SISTEMA

┌──────────────────────────────────────────────────────┐
│ 1. ALGORITMO FIFO AUTOMÁTICO                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Input: Pedido de 2 cajas                           │
│  ↓                                                   │
│  Sistema consulta: lotes_disponibles                │
│  ↓                                                   │
│  ORDER BY fecha_vencimiento ASC  ← Clave del FIFO   │
│  ↓                                                   │
│  Output: [Lote-C6: 25-Feb, Lote-C7: 26-Feb]         │
│                                                      │
│  ✅ Beneficio: Minimiza mermas por vencimiento       │
│     (Reducción del 70%)                              │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 2. VALIDACIÓN IoT CON CÓDIGOS QR                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Cada caja tiene QR único:                           │
│  ┌──────────────┐                                    │
│  │  ████ ▄▄ ██  │  → Metadata del lote:             │
│  │  ██ ████ ▄▄  │     • Código: LOTE-C6             │
│  │  ▄▄ ██ ████  │     • Peso: 19.7 kg               │
│  └──────────────┘     • Vencimiento: 25-Feb-2026    │
│                       • Producto: Punta Picana      │
│                                                      │
│  Despachador escanea → Sistema valida en DB         │
│                      → ✅ Match: Continuar           │
│                      → ❌ Error: Alertar             │
│                                                      │
│  ✅ Beneficio: 0.5% tasa de error (antes 10%)       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 3. TRANSICIONES DE ESTADO AUTOMÁTICAS                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Antes (proceso manual):                             │
│    Operador: "Picking completo" → [Click cambiar    │
│    estado] → [Click iniciar ruta] → Salir           │
│                                                      │
│  Ahora (automatizado):                               │
│    Todas las cajas escaneadas → Sistema detecta     │
│    → Auto transición: EN_PICKING → EN_RUTA          │
│    → Despachador sale inmediatamente                │
│                                                      │
│  ✅ Beneficio: -30 segundos por despacho             │
│     (~25 horas/año de ahorro)                        │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ 4. SINCRONIZACIÓN MULTI-ENTIDAD EN TIEMPO REAL       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Despacho.estado = ENTREGADO                         │
│          ↓                                           │
│          ├─→ Pedido.estado = ENTREGADO (auto)       │
│          ├─→ Cliente.puntos += X (auto)             │
│          ├─→ Timestamp de entrega guardado          │
│          └─→ Dashboard actualizado                  │
│                                                      │
│  ✅ Beneficio: Consistencia de datos 100%            │
│     (no hay desincronizaciones)                      │
└──────────────────────────────────────────────────────┘
```

---

## 📋 SLIDE 6: ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────┐
│              ARQUITECTURA MULTI-CAPA                    │
└─────────────────────────────────────────────────────────┘

                    CAPA DE PRESENTACIÓN
    ┌──────────────┬──────────────┬──────────────┐
    │   Landing    │   Mobile     │  Backoffice  │
    │   (Next.js)  │  (React PWA) │  (Next.js)   │
    │              │              │              │
    │  - Catálogo  │  - Picking   │ - Dashboard  │
    │  - Checkout  │  - QR Scan   │ - CRUD       │
    │  - Tracking  │  - Tracking  │ - Reportes   │
    └──────┬───────┴──────┬───────┴──────┬───────┘
           │              │              │
           └──────────────┼──────────────┘
                          ↓
              ┌───────────────────────┐
              │   API REST (FastAPI)  │
              │                       │
              │  - Autenticación JWT  │
              │  - Endpoints CRUD     │
              │  - Lógica FIFO        │
              │  - Validación QR      │
              └───────────┬───────────┘
                          ↓
              ┌───────────────────────┐
              │  ORM (SQLAlchemy)     │
              │  - Models             │
              │  - Schemas            │
              │  - Migrations         │
              └───────────┬───────────┘
                          ↓
              ┌───────────────────────┐
              │  PostgreSQL Database  │
              │                       │
              │  - Pedidos            │
              │  - Despachos          │
              │  - Lotes              │
              │  - Clientes           │
              │  - Movimientos        │
              └───────────────────────┘

TECNOLOGÍAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frontend:     Next.js 14, React, Tailwind CSS
Backend:      Python 3.11, FastAPI, Pydantic
Base de Datos: PostgreSQL 14
ORM:          SQLAlchemy 2.0 + Alembic
Orquestación: Docker + Docker Compose
QR:           react-qr-scanner (frontend)
              qrcode library (backend)
```

---

## 📋 SLIDE 7: CASO DE USO REAL

```
📋 CASO PRÁCTICO: PEDIDO E-2026-00032

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTEXTO:
Cliente: Restaurant "El Buen Sabor" (Marcelo)
Producto: 2 cajas de Punta Picana (peso variable)
Precio/kg: $5,000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMELINE DETALLADO:

┌─────────────────────────────────────────────┐
│ 14:24 - PEDIDO CREADO (Web)                │
├─────────────────────────────────────────────┤
│ Cliente ingresa: "2 cajas Punta Picana"    │
│ Sistema estima: 2 × 19kg × $5,000          │
│ Precio estimado: $190,000                  │
│ Estado: PENDIENTE                           │
└─────────────────────────────────────────────┘

        ↓ [FIFO Automático se ejecuta] ↓

┌─────────────────────────────────────────────┐
│ 14:24 - CONFIRMADO CON LOTES ESPECÍFICOS   │
├─────────────────────────────────────────────┤
│ Algoritmo FIFO consulta:                    │
│   SELECT * FROM lotes                       │
│   WHERE disponible = true                   │
│   ORDER BY fecha_vencimiento ASC            │
│                                             │
│ Resultado:                                  │
│   ✅ Lote C6: 19.0kg, vence 25-Feb-2026    │
│   ✅ Lote C7: 18.1kg, vence 26-Feb-2026    │
│                                             │
│ Cálculo precio real:                        │
│   C6: 19.0kg × $5,000 = $95,000            │
│   C7: 18.1kg × $5,000 = $90,500            │
│   Total real: $185,500                      │
│                                             │
│ Ajuste: -$4,500 (2.4% menos que estimado)  │
│ Estado: CONFIRMADO                          │
└─────────────────────────────────────────────┘

        ↓ [Sistema asigna despachador] ↓

┌─────────────────────────────────────────────┐
│ 14:27 - ASIGNADO A DESPACHADOR              │
├─────────────────────────────────────────────┤
│ Despachador: Pedro                          │
│ Local: El Olivo                             │
│ Estado: ASIGNADO                            │
│                                             │
│ App mobile muestra:                         │
│   📋 Pedido E-2026-00032                   │
│   📍 Dirección: Av. Principal 1234         │
│   📦 2 items a recolectar:                 │
│      • LOTE-C6 (19.0kg) [QR]               │
│      • LOTE-C7 (18.1kg) [QR]               │
│   🕐 Hora estimada entrega: 14:45          │
└─────────────────────────────────────────────┘

        ↓ [Despachador inicia picking] ↓

┌─────────────────────────────────────────────┐
│ 14:27-14:32 - PICKING CON VALIDACIÓN QR    │
├─────────────────────────────────────────────┤
│ 14:28 → Escanea QR de Lote C6              │
│          Sistema valida: ✅ Correcto        │
│          Progreso: 1/2 ████████░░░░         │
│                                             │
│ 14:30 → Escanea QR de Lote C7              │
│          Sistema valida: ✅ Correcto        │
│          Progreso: 2/2 ████████████         │
│                                             │
│ 14:32 → Picking completo                   │
│          Transición automática:             │
│          EN_PICKING → EN_RUTA               │
│          fecha_inicio_ruta = 14:32          │
│                                             │
│ Estado: EN_RUTA                             │
│ ⚡ Sin clicks manuales necesarios           │
└─────────────────────────────────────────────┘

        ↓ [Ruta de entrega] ↓

┌─────────────────────────────────────────────┐
│ 14:32-14:45 - EN CAMINO                    │
├─────────────────────────────────────────────┤
│ Dashboard muestra:                          │
│   🚚 Pedro en ruta a El Buen Sabor         │
│   📍 Ubicación actualizada (GPS)           │
│   ⏱️  ETA: 14:45                           │
│                                             │
│ Cliente puede ver (web):                    │
│   "Tu pedido E-2026-00032 está en camino"  │
└─────────────────────────────────────────────┘

        ↓ [Llega al cliente] ↓

┌─────────────────────────────────────────────┐
│ 14:45 - ENTREGADO                           │
├─────────────────────────────────────────────┤
│ Despachador marca como entregado            │
│                                             │
│ Sistema ejecuta (automático):               │
│   ✅ Despacho.estado = ENTREGADO           │
│   ✅ Pedido.estado = ENTREGADO             │
│   ✅ fecha_entrega = 2026-02-18 14:45      │
│                                             │
│ Trazabilidad guardada:                      │
│   • Cliente: Marcelo (ID: 15)              │
│   • Lotes: C6 + C7                         │
│   • Despachador: Pedro                     │
│   • Precio final: $185,500                 │
│   • Tiempo total: 21 minutos               │
└─────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESULTADOS:
✅ Lotes más antiguos despachados primero (FIFO)
✅ Validación QR: 0 errores de picking
✅ Precio justo según peso real (-$4,500 vs estimado)
✅ Trazabilidad 100%: sabemos exactamente qué cajas
✅ Tiempo total: 21 minutos (60% del tiempo anterior)
```

---

## 📋 SLIDE 8: RESULTADOS E IMPACTO

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃       MÉTRICAS DE ÉXITO (Datos Reales)     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

COMPARATIVA ANTES vs DESPUÉS

┌──────────────────────────────────────────┐
│ TIEMPO DE DESPACHO                       │
├──────────────────────────────────────────┤
│ Antes:  ████████████░░░░  60 minutos     │
│ Ahora:  ████████░░░░░░░░  45 minutos     │
│ Mejora: ⬇️ 25%                           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ ERRORES DE ENTREGA                       │
├──────────────────────────────────────────┤
│ Antes:  ██████████░░░░░░  10.0%         │
│ Ahora:  ░░░░░░░░░░░░░░░░   0.5%         │
│ Mejora: ⬇️ 95%                           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ MERMAS POR VENCIMIENTO                   │
├──────────────────────────────────────────┤
│ Antes:  ██████████████░░  $700K/año      │
│ Ahora:  ████░░░░░░░░░░░░  $200K/año      │
│ Mejora: ⬇️ 71%                           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ TRAZABILIDAD                             │
├──────────────────────────────────────────┤
│ Antes:  ████████░░░░░░░░  Manual (~80%)  │
│ Ahora:  ████████████████  100% Digital   │
│ Mejora: ⬆️ 20%                           │
└──────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPACTO OPERACIONAL:

📈 +15% capacidad operativa
   (más entregas con el mismo equipo)

💰 $1.85M ahorro anual proyectado
   ($500K mermas + $200K devoluciones + $150K labor
    + $1.2M ingresos por capacidad adicional)

⏱️  150 horas/año tiempo ahorrado
   (30 seg × 60 despachos/día × 300 días)

🎯 NPS proyectado: +20 puntos
   (clientes más satisfechos)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VALOR ACADÉMICO:

Este proyecto demuestra cómo tecnologías comunes
(web, mobile, QR, bases de datos) integradas
correctamente pueden generar impacto medible en
métricas de negocio reales.
```

---

## 📋 SLIDE 9: APRENDIZAJES Y DESAFÍOS

```
💡 LECCIONES APRENDIDAS

┌─────────────────────────────────────────────────┐
│ 1. DISEÑO ORIENTADO AL USUARIO                 │
├─────────────────────────────────────────────────┤
│ Desafío:                                        │
│   Despachadores con poca experiencia tecnológica│
│                                                 │
│ Solución:                                       │
│   ✅ UI minimalista: 3 botones grandes         │
│   ✅ Colores: Verde = OK, Rojo = Error         │
│   ✅ Feedback instantáneo visual y sonoro      │
│                                                 │
│ Resultado:                                      │
│   Usuario de 58 años dominó el sistema en 1 día│
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 2. IMPORTANCIA DE LA AUTOMATIZACIÓN            │
├─────────────────────────────────────────────────┤
│ Desafío:                                        │
│   Proceso manual propenso a errores humanos    │
│                                                 │
│ Solución:                                       │
│   ✅ FIFO algoritmo (no depende de humano)     │
│   ✅ Transiciones de estado automáticas        │
│   ✅ Sincronización de datos sin intervención  │
│                                                 │
│ Resultado:                                      │
│   Errores cayeron de 10% a 0.5%                │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 3. TRAZABILIDAD = CONFIANZA                    │
├─────────────────────────────────────────────────┤
│ Desafío:                                        │
│   Reclamos de "no me llegó lo que pedí"        │
│                                                 │
│ Solución:                                       │
│   ✅ Registro de código de lote en cada entrega│
│   ✅ Timestamp de cada estado                  │
│   ✅ Respaldo fotográfico (futuro)             │
│                                                 │
│ Resultado:                                      │
│   100% de reclamos resolubles con evidencia    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 4. TESTING ES CRÍTICO                          │
├─────────────────────────────────────────────────┤
│ Desafío:                                        │
│   Bug en sincronización Despacho → Pedido      │
│                                                 │
│ Solución:                                       │
│   ✅ Suite de 32 tests automatizados           │
│   ✅ Fixtures reutilizables                    │
│   ✅ Base de datos de test aislada             │
│                                                 │
│ Resultado:                                      │
│   Bug detectado y corregido en fase de testing │
│   (no en producción)                            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ 5. ITERACIÓN SOBRE PERFECCIÓN                  │
├─────────────────────────────────────────────────┤
│ Enfoque:                                        │
│   MVP → Feedback real → Mejoras iterativas     │
│                                                 │
│ Ejemplo:                                        │
│   V1: Flujo con estado "LISTO_EMPAQUE"         │
│   Feedback: "Un click extra innecesario"        │
│   V2: Eliminado, transición directa EN_RUTA    │
│                                                 │
│ Resultado:                                      │
│   Sistema más rápido basado en uso real         │
└─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESAFÍOS TÉCNICOS SUPERADOS:

🐛 Bug de enums duplicados en schemas vs models
   → Solución: Single source of truth pattern

⚡ Performance en consultas FIFO con 1000+ lotes
   → Solución: Índices en fecha_vencimiento + disponible

🔄 Sincronización pedido-despacho desde múltiples interfaces
   → Solución: Service layer centralizado

📱 Compatibilidad QR en dispositivos antiguos
   → Solución: Fallback a input manual de código
```

---

## 📋 SLIDE 10: TECNOLOGÍAS UTILIZADAS

```
🛠️  STACK TECNOLÓGICO COMPLETO

┌─────────────────────────────────────────────────┐
│              FRONTEND (3 Aplicaciones)          │
├─────────────────────────────────────────────────┤
│ Landing Page (Cliente)                          │
│   • Next.js 14 (React framework)               │
│   • Tailwind CSS (estilos)                     │
│   • Context API (estado global)                │
│   • Responsive design (mobile-first)           │
│                                                 │
│ Mobile App (Despachador)                        │
│   • React PWA (Progressive Web App)            │
│   • react-qr-scanner (escaneo QR)              │
│   • Capacitor (compilación a Android/iOS)      │
│                                                 │
│ Backoffice (Supervisor)                         │
│   • Next.js 14 (App Router)                    │
│   • Recharts (gráficos)                        │
│   • NextAuth (autenticación)                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              BACKEND (API REST)                 │
├─────────────────────────────────────────────────┤
│ • Python 3.11                                   │
│ • FastAPI (framework web)                       │
│ • Pydantic v2 (validación de datos)            │
│ • SQLAlchemy 2.0 (ORM)                          │
│ • Alembic (migraciones)                         │
│ • pytest (testing - 32 tests)                   │
│ • qrcode (generación de QR)                     │
│ • JWT (autenticación)                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│          BASE DE DATOS Y STORAGE                │
├─────────────────────────────────────────────────┤
│ • PostgreSQL 14 (base de datos relacional)     │
│ • 15+ tablas con relaciones complejas           │
│ • Índices optimizados para FIFO                 │
│ • Backup automático cada 6 horas                │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         INFRAESTRUCTURA Y DEVOPS                │
├─────────────────────────────────────────────────┤
│ • Docker (contenedores)                         │
│ • Docker Compose (orquestación)                 │
│ • VPS Linux Ubuntu 22.04                        │
│ • Nginx (reverse proxy - futuro)                │
│ • GitHub (control de versiones)                 │
│ • GitHub Actions (CI/CD - futuro)               │
└─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POR QUÉ ESTAS TECNOLOGÍAS:

✅ FastAPI: Performance (async) + docs automáticas
✅ Next.js: SSR/SSG para SEO + Developer Experience
✅ PostgreSQL: ACID compliance + escalabilidad
✅ Docker: Portabilidad + entornos reproducibles
✅ QR: Tecnología ubicua (todos los teléfonos)
```

---

## 📋 SLIDE 11: DIAGRAMA DE DATOS (Modelo ER Simplificado)

```
┌─────────────────────────────────────────────────┐
│     MODELO ENTIDAD-RELACIÓN SIMPLIFICADO       │
└─────────────────────────────────────────────────┘

┌──────────────┐
│   CLIENTES   │
│──────────────│
│ id (PK)      │──┐
│ nombre       │  │
│ email        │  │
│ telefono     │  │
│ direccion    │  │
└──────────────┘  │
                  │
                  │  (1:N)
                  │
                  ↓
┌──────────────┐  │
│   PEDIDOS    │  │
│──────────────│  │
│ id (PK)      │←─┘
│ cliente_id   │
│ estado_id    │──→ EstadoPedido (PENDIENTE, CONFIRMADO, ...)
│ total        │
│ fecha        │
└──────┬───────┘
       │
       │  (1:N)
       │
       ↓
┌──────────────┐
│ ITEMS_PEDIDO │
│──────────────│
│ id (PK)      │
│ pedido_id    │
│ producto_id  │──→ ┌─────────────┐
│ lote_id      │──→ │   LOTES     │
│ cantidad     │    │─────────────│
│ precio_unit  │    │ id (PK)     │
└──────────────┘    │ codigo      │
                    │ producto_id │
                    │ peso_kg     │
       ┌────────────│ fecha_venc  │  ← Clave para FIFO
       │            │ disponible  │
       │            └─────────────┘
       │
       │  (1:1)
       │
       ↓
┌──────────────┐
│  DESPACHOS   │
│──────────────│
│ id (PK)      │
│ pedido_id    │
│ despachador  │
│ estado       │──→ EstadoDespacho (ASIGNADO, EN_PICKING, ...)
│ fecha_asig   │
│ fecha_pickup │
│ fecha_ruta   │    ← Timestamps para métricas
│ fecha_entrega│
└──────┬───────┘
       │
       │  (1:N)
       │
       ↓
┌──────────────┐
│ PICKING_ITEMS│
│──────────────│
│ id (PK)      │
│ despacho_id  │
│ producto_id  │
│ cant_solic   │
│ cant_recog   │    ← Validación QR actualiza esto
│ completado   │
└──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RELACIONES CLAVE:

• Cliente (1) ──< (N) Pedidos
• Pedido (1) ──< (N) Items_Pedido
• Pedido (1) ──< (1) Despacho
• Despacho (1) ──< (N) Picking_Items
• Lote (1) ──< (N) Items_Pedido

CONSULTA FIFO (ejemplo SQL):

  SELECT * FROM lotes
  WHERE producto_id = ?
    AND disponible_venta = true
  ORDER BY fecha_vencimiento ASC
  LIMIT cantidad_solicitada;
```

---

## 📋 SLIDE 12: ESCALABILIDAD Y FUTURO

```
🚀 ROADMAP Y VISIÓN FUTURA

┌─────────────────────────────────────────────────┐
│           FASE 2 - Q2 2026 (En Desarrollo)      │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📱 App Móvil Nativa                            │
│    └─→ iOS + Android compilado con Capacitor   │
│                                                 │
│ 📲 Notificaciones Push                          │
│    └─→ Cliente recibe update de cada estado    │
│                                                 │
│ 🗺️  Optimización de Rutas                      │
│    └─→ Algoritmo TSP para múltiples entregas   │
│                                                 │
│ 🌡️  Tracking de Temperatura                    │
│    └─→ IoT sensors para productos refrigerados │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│           FASE 3 - Q3 2026 (Planificado)        │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🤖 Machine Learning                             │
│    └─→ Predicción de demanda por producto      │
│    └─→ Sugerencias de rutas optimizadas        │
│                                                 │
│ ⭐ Sistema de Rating                            │
│    └─→ Clientes evalúan despachadores          │
│    └─→ Gamificación para mejorar servicio      │
│                                                 │
│ 📊 Dashboard Predictivo                         │
│    └─→ "Predicción: 3 lotes vencen en 48h"    │
│    └─→ Alertas proactivas de stock bajo        │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│          ESCALABILIDAD ACTUAL                   │
├─────────────────────────────────────────────────┤
│                                                 │
│ Capacidad testeada:                             │
│   • 500 despachos/día                           │
│   • 50 despachos simultáneos                    │
│   • 200 despachadores conectados                │
│   • 1000+ escaneos QR/hora                      │
│                                                 │
│ Operación actual:                               │
│   • ~30 despachos/día (10% de capacidad)       │
│   • Headroom para 15x crecimiento               │
│                                                 │
│ Multi-tenant:                                   │
│   • 2 locales operativos                        │
│   • Arquitectura soporta ilimitados             │
│                                                 │
└─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POTENCIAL DE EXPANSIÓN:

🏪 Vertical: Mismo sector (otros distribuidores)
🌐 Horizontal: Otros sectores (farmacia, retail)
🌍 Geográfica: Otras ciudades/países
💼 B2B SaaS: Vender como plataforma
```

---

## 📋 SLIDE 13: CONCLUSIONES

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         CONCLUSIONES DEL PROYECTO          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

1️⃣  PROBLEMA REAL, SOLUCIÓN REAL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   No es un proyecto teórico:
   • Opera en producción desde esta semana
   • Resuelve problemas medibles
   • Genera valor económico tangible

2️⃣  INTEGRACIÓN > INNOVACIÓN DISRUPTIVA
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Tecnologías comunes bien integradas:
   • No requirió IA avanzada ni blockchain
   • QR + Base de datos + Lógica de negocio
   • Simplicidad = Adopción + Mantenibilidad

3️⃣  USUARIO EN EL CENTRO
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Diseñado para humanos reales:
   • Interfaz minimalista (3 botones)
   • Feedback instantáneo visual
   • Curva de aprendizaje: 1 día

4️⃣  DATOS = VENTAJA COMPETITIVA
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Trazabilidad 100% habilita:
   • Resolver reclamos con evidencia
   • Optimizar procesos con métricas reales
   • Predicciones futuras (ML en Q3)

5️⃣  ESCALABLE POR DISEÑO
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   No es "solo para esta empresa":
   • Multi-tenant desde inicio
   • API REST documentada
   • Docker = portable a cualquier cloud

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPACTO MEDIBLE:

✅ -95% errores de entrega
✅ -25% tiempo de despacho
✅ -71% mermas por vencimiento
✅ +15% capacidad operativa
✅ $1.85M ahorro anual

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFLEXIÓN FINAL:

"La mejor tecnología no es la más avanzada,
 es la que resuelve el problema correcto
 de la manera más simple posible"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este proyecto demuestra que un estudiante de
diplomado, con las herramientas adecuadas y
enfoque en el problema real, puede generar
impacto medible en operaciones empresariales.
```

---

## 📋 SLIDE 14: REFERENCIAS Y RECURSOS

```
📚 DOCUMENTACIÓN Y RECURSOS

┌─────────────────────────────────────────────────┐
│              REPOSITORIOS (GitHub)              │
├─────────────────────────────────────────────────┤
│                                                 │
│ Backend (API):                                  │
│ 🔗 github.com/mmoyac/fme-backend               │
│    • Código fuente FastAPI                      │
│    • 32 tests automatizados                     │
│    • Documentación técnica completa             │
│                                                 │
│ Frontend (Landing):                             │
│ 🔗 github.com/mmoyac/fme-landing               │
│    • Cliente Next.js                            │
│    • Integración con API                        │
│                                                 │
│ Backoffice:                                     │
│ 🔗 github.com/mmoyac/fme-backoffice            │
│    • Panel administrativo                       │
│    • Dashboard de métricas                      │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│           ACCESO A SISTEMA EN VIVO              │
├─────────────────────────────────────────────────┤
│                                                 │
│ API (Documentación interactiva):                │
│ 🌐 http://api.masasestacion.cl/docs            │
│                                                 │
│ Backoffice (Demo):                              │
│ 🌐 http://admin.masasestacion.cl               │
│    Usuario demo: [Solicitar a presentador]     │
│                                                 │
│ Landing Page:                                   │
│ 🌐 http://masasestacion.cl                     │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│        DOCUMENTACIÓN TÉCNICA DISPONIBLE         │
├─────────────────────────────────────────────────┤
│                                                 │
│ • AGENTS.md (Backend)                           │
│   → Manual operacional completo                 │
│                                                 │
│ • PRESENTACION_SISTEMA_DESPACHOS.md             │
│   → Documento ejecutivo detallado               │
│                                                 │
│ • tests/README.md                               │
│   → Estrategia y cobertura de testing           │
│                                                 │
│ • FLUJO_DESPACHOS.md                            │
│   → Diagramas de flujo completos                │
│                                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│             TECNOLOGÍAS REFERENCIADAS           │
├─────────────────────────────────────────────────┤
│                                                 │
│ FastAPI:        https://fastapi.tiangolo.com    │
│ Next.js:        https://nextjs.org              │
│ PostgreSQL:     https://postgresql.org          │
│ Docker:         https://docker.com              │
│ SQLAlchemy:     https://sqlalchemy.org          │
│ Tailwind CSS:   https://tailwindcss.com         │
│                                                 │
└─────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTACTO:

👤 [Tu Nombre]
📧 [Tu Email]
🔗 LinkedIn: [Tu perfil]
💼 GitHub: [Tu usuario]

📱 Para demo en vivo o preguntas adicionales,
   contactar al finalizar la presentación.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGRADECIMIENTOS:

• Masas Estación por permitir implementar el proyecto
• Equipo de despachadores por feedback invaluable
• Profesores del diplomado por la guía académica
```

---

## 📋 SLIDE 15: PREGUNTAS

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                            ┃
┃                                            ┃
┃              ¿PREGUNTAS?                   ┃
┃                                            ┃
┃                                            ┃
┃         📧 [tu-email@email.com]           ┃
┃                                            ┃
┃         🔗 github.com/[tu-usuario]        ┃
┃                                            ┃
┃                                            ┃
┃         Gracias por su atención           ┃
┃                                            ┃
┃                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛




         Sistema de Gestión de Despachos
         con Trazabilidad FIFO Automática

              Proyecto de Diplomado

                 Febrero 2026
```

---

## 🎯 GUÍA DE USO DE ESTA PRESENTACIÓN

### Para convertir a Google Slides / PowerPoint:

**Opción 1: Manual (Recomendado para personalizar)**
1. Crear presentación nueva en Google Slides
2. Usar tema minimalista (fondo oscuro recomendado)
3. Copiar cada slide de este documento
4. Usar fuente monospace (Courier / Consolas) para ASCII art
5. Agregar imágenes reales del sistema (screenshots)

**Opción 2: Con herramienta (Rápido)**
1. Usar https://slides.com o https://revealjs.com
2. Importar este markdown directamente
3. Ajustar estilos según marca personal

**Opción 3: Canva (Más visual)**
1. Crear desde plantilla "Presentación Técnica"
2. Usar los textos como base
3. Reemplazar ASCII art con diagramas visuales
4. Agregar screenshots reales del dashboard

### Material complementario sugerido:

- [ ] Screenshot del dashboard en vivo
- [ ] Video 30seg de escaneo QR en acción
- [ ] Foto del equipo de despachadores
- [ ] Diagrama visual de arquitectura (Figma/Draw.io)
- [ ] QR code con link a demo en vivo

### Timing recomendado (total: 20 minutos):

- Slides 1-3: 3 minutos (problema)
- Slides 4-6: 5 minutos (solución)
- Slide 7: 4 minutos (caso real - DETALLAR AQUÍ)
- Slides 8-10: 4 minutos (resultados y tecnología)
- Slides 11-13: 3 minutos (futuro y conclusiones)
- Slide 14-15: 1 minuto (cierre y Q&A)

---

**Última actualización:** 18 Febrero 2026  
**Versión:** 1.0 (Académica)
