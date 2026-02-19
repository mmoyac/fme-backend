# 🎓 GUÍA COMPLETA: PRESENTACIÓN PARA DIPLOMADO
## Cómo Convertir el Documento a Slides Visuales

**Última actualización:** 18 Febrero 2026

---

## 📦 ARCHIVOS PARA ENTREGAR AL DIPLOMADO

```
📁 Entrega_Proyecto_Despachos/
├── 📄 README_PROYECTO.md                    (Este archivo como índice)
├── 📊 Presentacion_Slides.pdf               (Exportado de Google Slides)
├── 🔗 URL_Presentacion.txt                  (Link a presentación online)
├── 📸 Screenshots/
│   ├── dashboard.png
│   ├── mobile_picking.png
│   ├── qr_scan.png
│   └── arquitectura.png
├── 📹 Videos/
│   └── demo_picking_30seg.mp4
└── 💻 Codigo/
    ├── fme-backend/                         (Clonar repositorio)
    ├── fme-backoffice/
    └── fme-landing/
```

---

## ✅ OPCIÓN 1: GOOGLE SLIDES (Recomendada)

### Ventajas:
✅ Gratis
✅ Accesible desde cualquier dispositivo
✅ Fácil de compartir (solo URL)
✅ Colaboración en tiempo real
✅ No requiere instalación

### Paso a Paso:

**1. Crear presentación nueva**
```
1. Ir a https://slides.google.com
2. Click en "+ En blanco"
3. Título: "Sistema de Gestión de Despachos - Diplomado"
```

**2. Configurar tema**
```
Menú: Diapositiva → Cambiar tema
Seleccionar: "Marina" o "Enfoque oscuro"
Color primario: Turquesa (#5EC8F2)
Fuente títulos: Montserrat
Fuente cuerpo: Roboto
```

**3. Crear SLIDE 1 (Portada)**
```
Layout: "Título y subtítulo"

Título:
    SISTEMA DE GESTIÓN DE DESPACHOS
    CON TRAZABILIDAD AUTOMÁTICA

Subtítulo:
    Optimización de Logística de Última Milla con IoT y FIFO
    
    Estudiante: [Tu Nombre]
    Diplomado: [Nombre del Diplomado]
    Fecha: Febrero 2026
    
Fondo: Imagen de bodega con cajas (opcional)
       O color sólido oscuro (#1e293b)
```

**4. Crear SLIDE 2 (Contexto del Problema)**
```
Layout: "Título y cuerpo"

Título: CONTEXTO DEL PROBLEMA

Contenido (usar viñetas):
    • Industria: E-commerce de alimentos B2B
    • Productos de peso variable (17-22 kg/caja)
    • Fechas de vencimiento críticas
    • Alto costo de errores en preparación
    
Agregar:
    • Imagen de cajas con diferentes pesos
    • Icon de calendario con "Vence en X días"
    
Nota al pie:
    "¿Cómo garantizar producto correcto con lote más antiguo?"
```

**5. Crear SLIDE 3 (¿Qué Resuelve?)**
```
Layout: "Título y dos columnas"

Título: ¿QUÉ RESUELVE EL SISTEMA?

Columna izquierda:
    1️⃣ TRAZABILIDAD 100%
       Registro de lote específico
       
    2️⃣ FIFO AUTOMÁTICO
       Algoritmo asigna lotes más antiguos
       
    3️⃣ VALIDACIÓN QR
       Verificación pre-entrega

Columna derecha:
    4️⃣ VISIBILIDAD TIEMPO REAL
       Dashboard con estados
       
    5️⃣ PRECIO JUSTO
       Cliente paga peso exacto
       
Agregar:
    • Iconos de cada feature
    • Screenshot mini del dashboard
```

**6. Crear SLIDE 4 (Flujo del Sistema)**
```
Layout: "Solo título"

Título: FLUJO COMPLETO (6 ETAPAS)

Contenido: Diagrama horizontal con flechas

[Cliente Ordena] → [FIFO Asigna] → [Despachador Recibe]
        ↓
[Picking QR] → [En Ruta] → [Entregado]

Usar SmartArt de Google Slides:
    Insertar → Diagrama → Proceso
    
Colores:
    Pendiente: Naranja
    Confirmado: Azul
    En Picking: Amarillo
    En Ruta: Verde claro
    Entregado: Verde oscuro

Tiempo total: 45 minutos
```

**7. Crear SLIDE 5 (Innovaciones Clave)**
```
Layout: "Título y cuerpo"

Título: INNOVACIONES TECNOLÓGICAS

Dividir en 4 cuadrantes:

┌──────────────┬──────────────┐
│ FIFO Auto    │ Validación QR│
│              │              │
│ Algoritmo    │ Código único │
│ ORDER BY     │ por caja     │
│ fecha_venc   │ Escaneo IoT  │
├──────────────┼──────────────┤
│ Transiciones │ Sincroniza   │
│ Automáticas  │ Tiempo Real  │
│              │              │
│ Sin clicks   │ Todos los    │
│ manuales     │ sistemas sync│
└──────────────┴──────────────┘

Agregar:
    • Screenshot del QR
    • Código SQL del FIFO
    • Efecto visual de sincronización
```

