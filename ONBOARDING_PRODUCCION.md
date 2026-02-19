# 🚀 Onboarding de Nuevos Tenants en Producción

Guía completa para agregar un nuevo cliente al sistema multi-tenant en el VPS.

---

## 📋 Requisitos Previos

- Acceso SSH al VPS: `root@168.231.96.205`
- Acceso a Cloudflare (para configurar DNS)
- Datos del cliente para llenar los CSV

---

## 1. 📦 Preparar Datos del Cliente (Local)

### 1.1. Crear carpeta del cliente

```bash
cd d:\ProyectosAI\Masas_Estacion\fme-backend
mkdir tenant_cliente_nuevo
```

### 1.2. Copiar templates y llenar con datos reales

```bash
# Copiar templates
copy templates_csv\*.csv tenant_cliente_nuevo\

# Archivos a editar:
# - tenant_config.csv      → Información de la empresa
# - locales.csv            → Locales físicos + WEB
# - productos.csv          → Catálogo de productos
# - precios.csv            → Precios por local
# - inventario.csv         → Stock inicial
# - usuarios.csv           → Admin y vendedores
```

### 1.3. Validar datos críticos

**tenant_config.csv:**
- `codigo`: Sin espacios, minúsculas, sin guiones (ej: `panaderialopez`)
- `dominio_principal`: Dominio real del cliente (ej: `panaderialopez.cl`)

**locales.csv:**
- **SIEMPRE** incluir un local con `codigo=WEB` como primera fila
- `nombre` debe ser "Tienda Online" o similar

**usuarios.csv:**
- `password`: Será hasheado automáticamente, usar contraseña temporal fuerte
- `role_id`: 1 = admin, 2 = vendedor
- `local_defecto_codigo`: Debe coincidir con un código en locales.csv

---

## 2. 📤 Transferir CSV al VPS

### 2.1. Crear directorio en VPS

```bash
ssh root@168.231.96.205
mkdir -p /root/onboarding/cliente_nuevo
exit
```

### 2.2. Copiar archivos con SCP

```powershell
# Desde PowerShell local
scp -r tenant_cliente_nuevo/*.csv root@168.231.96.205:/root/onboarding/cliente_nuevo/
```

**Verificar transferencia:**
```bash
ssh root@168.231.96.205
ls -lh /root/onboarding/cliente_nuevo/
# Debe mostrar 6 archivos CSV
```

---

## 3. 🔧 Ejecutar Importación en Producción

### 3.1. Conectar al VPS

```bash
ssh root@168.231.96.205
cd /root/docker/masas-estacion
```

### 3.2. Ejecutar script de importación

```bash
docker exec masas_estacion_backend python scripts/import_tenant_csv.py --folder /root/onboarding/cliente_nuevo/
```

**Salida esperada:**
```
🔧 Actualizando secuencias de base de datos...
✅ Secuencias actualizadas (6 tablas)

📋 Importando configuración del tenant...
✅ Tenant creado: Panadería López (ID: 4)

🏪 Importando locales...
✅ Local creado: Tienda Online (Código: WEB)
✅ Local creado: Sucursal Centro (Código: CENTRO)

📦 Importando productos...
✅ 15 productos creados

💰 Importando precios...
✅ 45 precios importados

📊 Importando inventario...
✅ 30 registros de inventario importados

👤 Importando usuarios...
✅ Usuario creado: admin@panaderialopez.cl
✅ Usuario creado: vendedor.centro@panaderialopez.cl

============================================================
✅ ¡IMPORTACIÓN COMPLETADA EXITOSAMENTE!
============================================================
Tenant: Panadería López
Dominio: panaderialopez.cl
Locales: 2
Productos: 15
Usuarios: 2
============================================================
```

### 3.3. Anotar el ID del tenant

**Importante:** Guarda el ID del tenant (ej: 4) que aparece en el log.

---

## 4. 🌐 Configurar DNS en Cloudflare

### 4.1. Acceder a Cloudflare

1. Ir a: https://dash.cloudflare.com
2. Seleccionar dominio: **masasestacion.cl**
3. Ir a: **DNS** → **Registros**

### 4.2. Agregar registros DNS

**Para Landing Page:**
```
Tipo: A
Nombre: cliente
Contenido: 168.231.96.205
TTL: Auto
Proxy: ❌ Solo DNS (nube gris)
```

**Para Backoffice:**
```
Tipo: A
Nombre: admin.cliente
Contenido: 168.231.96.205
TTL: Auto
Proxy: ❌ Solo DNS (nube gris)
```

**Ejemplo para "Panadería López":**
- `panaderialopez.masasestacion.cl` → 168.231.96.205
- `admin.panaderialopez.masasestacion.cl` → 168.231.96.205

### 4.3. Verificar propagación DNS

```bash
# Desde local, esperar 1-5 minutos y probar:
nslookup panaderialopez.masasestacion.cl
# Debe resolver a 168.231.96.205
```

---

## 5. 🔐 Actualizar Código de Tenant (Si es necesario)

Si el dominio del cliente es un **subdominio** de masasestacion.cl, el sistema lo detectará automáticamente por el campo `subdomain` en la BD.

Si usas dominios `.local` para desarrollo o el código no coincide:

```bash
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "UPDATE tenants SET codigo = 'panaderialopez' WHERE id = 4;"
```

---

## 6. ✅ Verificar Funcionamiento

### 6.1. Probar Landing Page

```
https://panaderialopez.masasestacion.cl
```

**Debe mostrar:**
- Nombre comercial del cliente
- Logo/branding configurado
- Catálogo de productos con precios
- Footer personalizado

