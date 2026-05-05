from flask import Flask, render_template, request, jsonify, send_file
import os
import cv2
from pdf2image import convert_from_path
from gtts import gTTS
import subprocess

app = Flask(__name__)

progress = {"value": 0}
OUTPUT_VIDEO = "output.mp4"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress
    progress["value"] = 0

    file = request.files.get("file")
    narration = request.form.get("narration", "")
    durations = request.form.get("durations", "")
    default_duration = int(request.form.get("default_duration", 3))
    bg_audio = request.files.get("audio")

    if not file:
        return "No file uploaded", 400

    # save PDF
    pdf_path = "input.pdf"
    file.save(pdf_path)

    # 🔥 Step 1: PDF → images
    images = convert_from_path(pdf_path)
    progress["value"] = 20

    image_paths = []
    for i, img in enumerate(images):
        path = f"page_{i}.jpg"
        img.save(path, "JPEG")
        image_paths.append(path)

    progress["value"] = 40

    # 🔥 Step 2: Create video
    frame = cv2.imread(image_paths[0])
    height, width, _ = frame.shape

    temp_video = "video.mp4"

    video = cv2.VideoWriter(
        temp_video,
        cv2.VideoWriter_fourcc(*'mp4v'),
        18,
        (width, height)
    )

    custom = list(map(int, durations.split(","))) if durations else []

    for i, img_path in enumerate(image_paths):
        frame = cv2.imread(img_path)

        dur = custom[i] if i < len(custom) else default_duration
        frames = dur * 18

        for _ in range(frames):
            video.write(frame)

    video.release()
    progress["value"] = 70

    # 🔥 Step 3: Audio (gTTS + background)
    audio_files = []

    if narration.strip():
        tts = gTTS(narration)
        tts.save("tts.mp3")
        audio_files.append("tts.mp3")

    if bg_audio:
        bg_audio.save("bg.mp3")
        audio_files.append("bg.mp3")

    final_audio = None

    if len(audio_files) == 1:
        final_audio = audio_files[0]

    elif len(audio_files) == 2:
        final_audio = "merged_audio.mp3"

        subprocess.call([
            "ffmpeg", "-y",
            "-i", audio_files[0],
            "-i", audio_files[1],
            "-filter_complex", "amix=inputs=2:duration=longest",
            final_audio
        ])

    progress["value"] = 85

    # 🔥 Step 4: Merge video + audio
    final_video = OUTPUT_VIDEO

    if final_audio:
        subprocess.call([
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", final_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            final_video
        ])
    else:
        final_video = temp_video

    progress["value"] = 100

    return "done"


@app.route("/progress")
def get_progress():
    return jsonify({"progress": progress["value"]})


@app.route("/download")
def download():
    return send_file(OUTPUT_VIDEO, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
