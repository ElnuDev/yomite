import subprocess
from collections import OrderedDict

import utils

is_hypr = True
try:
    subprocess.run(["hyprctl", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    is_hypr = False

class Window:
    id = None
    bbox = None
    details = None

    def __init__(self, id):
        self.id = id
        self.details = {}

    def __repr__(self):
        return f"{{ id: {self.id}, bbox: {self.bbox}, floating: {self.details.get("floating")}, fullscreen: {self.details.get("fullscreen")}, ... }}"

# Get window list, sorted by fullscreen then floating
def get_windows():
    windows = {}
    window = None
    for line in subprocess.check_output(["hyprctl", "clients"]).decode().splitlines():
        if line.startswith("Window "):
            window = line.split(" ")[1]
            windows[window] = Window(window)
            continue
        if not line.startswith("\t"):
            continue
        windows[window].details[line.split("\t")[1].split(":")[0]] = line.split(": ")[1]
        if line.startswith("\tat:"):
            at = True
        elif line.startswith("\tsize:"):
            at = False
        else:
            continue
        a_str, b_str = line.split(" ")[1].split(",")
        a, b = int(a_str), int(b_str)
        if at:
            x, y = a, b
            windows[window].bbox = (x, y)
        else:
            x, y = windows[window].bbox
            w, h = a, b
            windows[window].bbox = (x, y, x + w, y + h)
    def sort(window):
        fullscreen = window.details.get("fullscreen")
        floating = window.details.get("floating")
        return (
            -int(fullscreen) if fullscreen else 0,
            -int(floating) if floating else 0,
        )
    windows = OrderedDict(sorted(windows.items(), key=lambda x: sort(x[1])))
    return windows

def get_window_of_bbox(bbox):
    current_workspace = subprocess.check_output(["hyprctl", "activeworkspace"]).decode().split(" ")[2]
    x1, y1, x2, y2 = bbox
    for window in get_windows().values():
        if window.details["workspace"].split(" ")[0] != current_workspace:
            continue
        wx1, wy1, wx2, wy2 = window.bbox
        if x2 >= wx1 and x1 <= wx2 and y2 >= wy1 and y1 <= wy2:
            return window

window_id = None
bbox = None
size = None
offset = None

def unregister_window():
    global window_id, size, offset
    window_id = None
    size = None
    offset = None

def get_area():
    global window_id, size, offset
    bbox = utils.get_area() # not global
    size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
    window = get_window_of_bbox(bbox)
    if window:
        window_id = window.id
        offset = (
            bbox[0] - window.bbox[0],
            bbox[1] - window.bbox[1],
        )
    else:
        unregister_window()

def get_bbox():
    global window_id, bbox, offset
    if window_id:
        window = get_windows().get(window_id)
        if window:
            x = window.bbox[0] + offset[0]
            y = window.bbox[1] + offset[1]
            bbox = (x, y, x + size[0], y + size[1])
        else:
            unregister_window()
    return bbox

if __name__ == "__main__":
    bbox = utils.get_area()
    print(get_window_of_bbox(bbox))