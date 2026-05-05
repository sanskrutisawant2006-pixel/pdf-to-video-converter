from flask import Flask, render_template, request, jsonify, send_file
import cv2
import subprocess
import os

app = Flask(__name__)

progress = {"value": 0}
VIDEO_FILE = "video.mp4"
FINAL_VIDEO = "final.mp4"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global progress
    progress["value"] = 0

    files = request.files.getlist("file")
    narration = request.form.get("narration", "")
    durations = request.form.get("durations", "")
    default_duration = int(request.form.get("default_duration", 3))
    bg_audio = request.files.get("audio")

    if not files or files[0].filename == "":
        return "No images uploaded", 400

    image_paths = []

    for i, file in enumerate(files):
        path = f"img_{i}.jpg"
        file.save(path)
        image_paths.append(path)

    progress["value"] = 30

    frame = cv2.imread(image_paths[0])
    height, width, _ = frame.shape

    video = cv2.VideoWriter(
        VIDEO_FILE,
        cv2.VideoWriter_fourcc(*'mp4v'),
        18,
        (width, height)
    )

    # safe custom durations
    custom = []
    if durations:
        try:
            custom = [int(x.strip()) for x in durations.split(",")]
        except:
            custom = []

    for i, path in enumerate(image_paths):
        frame = cv2.imread(path)

        if i < len(custom) and custom[i] > 0:
            dur = custom[i]
        else:
            dur = default_duration

        for _ in range(dur * 18):
            video.write(frame)

    video.release()
    progress["value"] = 70

    # 🎵 background audio
    final_video = VIDEO_FILE

    if bg_audio and bg_audio.filename != "":
        bg_audio.save("bg.mp3")

        subprocess.call([
            "ffmpeg", "-y",
            "-i", VIDEO_FILE,
            "-i", "bg.mp3",
            "-shortest",
            "-c:v", "copy",
            "-c:a", "aac",
            FINAL_VIDEO
        ])

        final_video = FINAL_VIDEO

    progress["value"] = 100

    return jsonify({"video": final_video})


@app.route("/progress")
def progress_api():
    return jsonify(progress)


@app.route("/download")
def download():
    return send_file(FINAL_VIDEO if os.path.exists(FINAL_VIDEO) else VIDEO_FILE, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
