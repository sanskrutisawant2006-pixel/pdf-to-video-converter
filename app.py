from flask import Flask, request, jsonify, render_template
import os
import threading
from pdf2image import convert_from_path
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

    # Step 1: Convert PDF → images (LOW QUALITY = FAST)
    pages = convert_from_path(pdf_path, dpi=60)
    progress = 30

    image_paths = []
    for i, page in enumerate(pages):
        path = os.path.join(UPLOAD_FOLDER, f"page_{i}.jpg")
        page.save(path, "JPEG")
        image_paths.append(path)

    progress = 60

    # Step 2: Create video using imageio (LIGHT 🔥)
    output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")

    with imageio.get_writer(output_path, fps=1/duration) as writer:
        for img_path in image_paths:
            image = imageio.imread(img_path)
            writer.append_data(image)

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
