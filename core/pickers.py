# core/pickers.py
import customtkinter as ctk
import tkinter as tk
import time
from PIL import Image, ImageTk, ImageGrab
import numpy as np

class ScreenPicker:
    """Tạo một lớp phủ toàn màn hình để người dùng chọn tọa độ hoặc màu sắc."""
    def __init__(self, root):
        self.root = root
        self.overlay = None
        self.result = None
        self.pick_mode = None
        self.magnifier = None
        self.magnifier_canvas = None
        self.magnifier_photo = None
        self.fullscreen_capture = None
        self.zoom_level = 10
        self.capture_size = 20

    def _create_overlay(self):
        self.root.withdraw()
        time.sleep(0.2)
        self.fullscreen_capture = ImageGrab.grab()
        
        self.overlay = ctk.CTkToplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-alpha', 0.1)
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        self.overlay.focus_force()
        self.overlay.bind("<Motion>", self._on_mouse_move)
        self.overlay.bind("<Escape>", self._on_escape)
        self.overlay.bind("<Button-1>", self._on_click)
        
        magnifier_size = self.capture_size * self.zoom_level
        self.magnifier = ctk.CTkToplevel(self.overlay)
        self.magnifier.overrideredirect(True)
        self.magnifier.attributes('-topmost', True)
        self.magnifier.geometry(f"{magnifier_size}x{magnifier_size}+0+0")
        
        self.magnifier_canvas = tk.Canvas(self.magnifier, width=magnifier_size, height=magnifier_size, highlightthickness=0)
        self.magnifier_canvas.pack()
        
        center = magnifier_size / 2
        self.magnifier_canvas.create_line(center, 0, center, magnifier_size, fill="red", width=1)
        self.magnifier_canvas.create_line(0, center, magnifier_size, center, fill="red", width=1)

        self.overlay.after(20, lambda: self._on_mouse_move(None))

    def _on_mouse_move(self, event):
        if event:
            x, y = event.x_root, event.y_root
        else:
            x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()

        if self.magnifier and self.magnifier.winfo_exists():
            self.magnifier.geometry(f"+{x + 20}+{y + 20}")

        half_capture = self.capture_size // 2
        box = (x - half_capture, y - half_capture, x + half_capture, y + half_capture)
        captured_image = self.fullscreen_capture.crop(box)
        
        magnified_image = captured_image.resize(
            (self.capture_size * self.zoom_level, self.capture_size * self.zoom_level),
            Image.Resampling.NEAREST
        )
        
        self.magnifier_photo = ImageTk.PhotoImage(magnified_image)
        
        if self.magnifier_canvas and self.magnifier_canvas.winfo_exists():
            self.magnifier_canvas.create_image(0, 0, anchor=tk.NW, image=self.magnifier_photo)
            center = (self.capture_size * self.zoom_level) / 2
            self.magnifier_canvas.create_line(center, 0, center, self.capture_size * self.zoom_level, fill="red", width=1)
            self.magnifier_canvas.create_line(0, center, self.capture_size * self.zoom_level, center, fill="red", width=1)

    def _close_overlay(self):
        if self.magnifier: self.magnifier.destroy()
        if self.overlay: self.overlay.destroy()
        self.magnifier = None
        self.overlay = None
        self.fullscreen_capture = None
        self.root.deiconify()

    def _on_escape(self, event=None):
        self.result = None
        self._close_overlay()

    def _on_click(self, event):
        x, y = event.x_root, event.y_root
        if self.pick_mode == 'coord':
            self.result = {'x': x, 'y': y}
        elif self.pick_mode == 'color':
            pixel_color = self.fullscreen_capture.getpixel((x, y))
            self.result = {'x': x, 'y': y, 'rgb': tuple(pixel_color)}
        self._close_overlay()

    def pick_coordinate(self):
        self.pick_mode = 'coord'
        self.result = None
        self._create_overlay()
        self.root.wait_window(self.overlay)
        return self.result

    def pick_color(self):
        self.pick_mode = 'color'
        self.result = None
        self._create_overlay()
        self.root.wait_window(self.overlay)
        return self.result

class RegionPicker:
    """Tạo lớp phủ để người dùng vẽ một hình chữ nhật và trả về tọa độ."""
    def __init__(self, root, screenshot=None):
        self.root = root
        self.overlay = None
        self.result = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.screenshot = screenshot
        self.tk_screenshot = None  # Giữ tham chiếu để ảnh không bị xóa

    def _create_overlay(self):
        # Phương thức này không còn ẩn/hiện cửa sổ chính nữa
        self.overlay = ctk.CTkToplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        self.overlay.focus_force()
        
        # Sử dụng ảnh chụp màn hình được cung cấp làm nền
        self.tk_screenshot = ImageTk.PhotoImage(self.screenshot)
        
        self.canvas = tk.Canvas(self.overlay, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Hiển thị ảnh chụp màn hình lên canvas
        self.canvas.create_image(0, 0, image=self.tk_screenshot, anchor="nw")

        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.overlay.bind("<Escape>", self._on_escape)

    def _on_mouse_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2, dash=(5, 5))

    def _on_mouse_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def _on_mouse_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        # Tọa độ từ event đã là tọa độ màn hình vì canvas fullscreen
        abs_x1 = min(x1, x2)
        abs_y1 = min(y1, y2)
        abs_x2 = max(x1, x2)
        abs_y2 = max(y1, y2)
        
        self.result = (abs_x1, abs_y1, abs_x2, abs_y2)
        self._close_overlay()

    def _on_escape(self, event=None):
        self.result = None
        self._close_overlay()

    def _close_overlay(self):
        if self.overlay: self.overlay.destroy()
        self.overlay = None
        # Không còn gọi self.root.deiconify() ở đây

    def pick_region(self):
        if not self.screenshot:
            # Ghi lại lỗi nếu không có ảnh chụp màn hình được cung cấp
            print("Lỗi: RegionPicker yêu cầu phải có ảnh chụp màn hình.")
            return None
        self._create_overlay()
        self.root.wait_window(self.overlay)
        # Bỏ hoàn toàn time.sleep()
        return self.result
