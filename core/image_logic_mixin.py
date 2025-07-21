from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image
import customtkinter as ctk
import threading

from core.pickers import RegionPicker
from gui.image_editor import ImageEditor
from core.utils import base64_to_image

class ImageLogicMixin:
    def __init__(self, app_instance):
        self.app = app_instance

    def get_monitor_region(self, data_container):
        """Chụp ảnh màn hình và chọn vùng mà không ẩn cửa sổ chính."""
        overlay = ctk.CTkToplevel(self.app.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-alpha', 0.0)
        overlay.attributes('-topmost', True)
        overlay.overrideredirect(True)
        
        def capture_and_process():
            try:
                # Chụp toàn bộ màn hình một lần
                fullscreen_capture = ImageGrab.grab()
                # Đóng lớp phủ ngay lập tức
                overlay.destroy()
                # Mở công cụ chọn vùng với ảnh đã chụp
                picker = RegionPicker(self.app.root, screenshot=fullscreen_capture)
                coords = picker.pick_region()
                if coords:
                    data_container["monitor_region"] = coords
                    data_container["monitor_label"].configure(text=str(coords))
                    self.app.home_tab.log_message("Đã chọn vùng giám sát thành công.")
            except Exception as e:
                self.app.home_tab.log_message(f"Lỗi khi chọn vùng giám sát: {e}")
                messagebox.showerror("Lỗi", f"Không thể chọn vùng giám sát.\nChi tiết: {e}", parent=self.app.root)
        
        # Chạy việc chụp và xử lý trong một luồng riêng để không làm treo UI
        threading.Thread(target=capture_and_process, daemon=True).start()

    def get_template_image(self, type_id, data_container):
        """Chụp ảnh mẫu mà không ẩn cửa sổ chính."""
        overlay = ctk.CTkToplevel(self.app.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-alpha', 0.0)
        overlay.attributes('-topmost', True)
        overlay.overrideredirect(True)
        
        def capture_and_process():
            try:
                fullscreen_capture = ImageGrab.grab()
                overlay.destroy()
                picker = RegionPicker(self.app.root, screenshot=fullscreen_capture)
                coords = picker.pick_region()
                if not coords:
                    self.app.home_tab.log_message("Đã hủy chọn ảnh mẫu.")
                    return
                # Cắt ảnh mẫu từ ảnh chụp toàn màn hình
                image = fullscreen_capture.crop(coords)
                self._process_image_with_editor(type_id, data_container, image, "Đã cập nhật ảnh mẫu.")
            except Exception as e:
                self.app.home_tab.log_message(f"Lỗi khi chụp ảnh mẫu: {e}")
                messagebox.showerror("Lỗi", f"Không thể chụp ảnh mẫu.\nChi tiết: {e}", parent=self.app.root)
        
        threading.Thread(target=capture_and_process, daemon=True).start()

    def load_template_image(self, type_id, data_container):
        """Tải ảnh mẫu từ file."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg")])
        if not file_path:
            self.app.home_tab.log_message("Đã hủy tải ảnh mẫu.")
            return
        try:
            image = Image.open(file_path).convert("RGB")
            self._process_image_with_editor(type_id, data_container, image, "Đã tải ảnh mẫu từ file.")
        except Exception as e:
            self.app.home_tab.log_message(f"Lỗi khi tải ảnh mẫu: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở file ảnh. Vui lòng kiểm tra định dạng file.\nChi tiết: {e}", parent=self.app.root)

    def _process_image_with_editor(self, type_id, data_container, image, log_message):
        """Mở cửa sổ chỉnh sửa ảnh và xử lý kết quả."""
        editor_window = ImageEditor(self.app.root, image)
        editor_window.lift()
        self.app.root.wait_window(editor_window) # Chờ cho đến khi cửa sổ editor được đóng
        result = editor_window.get_result()
        if result and result.get("image"):
            self.update_template_image(data_container, result["image"])
            self.app.home_tab.log_message(f"[{type_id.upper()}] {log_message}")

    def update_template_image(self, data_container, image_obj):
        """Cập nhật ảnh mẫu trên giao diện và giữ tham chiếu CTkImage."""
        data_container["template_image"] = image_obj
        img_label = data_container["img_label"]
        
        # Tính toán kích thước hiển thị để vừa với label
        label_w = img_label.winfo_width()
        label_h = img_label.winfo_height()
        
        # Đảm bảo kích thước hợp lệ
        if label_w < 10 or label_h < 10:
            label_w, label_h = 150, 120 # Kích thước mặc định nếu label chưa được vẽ

        # Thay đổi kích thước ảnh để hiển thị mà không làm biến dạng
        image_obj.thumbnail((label_w - 10, label_h - 10), Image.Resampling.LANCZOS)
        
        data_container["ctk_image"] = ctk.CTkImage(light_image=image_obj, dark_image=image_obj, size=(image_obj.width, image_obj.height))
        img_label.configure(image=data_container["ctk_image"], text="")

    def test_image_match(self, data_container):
        """Kiểm tra nhận diện ảnh mẫu."""
        if data_container.get("template_image") is None or not isinstance(data_container.get("monitor_region"), tuple):
            self.app.home_tab.log_message("Lỗi: Thiếu vùng giám sát hoặc ảnh mẫu.")
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Vùng giám sát và Ảnh mẫu trước.", parent=self.app.root)
            return
        self.app.test_single_image_condition(data_container)

    def set_image_from_config(self, data_container, image_b64):
        """Thiết lập ảnh mẫu từ dữ liệu cấu hình (base64)."""
        image = base64_to_image(image_b64)
        if image:
            self.update_template_image(data_container, image)
        else:
            self.app.home_tab.log_message("Lỗi: Không thể tải ảnh mẫu từ cấu hình.")
