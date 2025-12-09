"""
Configuración de fixtures y utilidades para los tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base, get_db
from main import app

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Crear sesión de base de datos para tests."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Cliente de prueba con base de datos de test."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        # Crear local WEB que es requerido por el sistema
        from database.models import Local
        local_web = db_session.query(Local).filter(Local.codigo == 'WEB').first()
        if not local_web:
            local_web = Local(
                codigo='WEB',
                nombre='Tienda Online',
                direccion='Virtual'
            )
            db_session.add(local_web)
            db_session.commit()
        
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_producto(client):
    """Crear un producto de ejemplo."""
    response = client.post(
        "/api/productos/",
        json={
            "nombre": "Pan Amasado",
            "descripcion": "Pan tradicional chileno",
            "sku": "PAN-001"
        }
    )
    return response.json()


@pytest.fixture
def sample_local(client):
    """Crear un local de ejemplo."""
    response = client.post(
        "/api/locales/",
        json={
            "codigo": "LOC1",
            "nombre": "Sucursal Centro",
            "direccion": "Av. Principal 123"
        }
    )
    return response.json()


@pytest.fixture
def sample_cliente(client):
    """Crear un cliente de ejemplo."""
    response = client.post(
        "/api/clientes/",
        json={
            "nombre": "Juan",
            "apellido": "Pérez",
            "email": "juan@example.com",
            "telefono": "+56912345678",
            "direccion": "Calle Falsa 123",
            "comuna": "Santiago"
        }
    )
    return response.json()


@pytest.fixture
def producto_con_inventario(client, sample_producto, sample_local, db_session):
    """Producto con inventario configurado."""
    from database.models import Local
    
    # Obtener el local WEB
    local_web = db_session.query(Local).filter(Local.codigo == 'WEB').first()
    
    # Crear precio en local físico
    client.post(
        "/api/precios/",
        json={
            "producto_id": sample_producto["id"],
            "local_id": sample_local["id"],
            "monto_precio": 1500.0
        }
    )
    
    # Crear precio en local WEB (requerido para pedidos frontend)
    client.post(
        "/api/precios/",
        json={
            "producto_id": sample_producto["id"],
            "local_id": local_web.id,
            "monto_precio": 1500.0
        }
    )
    
    # Crear inventario en local físico
    client.put(
        f"/api/inventario/producto/{sample_producto['id']}/local/{sample_local['id']}",
        json={"cantidad_stock": 100}
    )
    
    return {
        "producto": sample_producto,
        "local": sample_local
    }
