from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image, ImageOps
from io import BytesIO
from pathlib import Path
import zipfile
import re

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024  # 250 MB total upload

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def safe_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return name or "image"


def output_extension(fmt: str, original_name: str) -> str:
    if fmt == "original":
        ext = Path(original_name).suffix.lower()
        return ".jpg" if ext == ".jpeg" else ext
    return {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}.get(fmt, ".jpg")


def resize_image(file_storage, width, height, quality, output_format, resize_mode):
    original_name = file_storage.filename or "image.jpg"
    original_ext = Path(original_name).suffix.lower()
    if original_ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    img = Image.open(file_storage.stream)
    img = ImageOps.exif_transpose(img)
    original_format = img.format

    if resize_mode == "exact":
        # Exact Size + Smart Crop: every output image is exactly width x height.
        # ImageOps.fit preserves proportions, enlarges if needed, then crops evenly from the center.
        img = ImageOps.fit(
            img,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    else:
        # Keep Ratio: fit inside the requested box without cropping or enlarging small images.
        source_width, source_height = img.size
        scale = min(width / source_width, height / source_height, 1.0)
        if scale < 1.0:
            new_size = (
                max(1, round(source_width * scale)),
                max(1, round(source_height * scale)),
            )
            img = img.resize(new_size, Image.Resampling.LANCZOS)

    if output_format == "original":
        fmt = (original_format or original_ext.replace(".", "")).upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if fmt not in {"JPEG", "PNG", "WEBP"}:
            fmt = "JPEG"
    else:
        fmt = output_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"

    out = BytesIO()

    if fmt == "JPEG":
        if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(rgba, mask=rgba.getchannel("A"))
            img = bg
        else:
            img = img.convert("RGB")
        img.save(out, "JPEG", quality=quality, optimize=True, progressive=True)

    elif fmt == "PNG":
        if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
            img = img.convert("RGBA")
        img.save(out, "PNG", optimize=True)

    elif fmt == "WEBP":
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img.save(out, "WEBP", quality=quality, method=6)

    out.seek(0)
    return out


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("images")
        if not files or not any(f.filename for f in files):
            flash("Choose at least one image.")
            return redirect(url_for("index"))

        try:
            width = max(1, min(int(request.form.get("width", 612)), 10000))
            height = max(1, min(int(request.form.get("height", 408)), 10000))
            quality = max(40, min(int(request.form.get("quality", 85)), 100))
        except ValueError:
            flash("Width, height and quality must be numbers.")
            return redirect(url_for("index"))

        resize_mode = request.form.get("resize_mode", "exact")
        if resize_mode not in {"exact", "fit"}:
            resize_mode = "exact"

        output_format = request.form.get("output_format", "original")
        if output_format not in {"original", "jpeg", "png", "webp"}:
            output_format = "original"

        zip_buffer = BytesIO()
        successful = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                if not file.filename:
                    continue
                try:
                    resized = resize_image(file, width, height, quality, output_format, resize_mode)
                    ext = output_extension(output_format, file.filename)
                    out_name = f"{safe_name(file.filename)}-resized{ext}"
                    zf.writestr(out_name, resized.getvalue())
                    successful += 1
                except Exception:
                    continue

        if successful == 0:
            flash("No valid images were processed. Use JPG, JPEG, PNG or WEBP.")
            return redirect(url_for("index"))

        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="resized-images.zip")

    return render_template("index.html")


@app.errorhandler(413)
def too_large(_):
    flash("Upload is too large. Maximum total upload size is 250 MB.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
