# 🔒 Guía de Configuración SSL/Nginx para Nuevos Tenants

Esta guía documenta el proceso completo para configurar dominios con certificados SSL para nuevos tenants en el sistema multi-tenant.

---

## � Modo Rápido: Script Automatizado

**¡NUEVO!** Ahora puedes usar el script automatizado para configurar todo en un solo comando:

```powershell
.\setup-tenant-ssl.ps1 -Domain "bigschool.lexastech.cl" -Email "info@lexastech.cl"
```

**Prerequisitos**:
- DNS configurado (A records → 168.231.96.205)
- Acceso SSH al VPS (el script te pedirá la contraseña 2-3 veces)

**El script hace todo automáticamente**:
1. ✅ Verifica que el DNS esté configurado
2. ✅ Genera archivo `.conf` con bloques nginx
3. ✅ Copia configuración al VPS
4. ✅ Obtiene certificados SSL con certbot
5. ✅ Activa HTTPS en ambos dominios
6. ✅ Verifica que todo funcione

**Si prefieres el proceso manual**, continúa leyendo la guía completa ⬇️

---

## 📋 Prerequisitos (Proceso Manual)

Antes de comenzar, asegúrate de tener:

1. **Acceso SSH al VPS**: `ssh root@168.231.96.205`
2. **Docker Compose ejecutándose**: Contenedores `nginx_proxy` y `nginx_certbot` activos
3. **DNS configurado**: Los dominios deben apuntar a la IP del VPS (168.231.96.205)

### Verificar DNS antes de continuar

```bash
# Verificar que los dominios resuelven correctamente
nslookup elolivo.lexastech.cl
nslookup admin.elolivo.lexastech.cl
```

**Resultado esperado**: Ambos deben resolver a `168.231.96.205`

---

## 🎯 Proceso Paso a Paso

### Paso 1: Crear Tenant en Base de Datos

Primero crea el tenant en la BD con el **dominio principal** (sin el prefijo `admin.`):

```sql
INSERT INTO tenants (nombre, codigo, dominio_principal, subdomain, activo)
VALUES ('El Olivo', 'elolivo', 'elolivo.lexastech.cl', NULL, true);
```

**Importante**: 
- `dominio_principal`: El dominio de la landing (sin admin)
- `subdomain`: Solo si usas estructura `X.masasestacion.cl`

### Paso 2: Crear Configuración Nginx

Crea un archivo de configuración nginx local. Ejemplo: `elolivo.lexastech.cl.conf`

```nginx
# Landing Page - elolivo.lexastech.cl
server {
    listen 80;
    server_name elolivo.lexastech.cl;

    # Ruta para validación de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirigir todo a HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name elolivo.lexastech.cl;

    # Certificados SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/elolivo.lexastech.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/elolivo.lexastech.cl/privkey.pem;

    # Configuraciones SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy a contenedor Docker de landing
    location / {
        proxy_pass http://masas_estacion_frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backoffice Admin - admin.elolivo.lexastech.cl
server {
    listen 80;
    server_name admin.elolivo.lexastech.cl;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name admin.elolivo.lexastech.cl;

    # IMPORTANTE: Usa el mismo certificado que el dominio principal
    # certbot crea un certificado SAN que incluye ambos dominios
    ssl_certificate /etc/letsencrypt/live/elolivo.lexastech.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/elolivo.lexastech.cl/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy a contenedor Docker de backoffice
    location / {
        proxy_pass http://masas_estacion_backoffice:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Paso 3: Copiar Configuración al VPS

```powershell
# Copiar archivo local al VPS (temporal)
scp elolivo.lexastech.cl.conf root@168.231.96.205:/tmp/elolivo.conf
```

### Paso 4: Instalar Configuración (Sin SSL aún)

```powershell
# Copiar a directorio de nginx y recargar
ssh root@168.231.96.205 "cp /tmp/elolivo.conf /root/docker/nginx-proxy/conf.d/elolivo.lexastech.cl.conf && docker exec nginx_proxy nginx -s reload"
```

**Nota**: Por ahora los bloques HTTPS (443) fallarán, pero eso es normal. Se activan después del certificado.

### Paso 5: Obtener Certificados SSL con Let's Encrypt

Este es el paso **crítico**. Certbot generará un certificado que incluye ambos dominios (landing + admin).

```powershell
ssh root@168.231.96.205 "echo '1' | docker exec -i nginx_certbot certbot certonly --webroot -w /var/www/certbot --email info@lexastech.cl --agree-tos -d elolivo.lexastech.cl -d admin.elolivo.lexastech.cl"
```

**Desglose del comando**:
- `echo '1' |`: Selecciona automáticamente la primera cuenta de certbot si hay múltiples
- `certonly`: Solo obtener certificado, no instalar
- `--webroot`: Método de validación HTTP-01
- `-w /var/www/certbot`: Directorio compartido con nginx
- `--email`: Email del administrador
- `--agree-tos`: Aceptar términos de servicio
- `-d dominio1 -d dominio2`: Lista de dominios para el certificado

**Resultado esperado**:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/elolivo.lexastech.cl/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/elolivo.lexastech.cl/privkey.pem
This certificate expires on 2026-05-25.
```

