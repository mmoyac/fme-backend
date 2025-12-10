
import mercadopago
import os
from fastapi import HTTPException
from database.models import Pedido
from sqlalchemy.orm import Session

# Inicializar SDK
# Obtenemos el token de ENV. Si no existe, fallará al iniciar pagos, pero permite levantar la app.
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")

class PaymentService:
    def __init__(self):
        self.sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

    def create_preference(self, pedido: Pedido):
        """
        Crea una preferencia de pago en Mercado Pago para un pedido.
        """
        if not MP_ACCESS_TOKEN:
            raise HTTPException(status_code=500, detail="Mercado Pago token not configured")

        # Construir items para MP
        items = []
        for item in pedido.items:
            items.append({
                "id": str(item.producto.sku),
                "title": item.producto.nombre,
                "quantity": item.cantidad,
                "currency_id": "CLP",
                "unit_price": float(item.precio_unitario_venta)
            })

        # Configurar preferencia
        preference_data = {
            "items": items,
            "payer": {
                "name": pedido.cliente.nombre,
                "surname": pedido.cliente.apellido,
                "email": pedido.cliente.email,
                "phone": {
                    "area_code": "",
                    "number": pedido.cliente.telefono
                },
                "address": {
                    "street_name": pedido.cliente.direccion or "",
                    "street_number": 0,
                    "zip_code": ""
                }
            },
            "back_urls": {
                "success": "https://masasestacion.cl/checkout/success",
                "failure": "https://masasestacion.cl/checkout/failure",
                "pending": "https://masasestacion.cl/checkout/pending"
            },
            "auto_return": "approved",
            "external_reference": str(pedido.id), # Importante para conciliar
            "statement_descriptor": "MASAS ESTACION",
            "notification_url": "https://api.masasestacion.cl/api/payments/webhook" # Webhook real
        }

        preference_response = self.sdk.preference().create(preference_data)
        
        if preference_response["status"] != 201:
            raise HTTPException(status_code=500, detail=f"Error creating MP preference: {preference_response}")

        return preference_response["response"]

    def check_payment(self, payment_id: str):
        """
        Consulta el estado de un pago directamente a Mercado Pago.
        """
        payment_info = self.sdk.payment().get(payment_id)
        
        if payment_info["status"] != 200:
            return None
            
        return payment_info["response"]

payment_service = PaymentService()
