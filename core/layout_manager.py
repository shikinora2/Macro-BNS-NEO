# core/layout_manager.py
import json
import cv2
import numpy as np
from PIL import ImageGrab
import os

from .utils import resource_path, base64_to_image

class LayoutManager:
    """
    Quản lý việc tải, định vị và truy cập các thành phần giao diện
    dựa trên các profile được định nghĩa trước.
    """
    def __init__(self, app_instance):
        self.app = app_instance
        self.profiles = {}
        self.active_profile_name = None
        self.active_profile_data = {}
        
        # Lưu trữ tọa độ thực tế của các vùng sau khi đã được định vị
        self.located_regions = {}

        self.load_profiles()

    def load_profiles(self):
        """Tải tất cả các profile từ file layout_profiles.json."""
        try:
            profile_path = resource_path(os.path.join('core', 'layout_profiles.json'))
            with open(profile_path, 'r', encoding='utf-8') as f:
                self.profiles = json.load(f)
            # Chỉ log khi tải thành công
            if self.profiles:
                self.app.home_tab.log_message(f"Đã tải {len(self.profiles)} profile giao diện.")
        except FileNotFoundError:
            # Nếu không tìm thấy file, coi như không có profile nào.
            # Tab Cài đặt sẽ tự động chuyển sang chế độ Thủ công.
            self.profiles = {}
        except json.JSONDecodeError:
            # Nếu file bị lỗi, báo cho người dùng biết.
            self.profiles = {}
            self.app.home_tab.log_message("Lỗi: File layout_profiles.json bị hỏng hoặc sai định dạng.")

    def get_profile_names(self):
        """Lấy danh sách tên của các profile đã tải."""
        return list(self.profiles.keys())

    def set_active_profile(self, profile_name):
        """Chọn một profile để sử dụng."""
        if profile_name in self.profiles:
            self.active_profile_name = profile_name
            self.active_profile_data = self.profiles[profile_name]
            # Reset các tọa độ đã định vị khi đổi profile
            self.located_regions = {}
            self.app.home_tab.log_message(f"Đã chọn profile: {profile_name}")
            return True
        self.app.home_tab.log_message(f"Lỗi: Không tìm thấy profile tên '{profile_name}'.")
        return False

    def locate_ui_element(self, region_name):
        """
        Quét màn hình để tìm một thành phần UI dựa trên ảnh mẫu (anchor).
        """
        if not self.active_profile_data:
            self.app.home_tab.log_message("Lỗi định vị: Chưa chọn profile giao diện.")
            return False

        region_info = self.active_profile_data.get(region_name)
        if not region_info:
            self.app.home_tab.log_message(f"Lỗi định vị: Không tìm thấy định nghĩa cho '{region_name}' trong profile.")
            return False

        search_coords = region_info.get("search_region")
        anchor_b64 = region_info.get("anchor_b64")

        if not search_coords or not anchor_b64:
            self.app.home_tab.log_message(f"Lỗi định vị: Vùng '{region_name}' thiếu thông tin search_region hoặc anchor.")
            return False

        try:
            screenshot = ImageGrab.grab(bbox=search_coords)
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

            anchor_img = base64_to_image(anchor_b64)
            anchor_cv = cv2.cvtColor(np.array(anchor_img), cv2.COLOR_RGB2GRAY)
            
            result = cv2.matchTemplate(screenshot_cv, anchor_cv, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            confidence_threshold = 0.8
            if max_val >= confidence_threshold:
                anchor_w, anchor_h = anchor_img.size
                top_left = (search_coords[0] + max_loc[0], search_coords[1] + max_loc[1])
                
                final_coords = (top_left[0], top_left[1], top_left[0] + anchor_w, top_left[1] + anchor_h)
                self.located_regions[region_name] = final_coords
                
                self.app.home_tab.log_message(f"Đã định vị '{region_name}' tại {final_coords}.")
                return True
            else:
                self.app.home_tab.log_message(f"Không thể định vị '{region_name}'. Độ tin cậy thấp: {max_val:.2f}")
                return False

        except Exception as e:
            self.app.home_tab.log_message(f"Lỗi nghiêm trọng khi định vị '{region_name}': {e}")
            return False

    def get_located_region(self, region_name):
        """
        Lấy tọa độ của một vùng đã được định vị trước đó.
        """
        return self.located_regions.get(region_name)
