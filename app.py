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
    narration = request.form.get("narration", "")

    if not files or files[0].filename == "":
        return "No images", 400

    image_paths = []

    # save images
    for file in files:
        filename = str(uuid.uuid4()) + ".png"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    progress["value"] = 30

    # narration audio
    if narration.strip():
        tts = gTTS(text=narration)
        tts.save(os.path.join(OUTPUT_FOLDER, "audio.mp3"))

    progress["value"] = 60

    # video creation
    frames = []

    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((640, 480))
        frame = np.array(img)

        # show each image ~2 sec (18 fps * 2)
        for _ in range(36):
            frames.append(frame)

    video_path = os.path.join(OUTPUT_FOLDER, "video.mp4")

    imageio.mimsave(video_path, frames, fps=18)

    progress["value"] = 100

    return jsonify({"status": "done"})


@app.route("/progress")
def progress_route():
    return jsonify(progress)


@app.route("/download")
def download():
    return send_file("static/output/video.mp4", as_attachment=True)


# 🔴 CRITICAL FIX FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port))
