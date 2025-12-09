import requests
import json
import sys

def init_auth():
    url = "http://localhost:8000/api/auth/setup/create_admin"
    payload = {
        "email": "admin@fme.cl",
        "password": "admin",
        "nombre_completo": "Super Admin",
        "role_id": 0, # Ignored by endpoint
        "is_active": True
    }
    
    print(f"Calling {url}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print("✅ Admin user created successfully!")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 400:
            print("⚠️ Setup already completed (Users exist).")
            print(response.json())
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    init_auth()
