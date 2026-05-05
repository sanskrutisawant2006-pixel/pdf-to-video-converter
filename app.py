
from flask import Flask, render_template, request, jsonify
import os
import threading
from pdf2image import convert_from_bytes
from PIL import Image
import imageio
import uuid

# OPTIONAL TTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except:
    GTTS_AVAILABLE = False

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {"value": 0}
video_name = ""

# =========================
# SAFE TTS FUNCTION
# =========================
def generate_audio_safe(text, path):
    if not GTTS_AVAILABLE:
        return False
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(path)
        return True
    except Exception as e:
        print("TTS failed:", e)
        return False

# =========================
# MAIN PROCESS
# =========================
def process_video(file_bytes, duration, narration_text):
    global progress, video_name

    try:
        progress["value"] = 10

        images = convert_from_bytes(file_bytes)
        progress["value"] = 30

        frames = []
        for img in images:
            img = img.resize((720, 480))
            frames.append(img)

        progress["value"] = 50

        temp_video = os.path.join(OUTPUT_FOLDER, "temp.mp4")

        writer = imageio.get_writer(temp_video, fps=1)

        for frame in frames:
            for _ in range(duration):
                writer.append_data(imageio.core.util.Array(frame))

        writer.close()

        progress["value"] = 70

        # =========================
        # ADD AUDIO (OPTIONAL)
        # =========================
        final_video = "output_" + str(uuid.uuid4()) + ".mp4"
        final_path = os.path.join(OUTPUT_FOLDER, final_video)

        audio_path = os.path.join(UPLOAD_FOLDER, "voice.mp3")

        use_audio = False
        if narration_text.strip() != "":
            use_audio = generate_audio_safe(narration_text, audio_path)

        if use_audio:
            try:
                import subprocess

                subprocess.run([
                    "ffmpeg",
                    "-y",
                    "-i", temp_video,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    final_path
                ])
            except Exception as e:
                print("FFmpeg failed:", e)
                final_path = temp_video
                final_video = "temp.mp4"
        else:
            final_path = temp_video
            final_video = "temp.mp4"

        progress["value"] = 100
        video_name = final_video

    except Exception as e:
        print("ERROR:", e)
        progress["value"] = 100


# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress

    file = request.files["pdf"]
    duration = int(request.form.get("duration", 3))
    narration = request.form.get("narration", "")

    file_bytes = file.read()

    progress["value"] = 0

    threading.Thread(
        target=process_video,
        args=(file_bytes, duration, narration)
    ).start()

    return jsonify({"status": "started"})


@app.route("/progress")
def get_progress():
    return jsonify({
        "progress": progress["value"],
        "video": video_name
    })


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
