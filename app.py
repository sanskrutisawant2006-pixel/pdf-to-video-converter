import os
import uuid
from flask import Flask, render_template, request, jsonify
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_videoclips

# Fix FFmpeg (Render)
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {"value": 0, "video": ""}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress
    progress = {"value": 0, "video": ""}

    file = request.files.get("pdf")
    if not file:
        return "No file", 400

    duration = int(request.form.get("duration", 3))

    # Save PDF
    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)

    # Convert PDF → Images
    images = convert_from_path(pdf_path, poppler_path="/usr/bin")

    image_paths = []
    total = len(images)

    for i, img in enumerate(images):
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.jpg")
        img.save(path, "JPEG")
        image_paths.append(path)

        progress["value"] = int((i + 1) / total * 40)

    # Create video
    clips = []
    for i, path in enumerate(image_paths):
        clip = ImageClip(path).set_duration(duration)
        clips.append(clip)

        progress["value"] = 40 + int((i + 1) / total * 40)

    video = concatenate_videoclips(clips, method="compose")

    output_name = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)

    video.write_videofile(output_path, fps=24)

    progress["value"] = 100
    progress["video"] = output_name

    return "done"


@app.route("/progress")
def get_progress():
    global progress
    return jsonify({
        "progress": progress.get("value", 0),
        "video": progress.get("video", "")
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
