
from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create-video", methods=["POST"])
def create_video():
    try:
        images = request.files.getlist("images")
        durations = request.form.get("durations", "")
        narration = request.form.get("narration", "")
        audio = request.files.get("audio")

        # durations
        duration_list = [int(x) for x in durations.split(",") if x.strip().isdigit()]
        if not duration_list:
            duration_list = [3] * len(images)

        clips = []
        total_duration = 0

        # create image clips
        for i, image in enumerate(images):
            filename = secure_filename(image.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(path)

            duration = duration_list[i] if i < len(duration_list) else 3
            total_duration += duration

            clip = ImageClip(path).set_duration(duration)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        audio_path = None

        # 🎤 narration (gTTS)
        if narration.strip():
            try:
                audio_path = os.path.join(OUTPUT_FOLDER, "tts.mp3")
                tts = gTTS(text=narration, lang="en")
                tts.save(audio_path)
            except Exception as e:
                print("gTTS failed:", e)

        # 🎵 fallback audio
        if not audio_path and audio and audio.filename != "":
            audio_path = os.path.join(UPLOAD_FOLDER, secure_filename(audio.filename))
            audio.save(audio_path)

        # attach audio safely
        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)

            # 🔥 IMPORTANT FIX: match durations
            if audio_clip.duration < total_duration:
                audio_clip = audio_clip.set_duration(total_duration)
            else:
                audio_clip = audio_clip.subclip(0, total_duration)

            video = video.set_audio(audio_clip)

        output_path = os.path.join(OUTPUT_FOLDER, "output.mp4")

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
