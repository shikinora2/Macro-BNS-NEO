# core/pickers.py
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab

class PickerBase:
    """Lớp cơ sở để xử lý trạng thái cửa sổ một cách an toàn khi chụp ảnh màn hình."""
    def __init__(self, root):
        self.root = root
        self.overlay = None
        self.result = None
        self.screenshot = None
        self.tk_screenshot = None
        self.waiter_window = None

    def _launch(self):
        """Điểm bắt đầu chính để khởi chạy quá trình chọn."""
        self.result = None
        
        # Ẩn cửa sổ chính để không bị dính vào ảnh chụp.
        self.root.withdraw()
        
        # Lên lịch chụp ảnh và tạo lớp phủ sau một khoảng trễ ngắn.
        # Điều này đảm bảo cửa sổ chính có đủ thời gian để biến mất hoàn toàn.
        self.root.after(200, self._capture_and_create_overlay)
        
        # Tạo một cửa sổ tạm, ẩn đi. Chúng ta sẽ chờ cửa sổ này.
        # Khi quá trình chọn kết thúc, lớp phủ sẽ phá hủy cửa sổ này,
        # giúp giải phóng lệnh chờ `wait_window`.
        waiter = ctk.CTkToplevel(self.root)
        waiter.withdraw()
        self.waiter_window = waiter
        
        self.root.wait_window(self.waiter_window)
        
        # Sau khi wait_window được giải phóng, quá trình kết thúc.
        self.root.deiconify() # Hiện lại cửa sổ chính.
        return self.result

    def _capture_and_create_overlay(self):
        """Chụp ảnh màn hình và gọi hàm tạo giao diện cho lớp phủ."""
        try:
            self.screenshot = ImageGrab.grab()
            self._create_overlay_ui() # Sẽ được triển khai bởi các lớp con
        except Exception as e:
            print(f"Lỗi khi chụp ảnh hoặc tạo lớp phủ: {e}")
            self._finalize() # Dọn dẹp nếu có lỗi xảy ra

    def _finalize(self):
        """Dọn dẹp tất cả các cửa sổ và giải phóng lệnh chờ."""
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.overlay = None
        
        if self.waiter_window and self.waiter_window.winfo_exists():
            self.waiter_window.destroy()
        self.waiter_window = None

    def _on_escape(self, event=None):
        self.result = None
        self._finalize()

    def _create_overlay_ui(self):
        """Các lớp con phải triển khai phương thức này."""
        raise NotImplementedError

class ScreenPicker(PickerBase):
    """Tạo lớp phủ để người dùng chọn tọa độ hoặc màu sắc."""
    def __init__(self, root):
        super().__init__(root)
        self.pick_mode = None
        self.magnifier = None
        self.magnifier_canvas = None
        self.magnifier_photo = None
        self.zoom_level = 10
        self.capture_size = 20

    def pick_coordinate(self):
        self.pick_mode = 'coord'
        return self._launch()

    def pick_color(self):
        self.pick_mode = 'color'
        return self._launch()

    def _create_overlay_ui(self):
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
        if not self.screenshot: return
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()

        if self.magnifier and self.magnifier.winfo_exists():
            self.magnifier.geometry(f"+{x + 20}+{y + 20}")

        half_capture = self.capture_size // 2
        box = (x - half_capture, y - half_capture, x + half_capture, y + half_capture)
        captured_image = self.screenshot.crop(box)
        
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

    def _on_click(self, event):
        x, y = event.x_root, event.y_root
        if self.pick_mode == 'coord':
            self.result = {'x': x, 'y': y}
        elif self.pick_mode == 'color':
            pixel_color = self.screenshot.getpixel((x, y))
            self.result = {'x': x, 'y': y, 'rgb': tuple(pixel_color)}
        self._finalize()

    def _finalize(self):
        if self.magnifier and self.magnifier.winfo_exists():
            self.magnifier.destroy()
        self.magnifier = None
        super()._finalize()

class RegionPicker(PickerBase):
    """Tạo lớp phủ để người dùng vẽ một hình chữ nhật."""
    def __init__(self, root):
        super().__init__(root)
        self.start_x = None
        self.start_y = None
        self.rect = None

    def pick_region(self):
        return self._launch()

    def _create_overlay_ui(self):
        self.overlay = ctk.CTkToplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        self.overlay.focus_force()
        
        self.tk_screenshot = ImageTk.PhotoImage(self.screenshot)
        
        self.canvas = tk.Canvas(self.overlay, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
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
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def _on_mouse_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        abs_x1 = min(x1, x2)
        abs_y1 = min(y1, y2)
        abs_x2 = max(x1, x2)
        abs_y2 = max(y1, y2)
        
        self.result = (abs_x1, abs_y1, abs_x2, abs_y2)
        self._finalize()
