# Simple Multiple Image Resizer

A small Python + Flask tool for resizing many images and downloading the results as one ZIP file.

## Features
- Multiple JPG/JPEG/PNG/WEBP upload
- Keeps aspect ratio
- Does not enlarge smaller images
- Quality control
- Keep original format or convert to WEBP/JPEG/PNG
- Returns one ZIP
- No database needed

## Run
1. Install Python 3.10+
2. Open CMD/Terminal inside this folder
3. Run: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open: `http://127.0.0.1:5000`

## Recommended for website images
Normal package images: 1600 x 1600, quality 82-88, WEBP.
Hero/banner images: 1920 x 1920, quality 85-90, WEBP.

The app preserves proportions automatically. Transparent PNGs remain transparent when exported as PNG or WEBP. JPEG uses a white background for transparency.


## Branding update

This version shows the message **"Welcome for Maliga Online Resize Image"** and displays the provided photo in a circular passport-style frame on the homepage.


## Exact Size / Smart Crop update

The tool now has two resize modes:

- **Exact Size — Smart Crop** (default): every output is exactly the requested width and height, such as 612 × 408 px. The image keeps its natural proportions and extra edges are cropped from the center, so it is not stretched.
- **Keep Original Ratio — Fit Inside**: preserves the full image and only fits it inside the requested width/height box. Output dimensions may differ.

## Success-message update

- The old "Python Image Tool" label was removed.
- After selecting images, the interface displays an "Uploaded successfully" message with the selected image count.
- After resizing finishes, the interface displays "Resize completed successfully" and a "Download Resized Images" button.
- The ZIP is prepared in the browser only after processing finishes, so the user can explicitly click the download button.