### Paso 6: Actualizar Configuración con SSL

**IMPORTANTE**: Ambos bloques `server` (landing y admin) deben usar **el mismo certificado** porque certbot creó un certificado SAN (Subject Alternative Name) que incluye ambos dominios.

Verifica que tu archivo `.conf` tenga:

```nginx
# Landing
ssl_certificate /etc/letsencrypt/live/elolivo.lexastech.cl/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/elolivo.lexastech.cl/privkey.pem;

# Admin (mismo certificado)
ssl_certificate /etc/letsencrypt/live/elolivo.lexastech.cl/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/elolivo.lexastech.cl/privkey.pem;
```

### Paso 7: Recargar Nginx con SSL Activo

```powershell
# Copiar configuración actualizada, validar y recargar
ssh root@168.231.96.205 "cp /tmp/elolivo.conf /root/docker/nginx-proxy/conf.d/elolivo.lexastech.cl.conf && docker exec nginx_proxy nginx -t && docker exec nginx_proxy nginx -s reload"
```

**Resultado esperado**:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
signal process started
```

### Paso 8: Verificar Funcionamiento

Abre en tu navegador:
- ✅ `https://elolivo.lexastech.cl` → Debe cargar la landing sin error SSL
- ✅ `https://admin.elolivo.lexastech.cl` → Debe cargar el backoffice sin error SSL
- ✅ `http://elolivo.lexastech.cl` → Debe redirigir automáticamente a HTTPS

---

## 🔧 Troubleshooting

### Error: "Dominio no registrado como tenant"

**Causa**: El tenant no está creado en la BD o el `dominio_principal` no coincide.

**Solución**:
```sql
-- Verificar tenants registrados
SELECT id, nombre, dominio_principal, subdomain FROM tenants;

-- Si falta, crear tenant
INSERT INTO tenants (nombre, codigo, dominio_principal, activo)
VALUES ('Nombre Cliente', 'codigo-cliente', 'cliente.lexastech.cl', true);
```

### Error: "Certificate not found" en nginx

**Causa**: Intentas activar SSL antes de obtener el certificado.

**Solución**:
1. Comenta temporalmente los bloques HTTPS (443) en el `.conf`
2. Recarga nginx
3. Obtén el certificado con certbot
4. Descomenta los bloques HTTPS
5. Recarga nginx nuevamente

### Error: "Failed authorization procedure" en certbot

**Causa**: El DNS no resuelve correctamente o nginx no está sirviendo `/.well-known/acme-challenge/`.

