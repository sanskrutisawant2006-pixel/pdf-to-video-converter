from flask import Flask, render_template, request
import cv2
import numpy as np
import os
import subprocess

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

        if not pdf:
            return render_template("index.html", message="Upload PDF")

        pdf_path = os.path.join(UPLOAD_FOLDER, "input.pdf")
        pdf.save(pdf_path)

        # 🔥 TRY PDF → images
        images = []
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
        except:
            pass

        # ❗ fallback (VERY IMPORTANT)
        if not images:
            img = np.ones((720, 1280, 3), dtype=np.uint8) * 255
            cv2.putText(img, "PDF CONVERSION NOT SUPPORTED ON SERVER",
                        (100, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            images = [img]

        # 🔥 convert images → frames
        frames = []
        for img in images:
            if hasattr(img, "convert"):
                img = img.convert("RGB")
                img = np.array(img)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            img = cv2.resize(img, (1280, 720))
            frames.append(img)

        # 🔥 durations
        custom = []
        if custom_input:
            try:
                custom = [int(x.strip()) for x in custom_input.split(",")]
            except:
                custom = []

        video_path = os.path.join(STATIC_FOLDER, "video.mp4")

        video = cv2.VideoWriter(
            video_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            18,
            (1280, 720)
        )

        for i, frame in enumerate(frames):
            dur = custom[i] if i < len(custom) else duration

            for _ in range(dur * 18):
                video.write(frame)

        video.release()

        # 🔊 narration
        audio_input = None

        if narration.strip():
            try:
                from gtts import gTTS
                tts = gTTS(narration)
                tts.save("voice.mp3")
                audio_input = "voice.mp3"
            except:
                pass

        # 🎵 background audio
        if audio and audio.filename != "":
            audio.save("bg.mp3")
            audio_input = "bg.mp3"

        final_video = "video.mp4"

        # 🔥 merge audio
        if audio_input:
            try:
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
            except:
                pass

        return render_template(
            "index.html",
            message="✅ Video Ready!",
            video=final_video
        )

    return render_template("index.html")


# 🔥 RENDER FIX (MOST IMPORTANT)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
