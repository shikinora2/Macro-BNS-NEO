import numpy as np
import base64
import io
from PIL import Image
import sys
import os
import customtkinter as ctk

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _are_colors_similar(color1_rgb, color2_rgb, tolerance_percent=10):
    max_dist = np.sqrt(3 * (255**2))
    absolute_tolerance = (tolerance_percent / 100.0) * max_dist
    diff = np.sqrt(np.sum((np.array(color1_rgb) - np.array(color2_rgb)) ** 2))
    return diff <= absolute_tolerance

def image_to_base64(pil_image):
    if pil_image is None: return None
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_image(base64_string):
    if base64_string is None: return None
    try:
        img_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(img_data))
    except Exception:
        return None

def get_responsive_size(master, width_ratio=0.1, height_ratio=0.1):
    """Tính toán kích thước widget dựa trên tỷ lệ màn hình."""
    screen_width = master.winfo_screenwidth()
    screen_height = master.winfo_screenheight()
    return int(screen_width * width_ratio), int(screen_height * height_ratio)

def add_tooltip(widget, text, wraplength=100):
    """Thêm tooltip cho widget."""
    tooltip = ctk.CTkLabel(widget.master, text=text, wraplength=wraplength, font=ctk.CTkFont(size=10))
    tooltip.pack_forget()

    def show_tooltip(event):
        if widget.winfo_exists():
            x, y = widget.winfo_rootx() + 20, widget.winfo_rooty() + 20
            tooltip.place(x=x, y=y)

    def hide_tooltip(event):
        tooltip.place_forget()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)