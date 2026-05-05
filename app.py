from flask import Flask, render_template, request, send_file, jsonify
import os
import uuid
import threading
from gtts import gTTS
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

progress = {"value": 0, "video": ""}


def create_video(images, audio_path, output_path):
    frame_array = []
    size = None

    for img_file in images:
        img = Image.open(img_file)
        img = img.convert("RGB")
        img = np.array(img)

        if size is None:
            size = (img.shape[1], img.shape[0])

        frame_array.append(img)

    out = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        1,  # fps
        size
    )

    for frame in frame_array:
        out.write(frame)

    out.release()


def process_video(images, narration, uid):
    try:
        progress["value"] = 10

        # Save images temporarily
        saved_images = []
        for img in images:
            path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpg")
            img.save(path)
            saved_images.append(path)

        progress["value"] = 40

        # Generate narration
        audio_path = ""
        if narration.strip() != "":
            audio_path = os.path.join(UPLOAD_FOLDER, f"{uid}.mp3")
            tts = gTTS(narration)
            tts.save(audio_path)

        progress["value"] = 70

        # Create video
        video_path = os.path.join(UPLOAD_FOLDER, f"{uid}.mp4")
        create_video(saved_images, audio_path, video_path)

        progress["value"] = 100
        progress["video"] = video_path

    except Exception as e:
        print("ERROR:", e)
        progress["value"] = 0


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    images = request.files.getlist("file")  # 🔥 IMPORTANT FIX
    narration = request.form.get("narration", "")

    print("FILES:", images)

    if not images or images[0].filename == "":
        return "No images uploaded", 400

    uid = str(uuid.uuid4())

    progress["value"] = 0
    progress["video"] = ""

    thread = threading.Thread(target=process_video, args=(images, narration, uid))
    thread.start()

    return "started"


@app.route("/progress")
def get_progress():
    return jsonify(progress)


@app.route("/download")
def download():
    video = progress.get("video")
    if video and os.path.exists(video):
        return send_file(video, as_attachment=True)
    return "No video", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
