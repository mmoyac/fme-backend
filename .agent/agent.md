# FME Backend - Guía para IA

## Entorno Virtual (IMPORTANTE)

Este proyecto **SIEMPRE** debe usar el entorno virtual de Python ubicado en `venv/`.

### Comandos que DEBES usar:

#### Ejecutar el servidor de desarrollo:
```bash
.\venv\Scripts\uvicorn.exe main:app --reload
```

#### Ejecutar scripts Python:
```bash
.\venv\Scripts\python.exe scripts/nombre_del_script.py
```

#### Instalar nuevas dependencias:
```bash
.\venv\Scripts\python.exe -m pip install nombre-paquete
```

#### Actualizar requirements.txt después de instalar:
```bash
.\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

### ⚠️ NO uses estos comandos:
- ❌ `python main.py`
- ❌ `uvicorn main:app --reload`
- ❌ `pip install ...`

Estos comandos usarían el Python global en lugar del entorno virtual.

---

## Estructura del Proyecto

### Base de Datos
- **Motor**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migraciones**: Alembic
- **Modelos**: `database/models.py`

### Autenticación
- **Sistema**: JWT (JSON Web Tokens)
- **Hash de contraseñas**: Argon2
- **Roles**: Admin, Administrador, Tesorero, Vendedor
- **RBAC**: Control de acceso basado en roles con menús dinámicos

### API Endpoints Principales

#### Autenticación (`/api/auth`)
- `POST /token` - Login y obtención de token JWT
- `GET /me` - Información del usuario actual
- `GET /menu` - Menú dinámico según rol del usuario

#### Administración (`/api/admin`)
- `/users` - CRUD de usuarios
- `/roles` - Gestión de roles
- `/menu_items` - Configuración de ítems de menú
- `/roles/{role_id}/menu` - Asignación de menús a roles

#### Catálogos
- `/api/productos` - Gestión de productos
- `/api/locales` - Gestión de locales/sucursales
- `/api/clientes` - Gestión de clientes

#### Operaciones
- `/api/inventario` - Control de stock por local
- `/api/precios` - Precios por producto y local
- `/api/pedidos` - Gestión de pedidos/ventas
- `/api/movimientos-inventario` - Historial de movimientos

#### Pagos
- `/api/payments` - Integración con Mercado Pago

---

## Scripts de Utilidad

### `scripts/seed_api.py`
Pobla la base de datos con datos iniciales:
- Roles: admin, administrador, tesorero, vendedor
- Usuarios de prueba con diferentes roles

**Ejecutar:**
```bash
.\venv\Scripts\python.exe scripts/seed_api.py
```

### `scripts/seed_menu_rbac.py`
Configura los ítems de menú y permisos por rol.

**Ejecutar:**
```bash
.\venv\Scripts\python.exe scripts/seed_menu_rbac.py
```

---

## Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fme_db

# JWT
SECRET_KEY=tu-clave-secreta-muy-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Mercado Pago
MP_ACCESS_TOKEN=tu-access-token-de-mercadopago
MP_PUBLIC_KEY=tu-public-key-de-mercadopago
```

---

## Flujo de Desarrollo

### 1. Activar entorno (opcional, para trabajar en terminal)
```bash
.\venv\Scripts\activate
```

### 2. Instalar/Actualizar dependencias
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Ejecutar migraciones (si hay cambios en modelos)
```bash
.\venv\Scripts\alembic.exe upgrade head
```

### 4. Poblar datos iniciales (primera vez)
```bash
.\venv\Scripts\python.exe scripts/seed_api.py
```

### 5. Levantar servidor
```bash
.\venv\Scripts\uvicorn.exe main:app --reload
```

---

## Testing

### Ejecutar tests:
```bash
.\venv\Scripts\pytest.exe
```

### Con cobertura:
```bash
.\venv\Scripts\pytest.exe --cov=. --cov-report=html
```

---

## Usuarios de Prueba

Después de ejecutar `seed_api.py`:

| Email | Password | Rol |
|-------|----------|-----|
| admin@fme.cl | admin | Admin (superusuario) |
| cliente@fme.cl | admin | Administrador (dueño) |
| tesorero@fme.cl | admin | Tesorero |
| vendedor@fme.cl | admin | Vendedor |

---

## Notas Importantes

1. **Siempre usa el entorno virtual** - Todos los comandos Python deben ejecutarse desde `.\venv\Scripts\`
2. **No commitear `.env`** - Contiene información sensible
3. **No commitear `venv/`** - Ya está en `.gitignore`
4. **Actualizar `requirements.txt`** después de instalar nuevas dependencias
5. **Ejecutar migraciones** antes de levantar el servidor si hay cambios en modelos
