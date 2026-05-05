
from flask import Flask, render_template, request, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from gtts import gTTS
import imageio_ffmpeg
import uuid

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
            return "No image uploaded"

        unique_id = str(uuid.uuid4())

        image_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.jpg")
        audio_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}.mp3")
        output_video = os.path.join(OUTPUT_FOLDER, f"{unique_id}.mp4")

        # save FIRST image only (keeps UI same but avoids heavy load)
        images[0].save(image_path)

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        # 🎤 SAFE gTTS (THIS WAS YOUR MAIN ISSUE)
        if narration.strip():
            try:
                tts = gTTS(text=narration[:150], lang="en")
                tts.save(audio_path)
            except:
                audio_path = None
        else:
            audio_path = None

        # 🎬 CREATE VIDEO (VERY IMPORTANT FIXES HERE)
        if audio_path and os.path.exists(audio_path):
            cmd = [
                ffmpeg,
                "-y",
                "-loop", "1",
                "-i", image_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-t", "5",
                "-pix_fmt", "yuv420p",
                "-shortest",
                output_video
            ]
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-loop", "1",
                "-i", image_path,
                "-c:v", "libx264",
                "-t", "5",
                "-pix_fmt", "yuv420p",
                output_video
            ]

        # 🔥 CRITICAL: prevents hanging
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)

        # check if file actually created
        if not os.path.exists(output_video):
            return "Video generation failed 😭"

        return send_file(output_video, as_attachment=True)

    except subprocess.TimeoutExpired:
        return "Server too slow (Render free limit 😭)"

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
