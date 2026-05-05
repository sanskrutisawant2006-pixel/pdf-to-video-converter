
from flask import Flask, render_template, request, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from gtts import gTTS

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
        durations = request.form.get("durations", "")
        narration = request.form.get("narration", "")

        duration_list = [int(x) for x in durations.split(",") if x.strip().isdigit()]
        if not duration_list:
            duration_list = [3] * len(images)

        image_paths = []

        # save images
        for image in images:
            filename = secure_filename(image.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(path)
            image_paths.append(path)

        # create text file for ffmpeg
        list_file = os.path.join(OUTPUT_FOLDER, "images.txt")

        with open(list_file, "w") as f:
            for i, path in enumerate(image_paths):
                duration = duration_list[i] if i < len(duration_list) else 3
                f.write(f"file '{path}'\n")
                f.write(f"duration {duration}\n")

            # last image repeat (important for ffmpeg)
            f.write(f"file '{image_paths[-1]}'\n")

        # 🎤 narration
        audio_path = None
        if narration.strip():
            audio_path = os.path.join(OUTPUT_FOLDER, "tts.mp3")
            tts = gTTS(text=narration, lang="en")
            tts.save(audio_path)

        output_video = os.path.join(OUTPUT_FOLDER, "output.mp4")

        # 🎬 ffmpeg command
        if audio_path:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-i", audio_path,
                "-vsync", "vfr",
                "-pix_fmt", "yuv420p",
                "-shortest",
                output_video
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-vsync", "vfr",
                "-pix_fmt", "yuv420p",
                output_video
            ]

        subprocess.run(cmd, check=True)

        return send_file(output_video, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
