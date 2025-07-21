import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN_FILE = "refresh_token.txt"

def read_refresh_token():
    try:
        with open(REFRESH_TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("❌ refresh_token.txt not found.")
        return None

def write_refresh_token(token):
    with open(REFRESH_TOKEN_FILE, "w") as f:
        f.write(token)

def refresh_access_token():
    refresh_token = read_refresh_token()
    if not refresh_token:
        print("❌ No refresh token available.")
        return None

    url = "https://services.leadconnectorhq.com/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]
        new_refresh_token = tokens["refresh_token"]
        write_refresh_token(new_refresh_token)
        print("✅ Access token and refresh token updated.")
        return access_token
    else:
        print("❌ Failed to refresh token.")
        print("Status code:", response.status_code)
        print("Response text:", response.text)
        return None

if __name__ == "__main__":
    refresh_access_token()
