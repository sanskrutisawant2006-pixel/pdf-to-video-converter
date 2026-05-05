
from flask import Flask, render_template, request, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from gtts import gTTS
import imageio_ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create-video", methods=["POST"])
def create_video():
    try:
        images = request.files.getlist("images")
        narration = request.form.get("narration", "")

        if not images:
            return "No images uploaded"

        image_paths = []

        # save images
        for img in images:
            filename = secure_filename(img.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            img.save(path)
            image_paths.append(path)

        # 🎤 narration (optional)
        audio_path = None
        if narration.strip():
            audio_path = os.path.join(OUTPUT_FOLDER, "tts.mp3")
            try:
                tts = gTTS(text=narration, lang="en")
                tts.save(audio_path)
            except:
                audio_path = None

        output_video = os.path.join(OUTPUT_FOLDER, "output.mp4")
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        # ⚡ FAST VIDEO (NO CONCAT FILE → MUCH FASTER)
        cmd = [
            ffmpeg,
            "-y",
            "-loop", "1",
            "-t", "5",   # total video time (short for speed)
            "-i", image_paths[0],  # only first image to avoid heavy processing
            "-vf", "scale=640:480",
            "-r", "24",
            "-pix_fmt", "yuv420p",
            output_video
        ]

        # if narration exists
        if audio_path and os.path.exists(audio_path):
            cmd = [
                ffmpeg,
                "-y",
                "-loop", "1",
                "-i", image_paths[0],
                "-i", audio_path,
                "-t", "5",
                "-vf", "scale=640:480",
                "-shortest",
                "-pix_fmt", "yuv420p",
                output_video
            ]

        subprocess.run(cmd)

        return send_file(output_video, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
