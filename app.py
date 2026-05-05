from flask import Flask, render_template, request, jsonify, send_file
import os
import cv2
from pdf2image import convert_from_path
from gtts import gTTS

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

    if not file:
        return "No file uploaded", 400

    # Save PDF
    pdf_path = "input.pdf"
    file.save(pdf_path)

    # Convert PDF → images
    try:
        images = convert_from_path(pdf_path)
    except:
        return "PDF conversion failed (poppler missing)", 500

    if len(images) == 0:
        return "Empty PDF", 500

    progress["value"] = 25

    image_paths = []
    for i, img in enumerate(images):
        path = f"page_{i}.jpg"
        img.save(path, "JPEG")
        image_paths.append(path)

    progress["value"] = 50

    # Video setup
    frame = cv2.imread(image_paths[0])
    height, width, _ = frame.shape

    video = cv2.VideoWriter(
        OUTPUT_VIDEO,
        cv2.VideoWriter_fourcc(*'mp4v'),
        18,
        (width, height)
    )

    # SAFE custom durations
    custom = []
    if durations:
        try:
            custom = [int(x.strip()) for x in durations.split(",")]
        except:
            custom = []

    # Create video frames
    for i, img_path in enumerate(image_paths):
        frame = cv2.imread(img_path)

        if i < len(custom) and custom[i] > 0:
            dur = custom[i]
        else:
            dur = default_duration

        frames = dur * 18

        for _ in range(frames):
            video.write(frame)

    video.release()
    progress["value"] = 80

    # Narration (optional)
    if narration.strip():
        try:
            tts = gTTS(narration)
            tts.save("audio.mp3")
        except:
            pass

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
