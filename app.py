
from flask import Flask, request, jsonify, render_template
import os
import threading
import fitz  # PyMuPDF
import imageio.v2 as imageio

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

    # 🔹 Step 1: PDF → images
    doc = fitz.open(pdf_path)
    image_paths = []

    for i, page in enumerate(doc):
        pix = page.get_pixmap()
        path = os.path.join(UPLOAD_FOLDER, f"page_{i}.png")
        pix.save(path)
        image_paths.append(path)

    progress = 60

    # 🔹 Step 2: Create video (FFMPEG via imageio)
    output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")

    writer = imageio.get_writer(
        output_path,
        fps=1,
        codec='libx264',
        format='FFMPEG'
    )

    for img_path in image_paths:
        image = imageio.imread(img_path)

        # repeat frames for duration
        for _ in range(duration):
            writer.append_data(image)

    writer.close()

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
