# core/image_logic_mixin.py
from tkinter import filedialog, messagebox
from PIL import Image
import customtkinter as ctk

from core.pickers import RegionPicker
from gui.image_editor import ImageEditor
from core.utils import base64_to_image

class ImageLogicMixin:
    def __init__(self, app_instance):
        self.app = app_instance

    def get_monitor_region(self, data_container):
        """Sử dụng RegionPicker đã được tối ưu hóa để chọn một vùng."""
        try:
            picker = RegionPicker(self.app.root)
            coords = picker.pick_region()
            if coords:
                data_container["monitor_region"] = coords
                data_container["monitor_label"].configure(text=str(coords))
                self.app.trang_chu_tab.log_message("Đã chọn vùng giám sát thành công.")
            else:
                self.app.trang_chu_tab.log_message("Đã hủy chọn vùng giám sát.")
        except Exception as e:
            self.app.trang_chu_tab.log_message(f"Lỗi khi chọn vùng giám sát: {e}")
            messagebox.showerror("Lỗi", f"Không thể chọn vùng giám sát.\nChi tiết: {e}", parent=self.app.root)

    def get_template_image(self, type_id, data_container):
        """Chụp một vùng màn hình để làm ảnh mẫu."""
        try:
            picker = RegionPicker(self.app.root)
            coords = picker.pick_region()
            if not coords:
                self.app.trang_chu_tab.log_message("Đã hủy chọn ảnh mẫu.")
                return
            
            # Lấy ảnh từ chính screenshot của picker để đảm bảo chính xác
            if picker.screenshot:
                image = picker.screenshot.crop(coords)
                self._process_image_with_editor(type_id, data_container, image, "Đã cập nhật ảnh mẫu.")
        except Exception as e:
            self.app.trang_chu_tab.log_message(f"Lỗi khi chụp ảnh mẫu: {e}")
            messagebox.showerror("Lỗi", f"Không thể chụp ảnh mẫu.\nChi tiết: {e}", parent=self.app.root)

    def load_template_image(self, type_id, data_container):
        """Tải ảnh mẫu từ file."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg")])
        if not file_path:
            self.app.trang_chu_tab.log_message("Đã hủy tải ảnh mẫu.")
            return
        try:
            image = Image.open(file_path).convert("RGB")
            self._process_image_with_editor(type_id, data_container, image, "Đã tải ảnh mẫu từ file.")
        except Exception as e:
            self.app.trang_chu_tab.log_message(f"Lỗi khi tải ảnh mẫu: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở file ảnh. Vui lòng kiểm tra định dạng file.\nChi tiết: {e}", parent=self.app.root)

    def _process_image_with_editor(self, type_id, data_container, image, log_message):
        editor_window = ImageEditor(self.app.root, image)
        # wait_window là cần thiết ở đây vì ImageEditor là một cửa sổ modal (hộp thoại)
        self.app.root.wait_window(editor_window)
        result = editor_window.get_result()
        if result and result.get("image"):
            self.update_template_image(data_container, result["image"])
            self.app.trang_chu_tab.log_message(f"[{type_id.upper()}] {log_message}")

    def update_template_image(self, data_container, image_obj):
        """Cập nhật ảnh mẫu và giữ tham chiếu CTkImage."""
        data_container["template_image"] = image_obj
        img_label = data_container["img_label"]
        
        preview_width, preview_height = 150, 120
        
        display_image = image_obj.copy()
        display_image.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)

        data_container["ctk_image"] = ctk.CTkImage(light_image=display_image, dark_image=display_image, size=(display_image.width, display_image.height))
        img_label.configure(image=data_container["ctk_image"], text="")

    def test_image_match(self, data_container):
        """Kiểm tra nhận diện ảnh mẫu."""
        if data_container.get("template_image") is None or not isinstance(data_container.get("monitor_region"), tuple):
            self.app.trang_chu_tab.log_message("Lỗi: Thiếu vùng giám sát hoặc ảnh mẫu.")
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Vùng giám sát và Ảnh mẫu trước.", parent=self.app.root)
            return
        self.app.test_single_image_condition(data_container)

    def set_image_from_config(self, data_container, image_b64):
        """Thiết lập ảnh mẫu từ cấu hình."""
        image = base64_to_image(image_b64)
        if image:
            self.update_template_image(data_container, image)
        else:
            self.app.trang_chu_tab.log_message("Lỗi: Không thể tải ảnh mẫu từ cấu hình.")
