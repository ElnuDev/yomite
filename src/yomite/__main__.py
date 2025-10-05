import pytesseract
import subprocess
import threading
import io
import webbrowser
import os
import traceback
import logging
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
threshold = 150

app = Flask(__name__)

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
    adjusted = image.convert("L").point(fn, mode="1")
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

def grab_thread():
    while True:
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
        threshold=threshold
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
    return text

@app.route("/settings", methods=["POST"])
def post_settings():
    global invert, threshold
    invert = request.form.get("invert") == "on"
    try:
        threshold = max(0, min(int(request.form.get("threshold")), 255))
    except:
        pass
    return ('', 204)

def main():
    start_grab_thread()
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    server = make_server("127.0.0.1", 0, app)
    port = server.socket.getsockname()[1]
    webbrowser.open(f"http://localhost:{port}", new=0)
    server.serve_forever()

if __name__ == "__main__":
    main()