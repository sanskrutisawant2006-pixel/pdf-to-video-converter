from flask import Flask, render_template, request, jsonify, send_file
import os
from PIL import Image
import imageio.v2 as imageio
import numpy as np
from gtts import gTTS
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {"value": 0}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global progress
    progress["value"] = 0

    files = request.files.getlist("images")
    narration_text = request.form.get("narration", "")
    
    if not files or len(files) == 0:
        return jsonify({"error": "No images uploaded"}), 400

    image_paths = []

    for file in files:
        path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".png")
        file.save(path)
        image_paths.append(path)

    progress["value"] = 20

    # 🔊 narration
    audio_path = None
    if narration_text.strip():
        tts = gTTS(text=narration_text)
        audio_path = os.path.join(OUTPUT_FOLDER, "audio.mp3")
        tts.save(audio_path)

    progress["value"] = 40

    # 🎥 video creation
    frames = []
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((640, 480))
        frames.append(np.array(img))

    video_path = os.path.join(OUTPUT_FOLDER, "video.mp4")

    imageio.mimsave(video_path, frames, fps=18)

    progress["value"] = 100

    return jsonify({"video": video_path})

@app.route("/progress")
def get_progress():
    return jsonify(progress)

@app.route("/download")
def download():
    return send_file("static/output/video.mp4", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
