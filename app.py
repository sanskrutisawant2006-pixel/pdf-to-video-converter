from flask import Flask, render_template, request, send_file
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_videoclips
import os
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        pdf = request.files.get("pdf")
        duration = int(request.form.get("duration", 2))

        pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(pdf_path)

        # Convert PDF → images
        images = convert_from_path(pdf_path)

        clips = []
        for img in images:
            img = img.convert("RGB")
            img_array = np.array(img)

            clip = ImageClip(img_array).set_duration(duration)
            clips.append(clip)

        video = concatenate_videoclips(clips)

        output_path = os.path.join(STATIC_FOLDER, "output.mp4")

        video.write_videofile(output_path, fps=24)

        return render_template("index.html", video="output.mp4")

    return render_template("index.html")


@app.route("/download")
def download():
    return send_file("static/output.mp4", as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)