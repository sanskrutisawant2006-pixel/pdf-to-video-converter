from flask import Flask, render_template, request, jsonify, send_file
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


def create_video(images, output_path):
    try:
        first_img = Image.open(images[0]).convert("RGB")
        size = first_img.size  # (width, height)

        fps = 18
        seconds_per_image = 2
        frames_per_image = fps * seconds_per_image

        out = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            size
        )

        for img_path in images:
            img = Image.open(img_path).convert("RGB")
            img = img.resize(size)
            frame = np.array(img)

            for _ in range(frames_per_image):
                out.write(frame)

        out.release()
        print("✅ Video created")

    except Exception as e:
        print("❌ Video error:", e)


def process_video(images, narration, uid):
    try:
        progress["value"] = 10

        saved_images = []
        for img in images:
            path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpg")
            img.save(path)
            saved_images.append(path)

        progress["value"] = 40

        # 🔊 Narration (gTTS)
        if narration.strip():
            audio_path = os.path.join(UPLOAD_FOLDER, f"{uid}.mp3")
            tts = gTTS(narration)
            tts.save(audio_path)
            print("✅ Audio generated")

        progress["value"] = 70

        # 🎬 Video
        video_path = os.path.join(UPLOAD_FOLDER, f"{uid}.mp4")
        create_video(saved_images, video_path)

        if os.path.exists(video_path):
            progress["value"] = 100
            progress["video"] = video_path
        else:
            progress["value"] = 0

    except Exception as e:
        print("❌ Processing error:", e)
        progress["value"] = 0


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    images = request.files.getlist("file")  # 🔥 MUST MATCH HTML
    narration = request.form.get("narration", "")

    if not images or images[0].filename == "":
        return "No images", 400

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
    app.run(host="0.0.0.0", port=10000).0.0.0", port=10000)
