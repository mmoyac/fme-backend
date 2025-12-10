# 🚀 Guía de Despliegue - Masas Estación Backend API

## 📋 Checklist Pre-Despliegue

### 1. Verificar Repositorio en GitHub

El repositorio ya está configurado. Asegúrate de estar en la rama correcta y tener los últimos cambios.

```bash
# Verificar estado
git status

# Subir cambios a main
git add .
git commit -m "feat: actualización de backend"
git push origin main
```

### 2. Configurar Secrets en GitHub

Ve a: `https://github.com/mmoyac/fme-backend/settings/secrets/actions`

Asegúrate de tener los siguientes secrets configurados:

| Secret | Valor | Descripción |
|--------|-------|-------------|
| `DOCKER_USERNAME` | `mmoyac` | Usuario de Docker Hub |
| `DOCKER_PASSWORD` | `[tu-token]` | Access Token de Docker Hub |
| `VPS_HOST` | `168.231.96.205` | IP del VPS |
| `VPS_USERNAME` | `root` | Usuario SSH |
| `VPS_SSH_KEY` | `[clave-privada]` | Clave privada SSH completa |
| `VPS_PORT` | `22` | Puerto SSH (Opcional, defecto 22) |

### 3. Preparar VPS

Conectar al VPS por SSH:

```bash
ssh root@168.231.96.205
```

Ejecutar en el VPS (solo necesario la primera vez):

```bash
# Crear directorios
mkdir -p /root/docker/masas-estacion
mkdir -p /root/docker/masas-estacion/nginx/conf.d

# Verificar que la red general-net existe
docker network ls | grep general-net

# Si no existe, crearla:
docker network create general-net
```

## 🚀 Despliegue Automático

### Opción 1: Ejecución Manual (Recomendada)

1. Ve a GitHub Actions: `https://github.com/mmoyac/fme-backend/actions`
2. Selecciona el workflow: **"Build and Push to Docker Hub"**
3. Click en **"Run workflow"**
4. Selecciona branch: `main`
5. Click en **"Run workflow"** verde
6. Espera a que complete el despliegue.

### Opción 2: Con Tag de Versión

```bash
# Crear tag de versión
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# El workflow se ejecutará automáticamente
```

## 🔍 Verificación del Despliegue

### 1. Verificar Build en GitHub Actions

- ✅ Build completado sin errores
- ✅ Imagen subida a Docker Hub (`mmoyac/masas-estacion-backend`)
- ✅ Deploy en VPS exitoso

### 2. Verificar en Docker Hub

URL: `https://hub.docker.com/r/mmoyac/masas-estacion-backend`

### 3. Verificar en VPS

```bash
# Conectar al VPS
ssh root@168.231.96.205

# Ver contenedor corriendo
docker ps | grep masas_estacion_backend

# Ver logs
cd /root/docker/masas-estacion
docker-compose logs -f backend
```

### 4. Health Check

```bash
# Desde el VPS, verificar respuesta interna con python
docker exec masas_estacion_backend python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# Resultado esperado: {'status': 'ok'}
```

### 5. Migraciones de Base de Datos (¡CRÍTICO!)
Si el despliegue incluye cambios en el modelo de datos (nuevas tablas o columnas), DEBES ejecutar las migraciones manualmente en el VPS:

```bash
# Ejecutar migraciones en el contenedor de producción
docker exec masas_estacion_backend alembic upgrade head
```
Si no haces esto, la aplicación fallará al intentar acceder a los nuevos campos.

## 🔄 Actualizar Aplicación

Para futuras actualizaciones:

```bash
# 1. Hacer cambios en el código
# 2. Commit y push
git add .
git commit -m "fix: corrección de validación"
git push

# 3. Ejecutar acción manual en GitHub o crear Tag
git tag -a v1.0.1 -m "Fix release"
git push origin v1.0.1
```

## 🐛 Troubleshooting

### Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs backend

# Reiniciar contenedor
docker-compose restart backend
```

### Error de Base de Datos

Si el backend no conecta a la base de datos, verifica las variables de entorno en el archivo `.env` del VPS (debe estar en `/root/docker/masas-estacion/.env`) o en el `docker-compose.prod.yml`.

```bash
# Verificar conexión desde contenedor
docker exec -it masas_estacion_backend python -c "from database.database import SessionLocal; print(SessionLocal())"
```
