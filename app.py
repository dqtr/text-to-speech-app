from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
import os
from uuid import uuid4
import time

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    text = data.get("text")
    voice = data.get("voice")

    if not text.strip():
        return jsonify({"error": "Empty text"}), 400

    lang_map = {
        "default": "en",
        "us": "en",
        "uk": "en-uk",
        "india": "en-in",
        "australia": "en-au"
    }

    lang = lang_map.get(voice, "en")
    filename = f"{uuid4().hex}.mp3"
    filepath = f"static/{filename}"

    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"audio_file": filepath})

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"static/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
