from flask import Flask, render_template, request, jsonify
import numpy as np
import os
import subprocess
import fitz

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

progress = {"value": 0}


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress
    progress["value"] = 0

    pdf = request.files.get("pdf")
    duration = int(request.form.get("duration", 3))
    custom_input = request.form.get("custom_durations", "")
    narration = request.form.get("narration", "")
    audio = request.files.get("audio")

    if not pdf:
        return "No file", 400

    pdf_path = os.path.join(UPLOAD_FOLDER, "input.pdf")
    pdf.save(pdf_path)

    # 🔥 PDF → Images
    images = []
    doc = fitz.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap()
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)

        if pix.n == 4:
            img = img[:, :, :3]

        images.append(img)

    progress["value"] = 20

    # durations
    custom = []
    if custom_input:
        try:
            custom = [int(x.strip()) for x in custom_input.split(",")]
        except:
            custom = []

    # 🔥 Save frames
    count = 0

    for i, img in enumerate(images):
        dur = custom[i] if i < len(custom) else duration

        for _ in range(dur * 2):
            path = os.path.join(UPLOAD_FOLDER, f"frame_{count}.jpg")

            import cv2
            img_resized = cv2.resize(img, (1280, 720))
            cv2.imwrite(path, img_resized)

            count += 1

    progress["value"] = 50

    # 🔥 Create video
    video_path = os.path.join(STATIC_FOLDER, "video.mp4")

    subprocess.call([
        "ffmpeg", "-y",
        "-framerate", "2",
        "-i", os.path.join(UPLOAD_FOLDER, "frame_%d.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        video_path
    ])

    progress["value"] = 70

    # 🔊 AUDIO
    audio_files = []

    if narration.strip():
        from gtts import gTTS
        tts = gTTS(narration)
        tts.save("voice.mp3")
        audio_files.append("voice.mp3")

    if audio and audio.filename != "":
        audio.save("bg.mp3")
        audio_files.append("bg.mp3")

    final_video = "video.mp4"

    if audio_files:
        if len(audio_files) == 1:
            subprocess.call([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_files[0],
                "-shortest",
                "-c:v", "copy",
                "-c:a", "aac",
                os.path.join(STATIC_FOLDER, "final.mp4")
            ])
        else:
            subprocess.call([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_files[0],
                "-i", audio_files[1],
                "-filter_complex",
                "[1:a]volume=1[a1];[2:a]volume=0.3[a2];[a1][a2]amix=inputs=2",
                "-c:v", "copy",
                "-c:a", "aac",
                os.path.join(STATIC_FOLDER, "final.mp4")
            ])

        final_video = "final.mp4"

    progress["value"] = 100

    return jsonify({"video": final_video})


@app.route("/progress")
def get_progress():
    return jsonify(progress)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
