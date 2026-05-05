from flask import Flask, render_template, request, jsonify, send_file
import cv2
import os
import numpy as np

app = Flask(__name__)

progress = {"value": 0}
VIDEO_FILE = "video.mp4"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress
    progress["value"] = 0

    file = request.files.get("file")
    durations = request.form.get("durations", "")
    default_duration = int(request.form.get("default_duration", 3))
    bg_audio = request.files.get("audio")

    if not file:
        return "No file uploaded", 400

    pdf_path = "input.pdf"
    file.save(pdf_path)

    progress["value"] = 20

    # 🔥 TRY converting PDF → images
    images = []

    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)
    except:
        pass

    # ❗ fallback if conversion fails
    if not images:
        img = np.ones((720, 1280, 3), dtype=np.uint8) * 255
        cv2.putText(img, "PDF PROCESS FAILED", (200, 350),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        images = [img]

    progress["value"] = 40

    # convert to cv2 frames
    frames_list = []
    for img in images:
        if hasattr(img, "convert"):
            img = img.convert("RGB")
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        frames_list.append(img)

    height, width, _ = frames_list[0].shape

    video = cv2.VideoWriter(
        VIDEO_FILE,
        cv2.VideoWriter_fourcc(*'mp4v'),
        18,
        (width, height)
    )

    progress["value"] = 60

    # durations
    custom = []
    if durations:
        try:
            custom = [int(x.strip()) for x in durations.split(",")]
        except:
            custom = []

    for i, frame in enumerate(frames_list):
        dur = custom[i] if i < len(custom) else default_duration

        for _ in range(dur * 18):
            video.write(frame)

    video.release()

    progress["value"] = 90

    # 🎵 audio (optional)
    if bg_audio and bg_audio.filename != "":
        bg_audio.save("bg.mp3")

        import subprocess
        try:
            subprocess.call([
                "ffmpeg", "-y",
                "-i", VIDEO_FILE,
                "-i", "bg.mp3",
                "-shortest",
                "-c:v", "copy",
                "-c:a", "aac",
                "final.mp4"
            ])
            VIDEO = "final.mp4"
        except:
            VIDEO = VIDEO_FILE
    else:
        VIDEO = VIDEO_FILE

    progress["value"] = 100

    return jsonify({"video": VIDEO})


@app.route("/progress")
def progress_api():
    return jsonify(progress)


@app.route("/download")
def download():
    if os.path.exists("final.mp4"):
        return send_file("final.mp4", as_attachment=True)
    return send_file(VIDEO_FILE, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
