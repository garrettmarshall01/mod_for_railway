import os
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='refresh_token.env')

app = Flask(__name__)

def refresh_access_token():
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
        response.raise_for_status()
        access_token = response.json().get("access_token")
        print("🔐 Access token used:", access_token[:30] + "..." if access_token else "❌ No token")
        return access_token
    except requests.RequestException as e:
        print(f"❌ Token refresh failed: {e}")
        return None

def extract_main_image(page_url):
    headers = {"User-Agent": "Mozilla/5.0"}
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

@app.route("/create-social-post", methods=["POST"])
def create_social_post():
    data = request.get_json()
    source_url = data.get("url")
    category_id = data.get("categoryId")
    if not category_id or not source_url:
        return jsonify({"error": "Missing 'categoryId' or 'url'"}), 400

    try:
        image_url = extract_main_image(source_url)
        if not image_url:
            return jsonify({"error": "No image found at URL"}), 404
    except Exception as e:
        return jsonify({"error": f"Image extraction failed: {str(e)}"}), 500

    access_token = refresh_access_token()
    if not access_token:
        return jsonify({"error": "Token refresh failed"}), 500

    json_data = {
        "userId": "I9VZlLtgWN8UYrWRxgi6",
        "accountIds": [
            "67894a07ff96da90cbac088f_JcjR61IOaXCNoZfDzZZn_F4B2LFRy78_profile"
        ],
        "summary": data.get("summary", "Hello World"),
        "media": [
            {"url": image_url, "caption": data.get("caption", "Auto-generated image")}
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
        "Version": "2021-07-28",
    }

    try:
        response = requests.post(
            "https://services.leadconnectorhq.com/social-media-posting/JcjR61IOaXCNoZfDzZZn/posts",
            headers=headers,
            json=json_data,
        )
        return jsonify({
            "status_code": response.status_code,
            "response": response.json()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)