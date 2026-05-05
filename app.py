
from flask import Flask, render_template, request, jsonify
import os
import subprocess
import threading
from werkzeug.utils import secure_filename
from gtts import gTTS
import imageio_ffmpeg
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static"   # important: UI reads from /static/

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {"value": 0, "video": ""}


@app.route("/")
def index():
    return render_template("index.html")


# ---------- BACKGROUND WORKER ----------
def process_video(images, narration, uid):
    try:
        progress["value"] = 10

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        # Save images
        image_paths = []
        for i, img in enumerate(images):
            path = os.path.join(UPLOAD_FOLDER, f"{uid}_{i}.jpg")
            img.save(path)
            image_paths.append(path)

        progress["value"] = 30

        # Create concat file
        txt_file = os.path.join(UPLOAD_FOLDER, f"{uid}.txt")
        with open(txt_file, "w") as f:
            for img in image_paths:
                f.write(f"file '{img}'\n")
                f.write("duration 2\n")
            f.write(f"file '{image_paths[-1]}'\n")

        video_path = os.path.join(OUTPUT_FOLDER, f"{uid}.mp4")

        # 🎬 create slideshow (FAST SETTINGS)
        cmd = [
            ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", txt_file,
            "-vf", "scale=640:480",
            "-pix_fmt", "yuv420p",
            video_path
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        progress["value"] = 60

        # 🎤 narration
        audio_path = None
        if narration.strip():
            try:
                audio_path = os.path.join(OUTPUT_FOLDER, f"{uid}.mp3")
                tts = gTTS(text=narration[:150], lang="en")
                tts.save(audio_path)
            except:
                audio_path = None

        # 🎧 merge audio
        if audio_path and os.path.exists(audio_path):
            final_path = os.path.join(OUTPUT_FOLDER, f"{uid}_final.mp4")

            cmd_audio = [
                ffmpeg,
                "-y",
                "-i", video_path,
                "-i", audio_path,
                "-shortest",
                final_path
            ]

            subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            video_path = final_path

        progress["value"] = 100
        progress["video"] = os.path.basename(video_path)

    except Exception as e:
        print("ERROR:", e)
        progress["value"] = 100


# ---------- ROUTES ----------
@app.route("/start", methods=["POST"])
def start():
    images = request.files.getlist("images")
    narration = request.form.get("narration", "")

    if not images:
        return "No images uploaded", 400

    uid = str(uuid.uuid4())

    progress["value"] = 0
    progress["video"] = ""

    # 🚀 run in background (THIS FIXES FREEZE)
    thread = threading.Thread(target=process_video, args=(images, narration, uid))
    thread.start()

    return "started"


@app.route("/progress")
def get_progress():
    return jsonify({
        "progress": progress["value"],
        "video": progress["video"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
