from flask import Flask, render_template, request
import numpy as np
import os
import subprocess
import fitz  # PyMuPDF

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        pdf = request.files.get("pdf")
        duration = int(request.form.get("duration", 3))
        custom_input = request.form.get("custom_durations", "")
        narration = request.form.get("narration", "")
        audio = request.files.get("audio")

        if not pdf or pdf.filename == "":
            return render_template("index.html", message="❌ Upload PDF")

        pdf_path = os.path.join(UPLOAD_FOLDER, "input.pdf")
        pdf.save(pdf_path)

        # 🔥 PDF → Images using PyMuPDF
        images = []
        doc = fitz.open(pdf_path)

        for page in doc:
            pix = page.get_pixmap()
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)

            if pix.n == 4:
                img = img[:, :, :3]

            images.append(img)

        if not images:
            return render_template("index.html", message="❌ Failed to read PDF")

        # 🔥 Durations
        custom = []
        if custom_input:
            try:
                custom = [int(x.strip()) for x in custom_input.split(",")]
            except:
                custom = []

        # 🔥 Save frames
        frame_paths = []
        count = 0

        for i, img in enumerate(images):
            dur = custom[i] if i < len(custom) else duration

            for _ in range(dur * 2):  # FPS = 2
                path = os.path.join(UPLOAD_FOLDER, f"frame_{count}.jpg")

                import cv2
                img_resized = cv2.resize(img, (1280, 720))
                cv2.imwrite(path, img_resized)

                frame_paths.append(path)
                count += 1

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

        # 🔊 Audio
        audio_input = None

        # narration
        if narration.strip():
            from gtts import gTTS
            tts = gTTS(narration)
            tts.save("voice.mp3")
            audio_input = "voice.mp3"

        # background audio
        if audio and audio.filename != "":
            audio.save("bg.mp3")
            audio_input = "bg.mp3"

        final_video = "video.mp4"

        if audio_input:
            subprocess.call([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_input,
                "-shortest",
                "-c:v", "copy",
                "-c:a", "aac",
                os.path.join(STATIC_FOLDER, "final.mp4")
            ])
            final_video = "final.mp4"

        return render_template(
            "index.html",
            message="✅ Video Ready!",
            video=final_video
        )

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