**Solución**:
```bash
# Verificar DNS
nslookup tudominio.lexastech.cl

# Verificar que nginx responde en puerto 80
curl -I http://tudominio.lexastech.cl

# Asegúrate de que el bloque HTTP (80) tenga:
location /.well-known/acme-challenge/ {
    root /var/www/certbot;
}
```

### Error: "Multiple ACME accounts"

**Causa**: Hay varias cuentas de Let's Encrypt registradas.

**Solución**: Usa `echo '1' | docker exec -i` para seleccionar automáticamente la primera cuenta.

### Error: Backend no detecta tenant en admin.X

**Causa**: El código de detección de tenant no reconoce prefijos administrativos.

**Solución**: Verifica que `services/tenant_service.py` tenga el código actualizado:

```python
# Detectar prefijo admin/api/backoffice
parts = hostname.split('.')
if len(parts) >= 3 and parts[0] in ['admin', 'api', 'www', 'backoffice']:
    dominio_base = '.'.join(parts[1:])
    tenant = db.query(Tenant).filter(
        Tenant.dominio_principal == dominio_base
    ).first()
```

---

## 🔄 Renovación Automática de Certificados

Los certificados de Let's Encrypt expiran cada **90 días**. El contenedor `nginx_certbot` debe tener un cron job configurado para renovar automáticamente.

**Verificar renovación automática**:
```bash
# Ver si el contenedor tiene certbot con renovación automática
ssh root@168.231.96.205 "docker exec nginx_certbot certbot renew --dry-run"
```

**Configurar renovación manual** (si no está automatizada):
```bash
# Agregar cron job en el host o contenedor
0 3 * * * docker exec nginx_certbot certbot renew --quiet && docker exec nginx_proxy nginx -s reload
```

---

## 📋 Checklist Rápido para Nuevo Tenant

- [ ] DNS configurado (A records → IP del VPS)
- [ ] Tenant creado en BD con `dominio_principal`
- [ ] Archivo `.conf` creado localmente
- [ ] Configuración copiada al VPS
- [ ] Nginx recargado (primera vez, sin SSL)
- [ ] Certificados SSL obtenidos con certbot (ambos dominios)
- [ ] Configuración actualizada con paths de certificados
- [ ] Nginx recargado (segunda vez, con SSL activo)
- [ ] Verificado acceso HTTPS en ambos dominios
- [ ] Verificado redirección HTTP → HTTPS
- [ ] Verificado login en backoffice (admin.X)
- [ ] Verificado catálogo en landing (X)

---

## 🎯 Estructura de Dominios Multi-Tenant

```
Tenant 1 (Masas Estación):
├─ masasestacion.cl              → Landing
├─ admin.masasestacion.cl        → Backoffice
└─ api.masasestacion.cl          → API REST

Tenant 2 (El Olivo):
├─ elolivo.lexastech.cl          → Landing
├─ admin.elolivo.lexastech.cl    → Backoffice
└─ Usa API compartida

Tenant 3 (Futuro Cliente):
├─ cliente.lexastech.cl          → Landing
├─ admin.cliente.lexastech.cl    → Backoffice
└─ Usa API compartida
```

**Detección automática**:
- Landing (`cliente.X`) → busca tenant por `dominio_principal = "cliente.X"`
- Backoffice (`admin.cliente.X`) → detecta prefijo `admin.`, busca tenant por `dominio_principal = "cliente.X"`

---

## 🔐 Seguridad

### Configuraciones SSL Recomendadas

Ya incluidas en el template, pero recuerda:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;

# Opcional (configuración avanzada)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
```

### Rate Limiting (Opcional)

Para proteger contra ataques DDoS:

```nginx
# En el bloque http {} de nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# En el bloque location {} de tu .conf
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://backend:8000;
}
```

---

**Última Actualización**: 2026-02-24  
**Autor**: Documentación generada para sistema multi-tenant FME  
**Versión**: 1.0
