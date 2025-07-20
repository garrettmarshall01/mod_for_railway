import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='refresh_token.env')

refresh_token = os.getenv("HL_REFRESH_TOKEN")
client_id = os.getenv("HL_CLIENT_ID")
client_secret = os.getenv("HL_CLIENT_SECRET")

data = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "client_id": client_id,
    "client_secret": client_secret,
}

try:
    response = requests.post("https://services.leadconnectorhq.com/oauth/token", data=data)
    print(f"✅ Status: {response.status_code}")
    print("🔐 Access Token:", response.json().get("access_token"))
    print("🔁 Refresh Token:", response.json().get("refresh_token"))
    print("📄 Full Response:", response.json())
except requests.RequestException as e:
    print(f"❌ Status: {getattr(e.response, 'status_code', 'No Status')}")
    print(f"❌ Response content: {getattr(e.response, 'text', 'No Content')}")
    print(f"❌ Error refreshing token: {e}")