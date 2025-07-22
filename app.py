import os
import json
from flask import Flask, request, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")

# ✅ Load Firebase credentials from env string (for Railway)
firebase_config = json.loads(os.getenv("FIREBASE_JSON"))
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Constants
COLLECTION_NAME = "tokens"
DOCUMENT_ID = "refresh_token"
FIELD_NAME = "refresh_token"
LOCATION_ID = "JcjR61IOaXCNoZfDzZZn"

app = Flask(__name__)

# Utility: Retrieve refresh token from Firestore
def get_refresh_token_from_firestore():
    doc = db.collection(COLLECTION_NAME).document(DOCUMENT_ID).get()
    if doc.exists:
        token = doc.to_dict().get(FIELD_NAME)
        print(f"🔑 Retrieved refresh token from Firestore: {token}")
        return token
    print("⚠️ No refresh token found in Firestore.")
    return None

# Utility: Store new refresh token in Firestore
def store_refresh_token_in_firestore(new_token):
    db.collection(COLLECTION_NAME).document(DOCUMENT_ID).set({FIELD_NAME: new_token})
    print("✅ Stored new refresh token in Firestore.")

# Utility: Call OAuth endpoint to refresh token
def refresh_access_token(refresh_token):
    print("🔄 Attempting to refresh access token using:", refresh_token)
    url = "https://services.leadconnectorhq.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Token refreshed successfully.")
        return token_data
    else:
        print(f"❌ Failed to refresh token. Status: {response.status_code}, Body: {response.text}")
        return None

# Step 1: Get a fresh access token on startup
access_token = None
startup_token = get_refresh_token_from_firestore()
if startup_token:
    token_data = refresh_access_token(startup_token)
    if token_data:
        access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        if new_refresh_token:
            store_refresh_token_in_firestore(new_refresh_token)

# DEBUG ENDPOINT: Just retrieve current token
@app.route('/debug-refresh-token', methods=['GET'])
def debug_refresh_token():
    token = get_refresh_token_from_firestore()
    return jsonify({"refresh_token": token})

# DEBUG ENDPOINT: Call OAuth and return new token
@app.route('/debug-token-refresh', methods=['GET'])
def debug_token_refresh():
    current_token = get_refresh_token_from_firestore()
    if not current_token:
        return jsonify({"error": "No refresh token in Firestore"}), 404

    token_response = refresh_access_token(current_token)
    if token_response:
        new_refresh_token = token_response.get("refresh_token")
        store_refresh_token_in_firestore(new_refresh_token)
        return jsonify({
            "access_token": token_response.get("access_token"),
            "new_refresh_token": new_refresh_token
        })
    else:
        return jsonify({"error": "Failed to refresh token"}), 500

# Utility: Scrape Open Graph or fallback image
def extract_main_image(page_url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ImageScraper/1.0)"}
    resp = requests.get(page_url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for attr, name in [('property', 'og:image'), ('name', 'twitter:image'), ('name', 'image')]:
        tag = soup.find("meta", {attr: name})
        if tag and tag.get("content"):
            return urljoin(page_url, tag["content"])
    img = soup.find("img")
    if img and img.get("src"):
        return urljoin(page_url, img["src"])
    return None

# MAIN POST ROUTE
@app.route("/create-social-post", methods=["POST"])
def create_social_post():
    global access_token
    data = request.get_json()
    source_url = data.get("url")
    category_id = data.get("categoryId")
    if not category_id:
        return jsonify({"error": "Missing 'categoryId'"}), 400
    if not source_url:
        return jsonify({"error": "Missing 'url'"}), 400

    try:
        image_url = extract_main_image(source_url)
        if not image_url:
            return jsonify({"error": "No image found at URL"}), 404
    except Exception as e:
        return jsonify({"error": f"Error extracting image: {str(e)}"}), 500

    json_data = {
        "userId": "I9VZlLtgWN8UYrWRxgi6",
        "accountIds": [
            "67894a07ff96da90cbac088f_JcjR61IOaXCNoZfDzZZn_F4B2LFRy78_profile"
        ],
        "summary": data.get("summary", "Hello World"),
        "media": [
            {
                "url": image_url,
                "caption": data.get("caption", "Auto-generated image"),
            }
        ],
        "status": data.get("status", "draft"),
        "followUpComment": source_url,
        "type": "post",
        "categoryId": category_id,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

    try:
        response = requests.post(
            f"https://services.leadconnectorhq.com/social-media-posting/{LOCATION_ID}/posts",
            headers=headers,
            json=json_data,
        )
        return jsonify({
            "status_code": response.status_code,
            "response": response.json()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Railway-compatible port setup
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)