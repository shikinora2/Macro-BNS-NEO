# Tệp: core/optimized_image_recognition.py
#
# PHIÊN BẢN SỬA LỖI "ACCESS VIOLATION" KHI THOÁT ỨNG DỤNG
# - Đảm bảo các đối tượng camera được giải phóng tài nguyên một cách tường minh.

import cv2
import numpy as np
import dxcam
import time

class OptimizedImageRecognizer:
    """
    Lớp này xử lý việc nhận diện ảnh với hiệu suất cao bằng cách sử dụng DXcam.
    Nó sẽ tự động khởi tạo một camera cho mỗi vùng giám sát để tối ưu hóa.
    """
    def __init__(self):
        self.cameras = {} # Dictionary để lưu các instance camera cho mỗi vùng
        self.is_dxcam_available = True
        try:
            # Thử tạo một camera tạm thời để kiểm tra thư viện có hoạt động không.
            temp_camera = dxcam.create()
            if temp_camera:
                # --- SỬA LỖI ---
                # Xóa đối tượng camera tạm thời ngay lập tức để tránh bị rò rỉ.
                del temp_camera
            print("[+] DXcam được hỗ trợ và đã sẵn sàng.")
        except Exception as e:
            print(f"[-] Lỗi khi khởi tạo DXcam: {e}. Chuyển sang chế độ nhận diện cũ (nếu có).")
            self.is_dxcam_available = False

    def get_camera(self, region):
        """
        Lấy hoặc tạo một camera cho một vùng cụ thể.
        Việc này giúp tránh phải khởi tạo lại camera mỗi lần check.
        """
        if not self.is_dxcam_available:
            return None

        region_key = tuple(region)
        if region_key not in self.cameras:
            try:
                print(f"[+] Tạo camera DXcam mới cho vùng: {region}")
                self.cameras[region_key] = dxcam.create(region=region)
                self.cameras[region_key].start(target_fps=240, video_mode=True)
            except Exception as e:
                print(f"[-] Lỗi khi tạo camera DXcam cho vùng {region}: {e}")
                self.cameras[region_key] = None
        return self.cameras[region_key]

    def find_image(self, template_image, region, confidence=0.8):
        """
        Tìm kiếm một ảnh mẫu trong một vùng giám sát cụ thể với hiệu suất cao.
        """
        camera = self.get_camera(region)
        if camera is None:
            return None

        frame = camera.get_latest_frame()

        if frame is None or template_image is None:
            return None

        if len(frame.shape) == 3:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            frame_gray = frame

        if len(template_image.shape) == 3:
            template_gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
        else:
            template_gray = template_image

        result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            return (max_loc[0] + region[0], max_loc[1] + region[1])

        return None

    def stop_all_cameras(self):
        """
        --- SỬA LỖI ---
        Dừng và giải phóng tất cả các camera một cách an toàn khi ứng dụng thoát.
        """
        # Lặp qua một bản sao của danh sách keys để có thể xóa item khỏi dict gốc
        for key in list(self.cameras.keys()):
            camera = self.cameras.pop(key, None) # Lấy và xóa camera khỏi dict
            if camera:
                try:
                    camera.stop()
                    del camera # Xóa đối tượng một cách tường minh
                except Exception as e:
                    print(f"Lỗi khi dừng camera cho vùng {key}: {e}")
        print("[+] Đã dừng và giải phóng tất cả camera DXcam.")