**8. Crear SLIDE 6 (Arquitectura)**
```
Layout: "Solo título"

Título: ARQUITECTURA DEL SISTEMA

Crear diagrama de capas:

┌─────────────────────────────────┐
│   PRESENTACIÓN                  │
│ Landing | Mobile | Backoffice   │
│ (Next.js) (PWA)   (Next.js)     │
├─────────────────────────────────┤
│   API REST (FastAPI)            │
│ Endpoints | Auth | Lógica       │
├─────────────────────────────────┤
│   ORM (SQLAlchemy)              │
│ Models | Schemas | Migrations   │
├─────────────────────────────────┤
│   BASE DE DATOS (PostgreSQL)    │
│ Pedidos | Despachos | Lotes     │
└─────────────────────────────────┘

Agregar logos de tecnologías:
    • Next.js logo
    • FastAPI logo
    • PostgreSQL logo
```

**9. Crear SLIDE 7 (Caso Real) - MÁS IMPORTANTE**
```
Layout: "Solo título"

Título: CASO DE USO REAL: PEDIDO E-2026-00032

Timeline vertical con horas:

14:24 🛒 Pedido creado
      Cliente: Restaurant "El Buen Sabor"
      Producto: 2 cajas Punta Picana
      
14:24 ✅ FIFO asignó lotes C6 + C7
      Precio ajustado: $185,500

14:27 👤 Asignado a despachador Pedro

14:27 📋 Picking iniciado
      Escaneo QR: ✅✅

14:32 🚚 EN RUTA (automático)

14:45 ✅ ENTREGADO
      Tiempo total: 21 minutos

Agregar:
    • Screenshot de pedido real
    • Foto de QR siendo escaneado
    • Mapa con ruta (si tienes GPS)
```

**10. Crear SLIDE 8 (Resultados)**
```
Layout: "Título y cuerpo"

Título: RESULTADOS E IMPACTO

Usar gráficos de barras comparativas:

Tiempo de Despacho
[Antes]  ████████████ 60 min
[Ahora]  ████████ 45 min
         ⬇️ 25% mejora

Errores de Entrega
[Antes]  ██████████ 10%
[Ahora]  ░ 0.5%
         ⬇️ 95% mejora

Mermas por Vencimiento
[Antes]  ████████████ $700K/año
[Ahora]  ████ $200K/año
         ⬇️ 71% mejora

Usar Google Sheets integrado para gráficos
```

**11. Crear SLIDE 9 (Tecnologías)**
```
Layout: "Título y tres columnas"

Título: STACK TECNOLÓGICO

Columna 1: FRONTEND
    • Next.js 14
    • React
    • Tailwind CSS
    • PWA
    
Columna 2: BACKEND
    • Python 3.11
    • FastAPI
    • SQLAlchemy
    • pytest
    
Columna 3: INFRA
    • PostgreSQL 14
    • Docker
    • VPS Ubuntu
    • GitHub

Agregar logos de cada tecnología
(Iconos descargables de simpleicons.org)
```

**12. Crear SLIDE 10 (Aprendizajes)**
```
Layout: "Título y cuerpo"

Título: APRENDIZAJES Y DESAFÍOS

Usar formato de lista numerada:

1. DISEÑO ORIENTADO AL USUARIO
   UI minimalista → Usuario de 58 años lo domina en 1 día
   
2. AUTOMATIZACIÓN CRÍTICA
   FIFO algoritmo → Errores cayeron 95%
   
3. TRAZABILIDAD = CONFIANZA
   Registro de lotes → 100% reclamos resolubles
   
4. TESTING ES ESENCIAL
   32 tests automatizados → Bug detectado pre-producción
   
5. ITERACIÓN > PERFECCIÓN
   MVP → Feedback → Mejoras → V2 optimizada

Agregar:
    • Icono de bombillo 💡 en cada punto
```

**13. Crear SLIDE 11 (Escalabilidad)**
```
Layout: "Título y dos columnas"

Título: ROADMAP Y FUTURO

Columna izquierda:
    FASE 2 - Q2 2026
    • App móvil nativa
    • Notificaciones push
    • Optimización de rutas
    • Tracking temperatura
    
Columna derecha:
    FASE 3 - Q3 2026
    • Machine Learning
    • Sistema de rating
    • Dashboard predictivo
    • Predicción de demanda

Capacidad actual:
    500 despachos/día (usando 10%)
    ↑ Headroom para 15x crecimiento
```

