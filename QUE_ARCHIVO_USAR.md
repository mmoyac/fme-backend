# 🎯 GUÍA RÁPIDA: ¿QUÉ ARCHIVO USAR?
## Selector por Audiencia y Objetivo

**Última actualización:** 18 Febrero 2026

---

## 🎓 PRESENTACIÓN PARA DIPLOMADO (Evaluación Académica)

### Objetivo: Explicar QUÉ hace el sistema y POR QUÉ es valioso (NO técnico)

```
┌─────────────────────────────────────────────────┐
│  SITUACIÓN: Defensa de proyecto en diplomado   │
│  AUDIENCIA: Profesores + Compañeros             │
│  TIEMPO: 15-20 minutos + Q&A                    │
│  ENFOQUE: Valor del sistema, no código         │
└─────────────────────────────────────────────────┘

📚 ARCHIVOS A USAR:

  1️⃣  📄 README_PROYECTO_DIPLOMADO.md
      └─→ Índice principal con TODO el contexto
          Leer PRIMERO antes de preparar
          
  2️⃣  📊 PRESENTACION_DIPLOMADO.md
      └─→ Contenido de 15 slides
          Convertir a Google Slides/PowerPoint
          
  3️⃣  📘 GUIA_CREACION_SLIDES.md
      └─→ Paso a paso para crear slides visuales
          16 pasos detallados con ejemplos
          
  4️⃣  📄 URL_PRESENTACION.txt
      └─→ Template para completar y entregar
          Incluir link a Google Slides final

✅ CHECKLIST DE ENTREGA:
   [ ] Presentación en Google Slides (URL)
   [ ] PDF exportado de la presentación
   [ ] README_PROYECTO_DIPLOMADO.md
   [ ] URL_PRESENTACION.txt completado
   [ ] 2-3 screenshots del sistema
```

---

## 💼 PRESENTACIÓN PARA GERENCIA (Aprobación de Presupuesto)

### Objetivo: Convencer con NÚMEROS y ROI (Decisión de negocio)

```
┌─────────────────────────────────────────────────┐
│  SITUACIÓN: Junta de gerencia/directorio       │
│  AUDIENCIA: C-level, Gerentes, CFO             │
│  TIEMPO: 20 minutos + 10 min Q&A               │
│  ENFOQUE: ROI, ahorro, métricas de negocio     │
└─────────────────────────────────────────────────┘

📚 ARCHIVOS A USAR:

  1️⃣  📄 KIT_PRESENTACION_INDEX.md
      └─→ Índice maestro del kit ejecutivo
          Estrategias de uso por escenario
          
  2️⃣  📊 GUIA_PRESENTACION_SLIDES.md
      └─→ 12 slides con talking points
          Versión ejecutiva con números financieros
          
  3️⃣  📋 RESUMEN_EJECUTIVO_1_PAGINA.md
      └─→ Handout para entregar al inicio
          Resumen de 1 página imprimible
          
  4️⃣  ❓ FAQ_EJECUTIVO.md
      └─→ 30+ preguntas frecuentes con respuestas
          Tu "chuleta" para Q&A
          
  5️⃣  📄 PRESENTACION_SISTEMA_DESPACHOS.md
      └─→ Documento completo (500 líneas)
          Para lectura post-reunión

✅ FLUJO RECOMENDADO:
   24h ANTES: Email #1 con RESUMEN_EJECUTIVO_1_PAGINA.pdf
   DURANTE:   Proyectar GUIA_PRESENTACION_SLIDES.md
              Entregar RESUMEN impresos
              Tener FAQ_EJECUTIVO.md abierto (laptop)
   POST:      Email #2 con PRESENTACION_SISTEMA_DESPACHOS.pdf
```

---

## 🔍 COMPARACIÓN LADO A LADO

```
┌──────────────────────┬─────────────────┬─────────────────┐
│      ASPECTO         │    DIPLOMADO    │    GERENCIA     │
├──────────────────────┼─────────────────┼─────────────────┤
│ Objetivo             │ Explicar valor  │ Aprobar $$$     │
│ Enfoque              │ Educativo       │ ROI             │
│ Slides               │ 15              │ 12              │
│ Duración             │ 15-20 min       │ 20 min          │
│ Nivel técnico        │ Medio-bajo      │ Bajo (negocio)  │
│ Demo en vivo         │ Opcional        │ Recomendado     │
│ Métricas             │ Generales       │ Financieras $$$ │
│ Caso real            │ Detallado       │ Resumen         │
│ Código fuente        │ Mencionar       │ No mencionar    │
│ Arquitectura         │ Diagrama simple │ Omitir          │
│ Roadmap futuro       │ Features        │ ROI adicional   │
│ Material entrega     │ PDF + URL       │ PDF + handout   │
└──────────────────────┴─────────────────┴─────────────────┘
```

