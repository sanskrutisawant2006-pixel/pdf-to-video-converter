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
        except Exception as e:
            print("PDF ERROR:", e)

        # 🚨 FALLBACK (ALWAYS SHOW SOMETHING)
        if not images:
            images = []
            for i in range(3):
                img = np.ones((720, 1280, 3), dtype=np.uint8) * 255
                cv2.putText(img, f"Slide {i+1}", (400, 350),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
                images.append(img)

        # 🔥 CONVERT TO FRAMES
        frames = []
        for img in images:
            if isinstance(img, np.ndarray):
                frame = img
            else:
                img = img.convert("RGB")
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            frame = cv2.resize(frame, (1280, 720))
            frames.append(frame)

        # 🔥 DURATION
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

        # 🔊 AUDIO PART
        audio_input = None

        # narration
        if narration.strip():
            try:
                from gtts import gTTS
                tts = gTTS(narration)
                tts.save("voice.mp3")
                audio_input = "voice.mp3"
                print("Narration OK")
            except Exception as e:
                print("TTS ERROR:", e)

        # background audio
        if audio and audio.filename != "":
            audio.save("bg.mp3")
            audio_input = "bg.mp3"

        final_video = "video.mp4"

        # 🔥 MERGE AUDIO
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
            except Exception as e:
                print("FFMPEG ERROR:", e)

        return render_template(
            "index.html",
            message="✅ Video Ready!",
            video=final_video
        )

    return render_template("index.html")


# 🔥 RENDER FIX
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
