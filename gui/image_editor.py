import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import base64

from core.utils import _are_colors_similar

FINDTEXT_CHARS = "0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def bit_to_base64(bit_string: str) -> str:
    padded_string = bit_string + '0' * ((6 - len(bit_string) % 6) % 6)
    result_chars = []
    for i in range(0, len(padded_string), 6):
        chunk = padded_string[i:i+6]
        decimal_value = int(chunk, 2)
        result_chars.append(FINDTEXT_CHARS[decimal_value])
    return "".join(result_chars)

class ImageEditor(ctk.CTkToplevel):
    def __init__(self, master, image: Image.Image):
        super().__init__(master)
        self.original_image = image.convert("RGB")
        self.current_image = self.original_image
        self.result_data = None
        self.main_color_rgb = None
        self.zoom_level = 5.0
        self.ctk_img = None  # Giữ tham chiếu đến CTkImage

        self.title("Tạo mẫu nhận diện ảnh")
        self.geometry(f"{int(master.winfo_screenwidth() * 0.6)}x{int(master.winfo_screenheight() * 0.6)}")
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        self.crop_margins = {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, sticky="ns", padx=(10,5), pady=10)

        self.image_scroll_frame = ctk.CTkScrollableFrame(self, label_text="Ảnh mẫu")
        self.image_scroll_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        self.image_label = ctk.CTkLabel(self.image_scroll_frame, text="")
        self.image_label.pack(expand=True)

        result_frame = ctk.CTkFrame(self)
        result_frame.grid(row=0, column=2, sticky="nsew", padx=(5,10), pady=10)
        result_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(controls_frame, text="1. Cắt ảnh", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        ctk.CTkButton(controls_frame, text="Cắt Trái", command=self.crop_left).pack(pady=4, padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Cắt mép trái của ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)
        ctk.CTkButton(controls_frame, text="Cắt Phải", command=self.crop_right).pack(pady=4, padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Cắt mép phải của ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)
        ctk.CTkButton(controls_frame, text="Cắt Trên", command=self.crop_top).pack(pady=4, padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Cắt mép trên của ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)
        ctk.CTkButton(controls_frame, text="Cắt Dưới", command=self.crop_bottom).pack(pady=4, padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Cắt mép dưới của ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)
        ctk.CTkButton(controls_frame, text="Reset Cắt", command=self.reset_crop, fg_color="#5bc0de").pack(pady=8, padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Đặt lại ảnh về trạng thái ban đầu", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)

        ctk.CTkLabel(controls_frame, text="Phóng to (Zoom)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 0))
        self.zoom_label = ctk.CTkLabel(controls_frame, text=f"{self.zoom_level:.1f}x")
        self.zoom_label.pack()
        self.zoom_slider = ctk.CTkSlider(controls_frame, from_=1.0, to=10.0, number_of_steps=90, command=self.set_zoom)
        self.zoom_slider.set(self.zoom_level)
        self.zoom_slider.pack(pady=(0, 10), padx=10, fill="x")
        ctk.CTkLabel(controls_frame, text="Điều chỉnh mức phóng to của ảnh", wraplength=100, font=ctk.CTkFont(size=10)).pack(pady=2)

        ctk.CTkLabel(result_frame, text="2. Chuyển thành Text", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(result_frame, text="Comment (ID):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.comment_entry = ctk.CTkEntry(result_frame)
        self.comment_entry.grid(row=1, column=1, sticky="e", padx=10, pady=5)
        self.comment_entry.insert(0, "my_skill")
        ctk.CTkLabel(result_frame, text="Đặt tên cho ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).grid(row=2, column=0, columnspan=2, pady=2)

        ctk.CTkButton(result_frame, text="Chuyển đổi ảnh sang Text", command=self.convert_pic_to_text).grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        ctk.CTkLabel(result_frame, text="Chuyển ảnh thành định dạng text để lưu", wraplength=100, font=ctk.CTkFont(size=10)).grid(row=4, column=0, columnspan=2, pady=2)

        ctk.CTkLabel(result_frame, text="Kết quả:", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, columnspan=2, pady=(10,0))
        self.result_textbox = ctk.CTkTextbox(result_frame, height=200, wrap="word")
        self.result_textbox.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        bottom_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkButton(bottom_frame, text="Hủy", command=self.cancel).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(bottom_frame, text="Lưu & Đóng", command=self.save_and_close).grid(row=0, column=1, padx=5, sticky="ew")

        self._update_display()

    def set_zoom(self, value):
        self.zoom_level = float(value)
        self.zoom_label.configure(text=f"{self.zoom_level:.1f}x")
        self._update_display()

    def _update_display(self):
        if not self.winfo_exists():
            return
        w, h = self.current_image.size
        max_display_size = (int(self.winfo_screenwidth() * 0.4), int(self.winfo_screenheight() * 0.4))
        display_size = (min(int(w * self.zoom_level), max_display_size[0]), min(int(h * self.zoom_level), max_display_size[1]))
        
        self.ctk_img = ctk.CTkImage(light_image=self.current_image, dark_image=self.current_image, size=display_size)
        self.image_label.configure(image=self.ctk_img)

    def convert_pic_to_text(self):
        image_to_process = self.current_image
        comment = self.comment_entry.get() or ""
        w, h = image_to_process.size

        raw_bytes = image_to_process.tobytes()
        encoded_data = base64.b64encode(raw_bytes).decode('utf-8')
        final_string = f"|<{comment}>$pic${w}x{h}${encoded_data}"

        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", final_string)
        messagebox.showinfo("Thành công", "Đã chuyển đổi ảnh sang Text.", parent=self)

    def save_and_close(self):
        text_result = self.result_textbox.get("1.0", "end-1c")
        self.result_data = {
            "image": self.current_image,
            "text": text_result if text_result and "Lỗi" not in text_result else ""
        }
        self.destroy()

    def cancel(self):
        self.result_data = None
        self.destroy()

    def get_result(self):
        return self.result_data
    
    def _apply_crop(self):
        w, h = self.original_image.size
        left = self.crop_margins['left']
        top = self.crop_margins['top']
        right = w - self.crop_margins['right']
        bottom = h - self.crop_margins['bottom']
        if left >= right or top >= bottom:
            if hasattr(self, 'last_action'): 
                self.crop_margins[self.last_action[0]] -= self.last_action[1]
                messagebox.showwarning("Cảnh báo", "Vùng cắt không hợp lệ. Vui lòng thử lại.", parent=self)
            return
        self.current_image = self.original_image.crop((left, top, right, bottom))
        self._update_display()
    
    def crop_left(self): self.crop_margins['left'] += 1; self.last_action = ('left', 1); self._apply_crop()
    def crop_right(self): self.crop_margins['right'] += 1; self.last_action = ('right', 1); self._apply_crop()
    def crop_top(self): self.crop_margins['top'] += 1; self.last_action = ('top', 1); self._apply_crop()
    def crop_bottom(self): self.crop_margins['bottom'] += 1; self.last_action = ('bottom', 1); self._apply_crop()
    def reset_crop(self): 
        self.crop_margins = {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        self.current_image = self.original_image
        self._update_display()