from flask import Flask, request, jsonify, render_template
import os
import threading
from pdf2image import convert_from_path
import cv2

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

    # 🔹 Step 1: PDF → Images (LOW DPI = FAST)
    pages = convert_from_path(pdf_path, dpi=50)
    progress = 30

    image_paths = []
    for i, page in enumerate(pages):
        path = os.path.join(UPLOAD_FOLDER, f"page_{i}.jpg")
        page.save(path, "JPEG")
        image_paths.append(path)

    progress = 60

    # 🔹 Step 2: Create Video using OpenCV (LIGHT 🔥)
    output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")

    first_frame = cv2.imread(image_paths[0])
    height, width, _ = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_path, fourcc, 1/duration, (width, height))

    for img_path in image_paths:
        img = cv2.imread(img_path)
        video.write(img)

    video.release()

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
