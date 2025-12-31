import mercadopago
import json

# Tu Access Token de "Prueba" (que parece de Prod)
ACCESS_TOKEN = "APP_USR-2020000981107633-120917-4f5d46496989e099e95a044d3285ab41-3052967873"

def check_credentials():
    print(f"🔍 Consultando credenciales para token...")
    sdk = mercadopago.SDK(ACCESS_TOKEN)
    
    # Intentar obtener info de la cuenta
    try:
        # No hay endpoint directo público documentado fácil en el SDK para "mis credenciales",
        # pero podemos crear un usuario de prueba para ver si el token funciona en sandbox
        print("Intentando crear una Preferencia de prueba...")
        
        pref_data = {
            "items": [{"title": "Test", "quantity": 1, "unit_price": 100}],
            "payer": {"email": "test_user_1234@test.com"}
        }
        res = sdk.preference().create(pref_data)
        
        if res["status"] == 201:
            print("✅ El Access Token FUNCIONA para crear preferencias.")
            print(f"Modo: {'Sandbox' if res['response'].get('sandbox_init_point') else 'Producción'}")
            print("Init Point:", res['response']['init_point'])
            print("Sandbox Init Point:", res['response']['sandbox_init_point'])
            
            # Si permite crear preferencia, al menos el token sirve.
            # El error 401 "Unauthorized use of live credentials" viene del FRONTEND
            # cuando intenta usar la Public Key para tokenizar la tarjeta de prueba.
        else:
            print(f"❌ Error creando preferencia: {res['status']}")
            print(res)

    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    check_credentials()
