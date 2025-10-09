#!/usr/bin/env python

import pytesseract
import subprocess
import threading
import io
import webbrowser
import os
import traceback
import logging
import time
import numpy as np
from PIL import Image, ImageGrab, ImageOps
from flask import Flask, render_template, send_file, make_response, request
from werkzeug.serving import make_server

def get_area():
    global area, bbox
    area = subprocess.check_output(["slurp"]).decode().strip()
    pos_str, dim_str = area.split()
    x_str, y_str = pos_str.split(',')
    x, y = int(x_str), int(y_str)
    w_str, h_str = dim_str.split('x')
    w, h = int(w_str), int(h_str)
    bbox = (x, y, x + w, y + h)

# raw area output from slurp
area = None
# bbox format for PIL.ImageGrab.grab
bbox = None

image = None
adjusted = None
text = ""

# settings
invert = True
threshold = 128
softness = 16

app = Flask(__name__)

def soft_threshold(image, threshold=128, softness=20):
    """
    Soft threshold with feathered edges.
    'softness' controls how wide the transition zone is.
    """
    gray = image.convert("L")
    arr = np.array(gray, dtype=np.float32)

    # Normalize to 0–1
    arr /= 255.0

    # Map to 0–1 with sigmoid-like softness
    t = threshold / 255.0
    s = softness / 255.0
    # Smoothstep function for smooth transition
    if softness == 0:
        # hard threshold (no division by zero)
        feathered = (arr > t).astype(np.float32)
    else:
        feathered = np.clip((arr - (t - s)) / (2 * s), 0, 1)

    # Convert back to 0–255 grayscale
    result = Image.fromarray((feathered * 255).astype(np.uint8))
    return result

def grab():
    global image
    try:
        image = ImageGrab.grab(bbox=bbox)
    except:
        # PIL may fail on Wayland, fall back to grim
        # user must install grim manually
        TEMP = "/tmp/yomite-grab.png"
        try:
            print(["grim", "-g", area, "-l", "0", TEMP])
            subprocess.run(["grim", "-g", area, "-l", "0", TEMP])
            image = Image.open(TEMP)
        except:
            traceback.print_exc()
        finally:
            os.remove(TEMP)

    # https://stackoverflow.com/a/50090612
    fn = lambda x : 255 if x > threshold else 0
    global adjusted
    adjusted = soft_threshold(image, threshold=threshold, softness=softness)
    if invert:
        adjusted = ImageOps.invert(adjusted)

    global text
    # various corrections for inconsistencies in tesseract's output
    text = pytesseract.image_to_string(
        adjusted, lang="jpn"
    ).replace(
        " ", ""
    ).replace(
        "\n\n", "\n"
    ).replace(
        "`", "「"
    )

last_request = time.time()
def grab_thread():
    TIMEOUT = 5
    while True:
        if time.time() - last_request > TIMEOUT:
            print(f"No requests in last {TIMEOUT} seconds, exiting...")
            os._exit(0)
        try:
            grab()
        except:
            traceback.print_exc()
            os._exit(1)

def start_grab_thread():
    get_area()
    thread = threading.Thread(target=grab_thread, daemon=True)
    thread.start()

@app.route("/")
def get_index():
    return render_template(
        "index.html.jinja",
        grab=text,
        invert=invert,
        threshold=threshold,
        softness=softness
    )

def image_response(image):
    if image == None:
        resp = make_response(('', 503))
        resp.headers["Retry-After"] = "1"
        return resp

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    resp = send_file(buf, mimetype="image/png")
    # https://stackoverflow.com/a/22429796
    resp.headers["Cache-Control"] = "max-age=0,must-revalidate"
    return resp

@app.route("/image")
def get_image():
    return image_response(image)

@app.route("/adjusted")
def get_adjusted():
    return image_response(adjusted)

@app.route("/reselect-area")
def get_reselect_area():
    global area
    get_area()
    return ('', 204)

@app.route("/text")
def get_text():
    global last_request
    last_request = time.time()
    return text

@app.route("/settings", methods=["POST"])
def post_settings():
    global invert, threshold, softness
    invert = request.form.get("invert") == "on"
    def process_slider(name):
        return max(0, min(int(request.form.get(name)), 255))
    try:
        threshold = process_slider("threshold")
    except:
        pass
    try:
        softness = process_slider("softness")
    except:
        pass
    return ('', 204)

@app.route("/exit", methods=["POST"])
def post_exit():
    os._exit(1)

def main():
    start_grab_thread()
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    server = make_server("127.0.0.1", 0, app)
    port = server.socket.getsockname()[1]
    url = f"http://localhost:{port}"
    webbrowser.open(url, new=0)
    print(f"Starting server at {url}")
    server.serve_forever()

if __name__ == "__main__":
    main()