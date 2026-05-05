from flask import Flask, request, jsonify, render_template
import os
import threading
from pdf2image import convert_from_path
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = 0
video_name = ""

@app.route("/")
def home():
    return render_template("index.html")

def process_video(pdf_path, duration):
    global progress, video_name

    # Step 1: PDF → images
    pages = convert_from_path(pdf_path, dpi=70)
    progress = 30

    image_paths = []
    for i, page in enumerate(pages):
        path = os.path.join(UPLOAD_FOLDER, f"page_{i}.jpg")
        page.save(path, "JPEG")
        image_paths.append(path)

    progress = 60

    # Step 2: Create video
    clip = ImageSequenceClip(image_paths, fps=1/duration)

    output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")
    clip.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        preset="ultrafast"
    )

    progress = 100
    video_name = "output.mp4"

@app.route("/start", methods=["POST"])
def start():
    global progress
    progress = 0

    pdf = request.files["pdf"]
    duration = int(request.form.get("duration", 3))

    pdf_path = os.path.join(UPLOAD_FOLDER, "input.pdf")
    pdf.save(pdf_path)

    # 🔥 Run in background thread
    thread = threading.Thread(target=process_video, args=(pdf_path, duration))
    thread.start()

    return "started"

@app.route("/progress")
def get_progress():
    return jsonify({
        "progress": progress,
        "video": video_name
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
