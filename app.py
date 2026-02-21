import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
RESEND_URL = "https://api.resend.com/emails"

def get_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing environment variable: {name}")
    return val

def send_email_with_image(lat, lon, image_bytes, filename="pothole.jpg"):
    resend_api_key = get_env("RESEND_API_KEY")
    resend_from = get_env("RESEND_FROM")
    to_email = get_env("TO_EMAIL")

    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    attachment_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "from": resend_from,
        "to": [to_email],
        "subject": "⚠️ Pothole Detected",
        "text": f"Pothole detected.\n\nLat: {lat}\nLon: {lon}\nGoogle Maps: {maps_link}\n",
        "attachments": [{"filename": filename, "content": attachment_b64}],
    }

    headers = {"Authorization": f"Bearer {resend_api_key}", "Content-Type": "application/json"}

    r = requests.post(RESEND_URL, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/report")
def report():
    api_key = get_env("API_KEY")  # حماية

    if request.headers.get("X-API-KEY") != api_key:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"ok": False, "error": "missing image"}), 400

    lat = request.form.get("lat")
    lon = request.form.get("lon")
    if not lat or not lon:
        return jsonify({"ok": False, "error": "missing lat/lon"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    try:
        data = send_email_with_image(lat, lon, image_bytes, filename=image_file.filename or "pothole.jpg")
        return jsonify({"ok": True, "resend": data})
    except Exception as e:
        # يظهر السبب في Logs بدل ما يطيح السيرفر
        print("REPORT ERROR:", repr(e))
        return jsonify({"ok": False, "error": str(e)}), 500
