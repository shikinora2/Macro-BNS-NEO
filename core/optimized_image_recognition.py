# Tệp: core/optimized_image_recognition.py
#
# PHIÊN BẢN SỬA LỖI & TỐI ƯU HÓA
# - Sửa lỗi kiểm tra phiên bản DXcam bằng cách sử dụng try-except khi import.
# - Giữ nguyên "lazy initialization" để tối ưu và tránh lỗi.

import cv2
import numpy as np
import time

class OptimizedImageRecognizer:
    """
    Lớp này xử lý việc nhận diện ảnh với hiệu suất cao bằng cách sử dụng DXcam.
    """
    def __init__(self):
        self.cameras = {}  # Dictionary để lưu các instance camera cho mỗi vùng
        self.is_dxcam_available = True
        try:
            # SỬA LỖI: Đây là cách kiểm tra an toàn nhất.
            # Nếu thư viện có thể được import, chúng ta coi như nó đã sẵn sàng.
            import dxcam
            print(f"[+] Thư viện DXcam đã được tìm thấy và sẵn sàng.")
        except ImportError:
            print(f"[-] Lỗi: Thư viện DXcam chưa được cài đặt. Nhận diện ảnh sẽ không hoạt động.")
            self.is_dxcam_available = False
        except Exception as e:
            # Bắt các lỗi tiềm ẩn khác khi import
            print(f"[-] Lỗi không xác định với DXcam: {e}. Nhận diện ảnh sẽ không hoạt động.")
            self.is_dxcam_available = False

    def get_camera(self, region):
        """
        Lấy hoặc tạo một camera cho một vùng cụ thể (Lazy Initialization).
        """
        if not self.is_dxcam_available:
            return None

        # Lazily import dxcam here to ensure it's only imported when needed
        import dxcam

        region_key = tuple(region)
        if region_key not in self.cameras:
            try:
                print(f"[+] Tạo camera DXcam mới cho vùng: {region}")
                camera = dxcam.create(region=region)
                if camera is None:
                    raise Exception("DXcam.create() trả về None. Card đồ họa có thể không được hỗ trợ.")
                camera.start(target_fps=240, video_mode=True)
                self.cameras[region_key] = camera
            except Exception as e:
                print(f"[-] Lỗi nghiêm trọng khi tạo camera DXcam cho vùng {region}: {e}")
                self.cameras[region_key] = None
        
        return self.cameras.get(region_key)

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
        Dừng và giải phóng tất cả các camera một cách an toàn khi ứng dụng thoát.
        """
        for key in list(self.cameras.keys()):
            camera = self.cameras.pop(key, None)
            if camera:
                try:
                    camera.stop()
                    del camera
                except Exception as e:
                    print(f"Lỗi khi dừng camera cho vùng {key}: {e}")
        print("[+] Đã dừng và giải phóng tất cả camera DXcam.")
