import os, smtplib, ssl
from flask import Flask, request, jsonify
from email.message import EmailMessage

app = Flask(__name__)

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
TO_EMAIL = os.environ["TO_EMAIL"]
API_KEY = os.environ["API_KEY"]  # خلّه مطلوب للحماية

def send_email_with_image(lat, lon, image_bytes, filename="pothole.jpg"):
    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    msg = EmailMessage()
    msg["Subject"] = "⚠️ Pothole Detected"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    msg.set_content(
        f"Pothole detected.\n\n"
        f"Lat: {lat}\nLon: {lon}\n"
        f"Google Maps: {maps_link}\n"
    )

    msg.add_attachment(image_bytes, maintype="image", subtype="jpeg", filename=filename)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/report")
def report():
    # حماية
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

    send_email_with_image(lat, lon, image_bytes, filename=image_file.filename or "pothole.jpg")
    return jsonify({"ok": True})