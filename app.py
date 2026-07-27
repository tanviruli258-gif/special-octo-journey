import os
import subprocess
import tempfile
import uuid

from flask import Flask, request, render_template, send_file, jsonify

app = Flask(__name__)

# বড় ভিডিও আপলোডের জন্য লিমিট বাড়ানো হলো (ডিফল্ট 1GB)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB

QUALITY_MAP = {
    "sqcif": "128x96",
    "qcif": "176x144",
    "cif": "352x288",
}


def run_ffmpeg(cmd):
    """ffmpeg কমান্ড রান করে, এরর হলে exception ছোঁড়ে"""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,  # ৩০ মিনিট সেফটি টাইমআউট
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="ignore")[-2000:])
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    if "video" not in request.files:
        return jsonify({"error": "কোনো ভিডিও ফাইল পাওয়া যায়নি"}), 400

    video = request.files["video"]
    quality = request.form.get("quality", "qcif")
    size = QUALITY_MAP.get(quality, "176x144")

    if video.filename == "":
        return jsonify({"error": "ফাইলের নাম খালি"}), 400

    job_id = uuid.uuid4().hex
    work_dir = tempfile.mkdtemp(prefix=f"conv_{job_id}_")

    input_ext = os.path.splitext(video.filename)[1] or ".mp4"
    input_path = os.path.join(work_dir, f"input{input_ext}")
    output_path = os.path.join(work_dir, "output.3gp")

    video.save(input_path)

    try:
        # প্রাইমারি: H.263 ভিডিও + AAC অডিও (.3gp কন্টেইনার) — বেশিরভাগ ffmpeg বিল্ডে থাকে, ভালো কম্প্যাটিবিলিটি
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={size}",
            "-c:v", "h263",
            "-b:v", "128k",
            "-r", "15",
            "-c:a", "aac",
            "-ar", "8000",
            "-b:a", "32k",
            "-ac", "1",
            output_path,
        ]
        run_ffmpeg(cmd)
    except Exception as primary_error:
        try:
            # ফলব্যাক: MPEG-4 ভিডিও + AAC অডিও
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vf", f"scale={size}",
                "-c:v", "mpeg4",
                "-b:v", "128k",
                "-r", "15",
                "-c:a", "aac",
                "-ar", "8000",
                "-b:a", "32k",
                "-ac", "1",
                output_path,
            ]
            run_ffmpeg(cmd_fallback)
        except Exception as fallback_error:
            return jsonify({
                "error": "কনভার্সন ব্যর্থ হয়েছে",
                "primary_error": str(primary_error)[-500:],
                "fallback_error": str(fallback_error)[-500:],
            }), 500

    download_name = os.path.splitext(video.filename)[0] + ".3gp"
    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="video/3gpp",
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
