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

    # 🔴 match your UI
    files = request.files.getlist("file")
    narration = request.form.get("narration", "")
    durations_input = request.form.get("durations", "")

    if not files or files[0].filename == "":
        return "No images", 400

    image_paths = []

    # save images
    for file in files:
        filename = str(uuid.uuid4()) + ".jpg"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    progress["value"] = 20

    # 🔊 narration
    if narration.strip():
        tts = gTTS(text=narration)
        tts.save(os.path.join(OUTPUT_FOLDER, "audio.mp3"))

    progress["value"] = 40

    # 🎯 parse durations
    durations = []
    if durations_input:
        try:
            durations = [int(x.strip()) for x in durations_input.split(",")]
        except:
            durations = []

    # 🎥 create frames
    fps = 18
    frames = []

    for i, path in enumerate(image_paths):
        img = Image.open(path).convert("RGB")
        img = img.resize((640, 480))
        frame = np.array(img)

        # duration per image
        if i < len(durations):
            seconds = durations[i]
        else:
            seconds = 3  # default

        frame_count = seconds * fps

        for _ in range(frame_count):
            frames.append(frame)

    progress["value"] = 70

    video_path = os.path.join(OUTPUT_FOLDER, "video.mp4")
    imageio.mimsave(video_path, frames, fps=fps)

    progress["value"] = 100

    return "done"


@app.route("/progress")
def get_progress():
    return jsonify(progress)


@app.route("/download")
def download():
    return send_file("static/output/video.mp4", as_attachment=True)


# ✅ RENDER FIX (VERY IMPORTANT)
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
