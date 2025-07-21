
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN_FILE = "refresh_token.txt"

def load_refresh_token():
    with open(REFRESH_TOKEN_FILE, "r") as f:
        return f.read().strip()

def save_refresh_token(token):
    with open(REFRESH_TOKEN_FILE, "w") as f:
        f.write(token.strip())

def get_access_token():
    refresh_token = load_refresh_token()
    url = "https://services.leadconnectorhq.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token
    }

    response = requests.post(url, data=data)
    if response.status_code != 200:
        print("Failed to refresh token:", response.text)
        return None

    tokens = response.json()
    save_refresh_token(tokens["refresh_token"])
    return tokens["access_token"]

def make_api_call():
    access_token = get_access_token()
    if not access_token:
        return {"error": "Token refresh failed"}

    url = "https://services.leadconnectorhq.com/v1/locations"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    result = make_api_call()
    print(result)