**14. Crear SLIDE 12 (Conclusiones)**
```
Layout: "Título y cuerpo"

Título: CONCLUSIONES

Usar viñetas con iconos:

✅ PROBLEMA REAL, SOLUCIÓN REAL
   Opera en producción con impacto medible

✅ INTEGRACIÓN > INNOVACIÓN DISRUPTIVA
   Tecnologías simples bien integradas

✅ USUARIO EN EL CENTRO
   Interfaz minimalista, aprendizaje 1 día

✅ DATOS = VENTAJA COMPETITIVA
   Trazabilidad 100% habilita optimizaciones

✅ ESCALABLE POR DISEÑO
   Multi-tenant, portable, documentado

Frase de cierre en texto grande:
"La mejor tecnología resuelve el problema correcto
 de la manera más simple posible"
```

**15. Crear SLIDE 13 (Referencias)**
```
Layout: "Título y cuerpo"

Título: REFERENCIAS Y RECURSOS

Repositorios:
    🔗 github.com/mmoyac/fme-backend
    🔗 github.com/mmoyac/fme-backoffice
    🔗 github.com/mmoyac/fme-landing

Sistema en Vivo:
    🌐 http://admin.masasestacion.cl
    🌐 http://api.masasestacion.cl/docs

Documentación:
    • AGENTS.md (Backend)
    • PRESENTACION_SISTEMA_DESPACHOS.md
    • tests/README.md

Tecnologías:
    FastAPI | Next.js | PostgreSQL | Docker
```

**16. Crear SLIDE 14 (Preguntas)**
```
Layout: "Solo título"

Título grande centrado:

    ¿PREGUNTAS?
    
    
    📧 [tu-email@email.com]
    🔗 github.com/[tu-usuario]
    
    
    Gracias por su atención


Fondo: Imagen inspiradora de logística/tecnología
       O color sólido con gradiente
```

---

## 💾 EXPORTAR Y COMPARTIR

**Exportar a PDF:**
```
1. Archivo → Descargar → Documento PDF (.pdf)
2. Configuración:
   - Tamaño: Estándar (No agrupar diapositivas)
   - Calidad: Alta
3. Guardar como: "Presentacion_Sistema_Despachos_[TuNombre].pdf"
```

**Compartir URL:**
```
1. Botón "Compartir" (esquina superior derecha)
2. Configuración:
   - "Cualquier persona con el enlace puede ver"
   - Desactivar comentarios (solo visualizar)
3. Copiar enlace
4. Crear archivo "URL_Presentacion.txt":
   
   Presentación: Sistema de Gestión de Despachos
   URL: https://docs.google.com/presentation/d/[ID]/edit?usp=sharing
   
   Nota: Presentación de solo lectura para evaluación del diplomado.
```

---

## 📸 MATERIAL COMPLEMENTARIO NECESARIO

### Screenshots a Capturar:

