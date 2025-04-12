from flask import Flask, render_template, request, send_file
from gtts import gTTS
import os
from uuid import uuid4

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    audio_file = None
    if request.method == "POST":
        text = request.form["text"]
        if text.strip():
            tts = gTTS(text)
            filename = f"static/{uuid4().hex}.mp3"
            tts.save(filename)
            audio_file = filename
    return render_template("index.html", audio_file=audio_file)

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"static/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