---

## 📖 DOCUMENTACIÓN TÉCNICA (Referencia Interna)

### Objetivo: Manual operacional para desarrolladores

```
┌─────────────────────────────────────────────────┐
│  SITUACIÓN: Onboarding de nuevo dev            │
│  AUDIENCIA: Programadores, DevOps               │
│  TIEMPO: Estudio independiente                  │
│  ENFOQUE: Cómo funciona el código              │
└─────────────────────────────────────────────────┘

📚 ARCHIVOS A USAR:

  1️⃣  📘 AGENTS.md (Backend)
      └─→ Manual operacional completo
          Arquitectura, comandos, reglas de negocio
          
  2️⃣  📘 AGENTS.md (Backoffice)
      └─→ Guía del panel administrativo
          Funcionalidades, estructura, UI
          
  3️⃣  📘 AGENTS.md (Landing)
      └─→ Frontend del cliente
          Integración con API, componentes
          
  4️⃣  🧪 tests/README.md
      └─→ Suite de 32 tests automatizados
          Fixtures, cobertura, convenciones
          
  5️⃣  📊 FLUJO_DESPACHOS.md
      └─→ Diagramas de flujo detallados
          Estados, transiciones, validaciones

❌ NO USAR PARA:
   Presentaciones a no-técnicos
   Material de ventas o marketing
   Documentación de usuario final
```

---

## 🚀 ESCENARIOS ESPECÍFICOS

### Escenario A: "Tengo 5 minutos en ascensor con CEO"

```
📄 Usar: RESUMEN_EJECUTIVO_1_PAGINA.md

🗣️  Script:
   "Implementamos sistema que reduce errores 95%
    y ahorra $1.8M al año. Ya funciona en producción.
    ROI en 1.4 años. ¿Le envío el detalle?"
    
   [Entregar PDF del resumen]
```

---

### Escenario B: "Presentación remota por Zoom"

```
📄 Usar: 
   • GUIA_PRESENTACION_SLIDES.md (pantalla compartida)
   • FAQ_EJECUTIVO.md (pantalla secundaria)
   
🖥️  Setup:
   Monitor 1: Slides en modo presentador
   Monitor 2: FAQ + Dashboard en vivo
   
💡 Tip: Grabar sesión para compartir después
```

---

### Escenario C: "Email de seguimiento post-reunión"

```
📧 Usar: EMAIL_TEMPLATES.md

Seleccionar:
   • Template #2 (Post-reunión inmediato)
   • Adjuntar: PRESENTACION_SISTEMA_DESPACHOS.pdf
   • Incluir: Próximos pasos acordados
```

---

### Escenario D: "Capacitación de nuevo despachador"

```
❌ NO usar archivos de presentaciones

✅ Crear material específico:
   • Manual de usuario (no está en este kit)
   • Video tutoriales paso a paso
   • FAQs de uso diario
   
💡 Este kit es para stakeholders, no usuarios finales
```

---

## 🎨 PERSONALIZACIÓN POR AUDIENCIA

```
┌──────────────────────────────────────────────────────┐
│              MATRIZ DE PERSONALIZACIÓN               │
├──────────────┬────────────┬────────────┬─────────────┤
│   AUDIENCIA  │   ENFOQUE  │  DURACIÓN  │   ARCHIVO   │
├──────────────┼────────────┼────────────┼─────────────┤
│ Profesores   │ Aprendizaje│ 15-20 min  │ *_DIPLOMADO │
│ Estudiantes  │ Técnico    │ 20-30 min  │ *_DIPLOMADO │
│ CEO/CFO      │ ROI        │ 10-15 min  │ RESUMEN_1P  │
│ Gerentes     │ Operacional│ 20 min     │ GUIA_SLIDES │
│ Desarrollador│ Código     │ Async      │ AGENTS.md   │
│ Cliente      │ Beneficios │ 5 min      │ (Crear new) │
│ Inversor     │ Escalabilid│ 30 min     │ PRESENTACION│
└──────────────┴────────────┴────────────┴─────────────┘
```