**1. Dashboard Principal (screenshot #1)**
```
Ir a: http://admin.masasestacion.cl/admin/despacho
Capturar: Vista completa del dashboard con métricas
Nombrar: dashboard_principal.png
Usar en: Slide 3, Slide 8
```

**2. Mobile Picking (screenshot #2)**
```
Abrir en celular: App de picking
Capturar: Pantalla con lista de items y botón escanear
Nombrar: mobile_picking.png
Usar en: Slide 5, Slide 7
```

**3. Escaneo QR (screenshot #3)**
```
Capturar: Momento de escanear QR con feedback "✅ Caja correcta"
Nombrar: qr_scan_success.png
Usar en: Slide 5, Slide 7
```

**4. Diagrama de Arquitectura (screenshot #4)**
```
Opción A: Crear en Draw.io (https://app.diagrams.net)
Opción B: Crear en Excalidraw (https://excalidraw.com)
Nombrar: arquitectura_sistema.png
Usar en: Slide 6
```

**5. Pedido Real (screenshot #5)**
```
Ir a: Backoffice → Pedidos → E-2026-00032
Capturar: Vista completa del pedido con timeline
Nombrar: pedido_real_e2026_00032.png
Usar en: Slide 7
```

---

## 🎥 VIDEO DEMO (Opcional pero Impactante)

### Grabar video de 30 segundos:
```
Escena 1 (10 seg):
    Despachador abre app → Ve lista de items

Escena 2 (10 seg):
    Escanea QR → Feedback "✅ Caja correcta"
    Progreso: 1/2 → 2/2

Escena 3 (10 seg):
    Transición automática a EN_RUTA
    Mensaje: "¡Listo para entregar!"

Herramientas:
    • Grabar pantalla: OBS Studio (gratis)
    • Editar: DaVinci Resolve (gratis)
    • O simplemente: Grabar con otro celular
    
Exportar como: demo_picking_30seg.mp4
Subir a: Google Drive (compartir link)
        O YouTube (video no listado)
```

---

## 📋 CHECKLIST FINAL ANTES DE ENTREGAR

### General:
- [ ] Presentación tiene 14-16 slides (no más)
- [ ] Tiempo estimado: 15-20 minutos
- [ ] Todas las imágenes tienen buena calidad
- [ ] Colores consistentes (tema turquesa/teal)
- [ ] Tipografía legible a distancia

### Contenido Técnico:
- [ ] Se explica QUÉ resuelve (no solo cómo)
- [ ] Caso real incluido con datos específicos
- [ ] Métricas de impacto claramente mostradas
- [ ] Stack tecnológico completo listado
- [ ] Referencias a código y documentación

### Archivos para Entregar:
- [ ] Presentacion_Slides.pdf
- [ ] URL_Presentacion.txt (link a Google Slides)
- [ ] Screenshots/ (carpeta con imágenes)
- [ ] Videos/ (si grabaste demo)
- [ ] README_PROYECTO.md (índice principal)

### Extras (Opcionales):
- [ ] QR code con link a presentación
- [ ] QR code con link a demo en vivo
- [ ] Handout imprimible (resumen 1 página)
- [ ] Video demo embebido en slides

---

## 🎯 ALTERNATIVAS A GOOGLE SLIDES

### OPCIÓN 2: Microsoft PowerPoint

**Pros:**
✅ Más opciones de animación
✅ Integración con Office 365
✅ Offline capable

**Contras:**
❌ Requiere licencia (o usar web gratuito)
❌ Menos colaborativo

**Cómo usar:**
1. Descargar plantilla "Tech Startup" o "Marina"
2. Seguir mismos pasos que Google Slides
3. Exportar a PDF o PPTX para compartir

---

### OPCIÓN 3: Canva (Más Visual)

**URL:** https://canva.com

**Pros:**
✅ Templates profesionales pre-diseñados
✅ Librería de iconos y fotos gratis
✅ Muy intuitivo (drag & drop)
✅ Export a PDF de alta calidad

**Contras:**
❌ Menos control granular
❌ Versión gratis tiene limitaciones

**Cómo usar:**
1. Buscar "Tech Presentation Template"
2. Personalizar con tu contenido
3. Reemplazar fotos genéricas con screenshots reales
4. Descargar como PDF o compartir link

**Plantillas recomendadas:**
- "Tech Startup Pitch Deck" (Oscuro)
- "Minimalist Technology" (Limpio)
- "Digital Agency Presentation" (Moderno)

---

### OPCIÓN 4: Reveal.js (Para Devs)

**URL:** https://revealjs.com

**Pros:**
✅ Markdown nativo (copiar/pegar directo)
✅ Version control con Git
✅ Animaciones CSS personalizables
✅ Temas oscuros hermosos

**Contras:**
❌ Requiere conocimiento HTML/CSS
❌ Curva de aprendizaje más alta

**Instalación:**
```bash
npm install -g reveal-md

# Crear presentación
reveal-md PRESENTACION_DIPLOMADO.md --theme black

# Exportar a PDF
reveal-md PRESENTACION_DIPLOMADO.md --print slides.pdf
```

---

## 🚀 DÍA DE LA PRESENTACIÓN

### 1 Hora Antes:
- [ ] Laptop cargado + cargador de respaldo
- [ ] Abrir presentación en Google Slides (en línea)
- [ ] Abrir presentación PDF descargado (backup offline)
- [ ] Probar proyector/pantalla
- [ ] Abrir demo en vivo en otra pestaña
- [ ] Celular con data activa (backup Internet)

### Durante:
- [ ] Modo presentador activado (ver notas)
- [ ] Timer visible (20 min máximo)
- [ ] Slides avanzadas con espacebar (no click)
- [ ] Pausar en Slide 7 (caso real) - explicar detalle
- [ ] Mostrar demo en vivo en Slide 8 (si conexión estable)

### Después:
- [ ] Compartir link a presentación con profesores
- [ ] Compartir link a demo en vivo
- [ ] Responder preguntas con datos específicos

---

## 📞 SOPORTE Y AYUDA

Si necesitas ayuda para crear la presentación visual:

**Diseño:**
- Canva tutorials: https://youtube.com/canva
- Google Slides tips: https://youtube.com/googledrive

**Screenshots:**
- Windows: Win + Shift + S
- Mac: Cmd + Shift + 4
- Herramienta: Greenshot (gratis)

**Diagramas:**
- Draw.io: https://app.diagrams.net
- Excalidraw: https://excalidraw.com
- Mermaid Live: https://mermaid.live

**Videos:**
- OBS Studio: https://obsproject.com
- Loom: https://loom.com (grabación rápida)

---

**Éxito en tu presentación! 🎓**

