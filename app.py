import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ["API_KEY"]              # حماية endpoint
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM = os.environ["RESEND_FROM"]      # مثل: "Pothole Bot <alerts@yourdomain.com>"
TO_EMAIL = os.environ["TO_EMAIL"]            # ايميلك

RESEND_URL = "https://api.resend.com/emails"

def send_email_with_image(lat, lon, image_bytes, filename="pothole.jpg"):
    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    attachment_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "from": RESEND_FROM,
        "to": [TO_EMAIL],
        "subject": "⚠️ Pothole Detected",
        "text": f"Pothole detected.\n\nLat: {lat}\nLon: {lon}\nGoogle Maps: {maps_link}\n",
        "attachments": [
            {
                "filename": filename,
                "content": attachment_b64
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    r = requests.post(RESEND_URL, json=payload, headers=headers, timeout=15)
    # لو صار خطأ، نخليه يطلع في Logs
    r.raise_for_status()
    return r.json()

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/report")
def report():
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"ok": False, "error": "missing image"}), 400

    lat = request.form.get("lat")
    lon = request.form.get("lon")
    if not lat or not lon:
        return jsonify({"ok": False, "error": "missing lat/lon"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    data = send_email_with_image(lat, lon, image_bytes, filename=image_file.filename or "pothole.jpg")
    return jsonify({"ok": True, "resend": data})
