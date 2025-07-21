# gui/status_overlay.py
import customtkinter as ctk
import win32gui
import win32con
import win32api

class StatusOverlay(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Màu nền mà chúng ta sẽ làm cho trong suốt
        self.TRANSPARENT_COLOR = '#000001' 

        # Cấu hình cửa sổ cơ bản
        self.overrideredirect(True)  # Bỏ viền và thanh tiêu đề
        self.geometry("300x40+100+100") # Kích thước và vị trí ban đầu
        self.lift()  # Đưa lên trên
        self.attributes("-topmost", True)  # Luôn hiển thị trên cùng
        
        # Làm cho nền cửa sổ trong suốt
        self.config(bg=self.TRANSPARENT_COLOR)
        self.attributes("-transparentcolor", self.TRANSPARENT_COLOR)

        # Nhãn để hiển thị văn bản trạng thái
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00FFFF",  # Màu Cyan cho dễ nhìn
            fg_color="transparent"
        )
        self.status_label.pack(expand=True, fill="both")
        
        # Sử dụng win32api để làm cho cửa sổ có thể "nhấn xuyên qua"
        self.after(100, self._set_click_through)
        
    def _set_click_through(self):
        try:
            hwnd = self.winfo_id()
            styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            styles |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, styles)
            win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 1), 0, win32con.LWA_COLORKEY)
        except Exception as e:
            print(f"Lỗi khi cài đặt click-through: {e}")

    def update_status(self, text, duration_ms=1500):
        """Hiển thị một trạng thái và tự động xóa sau một khoảng thời gian."""
        self.status_label.configure(text=text)
        # Hủy lịch trình xóa cũ (nếu có)
        if hasattr(self, '_clear_job'):
            self.after_cancel(self._clear_job)
        # Lên lịch trình xóa mới
        self._clear_job = self.after(duration_ms, lambda: self.status_label.configure(text=""))
        
    def move_window(self, x, y):
        """Di chuyển cửa sổ đến tọa độ (x, y) mới."""
        self.geometry(f"+{x}+{y}")

    def show(self):
        self.deiconify()

    def hide(self):
        self.withdraw()