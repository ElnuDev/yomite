import os
import subprocess

def get_area():
    slop = os.environ["XDG_SESSION_TYPE"] == "x11"
    area = subprocess.check_output(["slop" if slop else "slurp"]).decode().strip()
    if slop:
        dim_str, x_str, y_str = area.split('+')
    else:
        pos_str, dim_str = area.split()
        x_str, y_str = pos_str.split(',')
    x, y = int(x_str), int(y_str)
    w_str, h_str = dim_str.split('x')
    w, h = int(w_str), int(h_str)
    return (x, y, x + w, y + h)