### 6.2. Probar Backoffice

```
https://admin.panaderialopez.masasestacion.cl
```

**Credenciales:**
- Usuario: `admin@panaderialopez.cl` (el email del CSV)
- Contraseña: La que pusiste en usuarios.csv

**Verificar:**
- Login exitoso
- Dashboard carga correctamente
- Productos visibles
- Inventario correcto
- Locales listados

### 6.3. Probar API directamente

```bash
curl https://api.masasestacion.cl/api/config/landing -H "Host: panaderialopez.masasestacion.cl"
```

Debe retornar JSON con la configuración del tenant correcto.

---

## 7. 🐛 Solución de Problemas

### Error: "No se pudo detectar el tenant"

**Causa:** El código del tenant no coincide con el subdominio.

**Solución:**
```bash
# Verificar código actual
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "SELECT id, nombre, codigo, subdomain FROM tenants WHERE id = X;"

# Actualizar si es necesario
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "UPDATE tenants SET codigo = 'codigo_correcto', subdomain = 'subdominio' WHERE id = X;"
```

### Error: "Incorrect username or password"

**Causa 1:** Contraseña incorrecta en usuarios.csv
**Solución:** Resetear contraseña:

```bash
# En el VPS
docker exec -it masas_estacion_backend bash
python
>>> from utils.security import get_password_hash
>>> print(get_password_hash("nueva_password_123"))
# Copiar el hash resultante

# Actualizar en BD
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "UPDATE users SET hashed_password = 'EL_HASH_COPIADO' WHERE email = 'admin@cliente.cl';"
```

**Causa 2:** Usuario en tenant incorrecto
**Solución:**
```bash
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "SELECT id, email, tenant_id FROM users WHERE email = 'admin@cliente.cl';"
# Verificar que tenant_id coincida con el ID del tenant creado
```

### Error: CORS al hacer login

**Causa:** El dominio no está en la lista de orígenes permitidos.

**Solución:** Editar `main.py` en el backend:

```python
origins = [
    # ... otros dominios
    "https://cliente.masasestacion.cl",
    "https://admin.cliente.masasestacion.cl",
]
```

**Reiniciar backend:**
```bash
cd /root/docker/masas-estacion
docker compose -f docker-compose.prod.yml restart backend
```

### Productos sin stock o sin precio

**Causa:** No se importaron correctamente precios o inventario.

**Solución:** Verificar en BD:
```bash
# Precios
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "SELECT COUNT(*) FROM precios p JOIN locales l ON p.local_id = l.id WHERE l.tenant_id = X;"

# Inventario
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "SELECT COUNT(*) FROM inventario i JOIN locales l ON i.local_id = l.id WHERE l.tenant_id = X;"
```

Si faltan registros, re-ejecutar el script de importación (eliminando el tenant primero):
```bash
# CUIDADO: Esto elimina TODOS los datos del tenant
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "DELETE FROM tenants WHERE id = X CASCADE;"
```

---

## 8. 📧 Entregar Credenciales al Cliente

**Template de email:**

```
Estimado/a Cliente,

Su tienda online ya está lista en:
🌐 https://cliente.masasestacion.cl

Panel de administración:
🔐 https://admin.cliente.masasestacion.cl

Credenciales de acceso:
Usuario: admin@cliente.cl
Contraseña: [CONTRASEÑA_TEMPORAL]

Por favor cambie su contraseña después del primer inicio de sesión.

Saludos,
Equipo Técnico
```

---

## 9. 🔄 Mantenimiento Post-Onboarding

### Actualizar datos del tenant

```bash
# Ejemplo: Cambiar nombre comercial
docker exec -i masas_estacion_backend psql -U fme -d fme_database -c "UPDATE configuracion_landing SET nombre_comercial = 'Nuevo Nombre' WHERE tenant_id = X;"

# Reiniciar backend para refrescar cache (si aplica)
docker compose -f docker-compose.prod.yml restart backend
```

### Agregar nuevos usuarios

Usar el backoffice del cliente o ejecutar SQL:
```bash
docker exec -it masas_estacion_backend bash
python
>>> from utils.security import get_password_hash
>>> from database.database import SessionLocal
>>> from database.models import User
>>> db = SessionLocal()
>>> user = User(
...     tenant_id=X,
...     email="nuevo@cliente.cl",
...     nombre_completo="Nuevo Usuario",
...     hashed_password=get_password_hash("password123"),
...     role_id=2,
...     local_defecto_id=Y,
...     is_active=True
... )
>>> db.add(user)
>>> db.commit()
```

---

## 10. 📊 Checklist Final

Antes de entregar al cliente:

- [ ] Landing carga correctamente con branding
- [ ] Catálogo muestra todos los productos
- [ ] Precios visibles en todos los productos
- [ ] Login de backoffice funciona
- [ ] Dashboard carga sin errores
- [ ] CRUD de productos funciona
- [ ] Gestión de inventario funciona
- [ ] Sistema de pedidos funciona
- [ ] Boletas se generan correctamente
- [ ] DNS propagado (nslookup exitoso)
- [ ] Credenciales documentadas y enviadas

---

## 🆘 Contacto de Soporte

**VPS:** root@168.231.96.205  
**Puerto SSH:** 22  
**Logs del backend:**
```bash
docker logs masas_estacion_backend --tail 100 -f
```

**Logs de la BD:**
```bash
docker logs masas_estacion_db --tail 100 -f
```

---

**Última Actualización:** 2026-02-01  
**Autor:** Sistema de Onboarding Multi-Tenant  
**Versión:** 1.0
