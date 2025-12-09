import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def verify_auth():
    # 1. Login
    token_url = f"{BASE_URL}/api/auth/token"
    # FormData format for OAuth2PasswordRequestForm
    payload = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    print(f"1. Testing Login ({token_url})...")
    try:
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Login successful!")
            print(f"   Token: {access_token[:20]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 2. Get User Info (Protected)
    user_url = f"{BASE_URL}/api/auth/users/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\n2. Testing Protected Route ({user_url})...")
    try:
        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Access successful!")
            print(f"   User: {user_data['email']} (Role: {user_data['role']['nombre']})")
        else:
            print(f"❌ Access failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_auth()