---

## 🔢 NÚMEROS QUE DEBES MEMORIZAR

### Para CUALQUIER audiencia:

```
-95%   Reducción de errores (10% → 0.5%)
-25%   Reducción de tiempo (60 → 45 min)
-71%   Reducción de mermas ($700K → $200K)

$1.85M  Ahorro anual total proyectado
1.46    Años para ROI completo

21 min  Tiempo total del caso real (E-2026-00032)

100%    Trazabilidad completa con códigos QR
99.5%   Exactitud de picking actual

32      Tests automatizados (100% pasando)
15+     Tablas en base de datos
3       Aplicaciones frontend
```

---

## ⚠️  ERRORES COMUNES A EVITAR

```
❌ Usar archivo técnico (AGENTS.md) para presentar a gerencia
   → Demasiado técnico, pierde atención

❌ Usar presentación ejecutiva (GUIA_SLIDES) en diplomado
   → Enfoque en negocio, no en aprendizaje académico

❌ Leer textualmente el documento en slides
   → Boring, pierdes engagement

❌ No estudiar FAQ antes de presentar
   → Quedas sin respuesta a preguntas obvias

❌ Presentación demasiado larga (>30 min)
   → Pierdes audiencia, menos es más

❌ No mostrar caso real con datos específicos
   → Parece teórico, sin credibilidad
```

---

## 🎯 DECISIÓN RÁPIDA (Flowchart)

```
                    [Tengo que presentar]
                              |
        ┌─────────────────────┴─────────────────────┐
        │                                           │
   ¿Para quién?                              ¿Para quién?
        │                                           │
    Académico                                   Negocio
        │                                           │
        v                                           v
┌───────────────────┐                   ┌───────────────────┐
│ README_PROYECTO_  │                   │ KIT_PRESENTACION_ │
│ DIPLOMADO.md      │                   │ INDEX.md          │
│       +           │                   │       +           │
│ PRESENTACION_     │                   │ GUIA_PRESENTACION_│
│ DIPLOMADO.md      │                   │ SLIDES.md         │
│       +           │                   │       +           │
│ GUIA_CREACION_    │                   │ RESUMEN_EJECUTIVO_│
│ SLIDES.md         │                   │ 1_PAGINA.md       │
└───────────────────┘                   │       +           │
                                        │ FAQ_EJECUTIVO.md  │
                                        └───────────────────┘
```

---

## 💡 PRO TIPS

### 1. Siempre empieza por el README apropiado
```
Diplomado → README_PROYECTO_DIPLOMADO.md
Gerencia  → KIT_PRESENTACION_INDEX.md
```

### 2. Ten el FAQ abierto durante Q&A
```
Laptop pantalla secundaria con FAQ_EJECUTIVO.md
Quick search (Ctrl+F) para encontrar respuestas rápido
```

### 3. Practica el timing
```
REGLA: 1 slide = 1-2 minutos máximo
15 slides = 15-20 minutos
Deja 10 min para preguntas
```

### 4. Personaliza los templates
```
Buscar [Pendiente], [Tu Nombre], [Tu Email]
Reemplazar con tus datos reales
```

### 5. Material complementario
```
Screenshots > ASCII art
Video demo > texto explicativo
Dashboard en vivo > capturas estáticas
```

---

## 📞 ¿TODAVÍA TIENES DUDAS?

```
┌─────────────────────────────────────────────────┐
│  PREGUNTA: ¿Cuál es el archivo más importante? │
├─────────────────────────────────────────────────┤
│  RESPUESTA:                                     │
│                                                 │
│  Para DIPLOMADO:                                │
│    → README_PROYECTO_DIPLOMADO.md               │
│                                                 │
│  Para GERENCIA:                                 │
│    → RESUMEN_EJECUTIVO_1_PAGINA.md              │
│                                                 │
│  Para DESARROLLADORES:                          │
│    → AGENTS.md (Backend)                        │
│                                                 │
│  Start here ☝️                                  │
└─────────────────────────────────────────────────┘
```

---

## 🎬 SIGUIENTE PASO

```
1. Identificar tu audiencia y objetivo
      ↓
2. Leer el README correspondiente
      ↓
3. Preparar presentación según guías
      ↓
4. Practicar 2-3 veces
      ↓
5. ¡Presentar con confianza! 🎯
```

---

**¡Éxito en tu presentación! 🚀**

*Última actualización: 18 Febrero 2026*
