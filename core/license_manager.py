# core/license_manager.py
import json
import base64
import os
from datetime import datetime
# Không cần import resource_path ở đây nữa

class LicenseManager:
    def __init__(self):
        """
        Khởi tạo LicenseManager.
        Đường dẫn đến keys.json giờ đây được xác định một cách đáng tin cậy
        dựa trên vị trí của chính tệp script này.
        """
        try:
            # Lấy đường dẫn tuyệt đối đến thư mục chứa file script này (thư mục 'core')
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Ghép đường dẫn thư mục đó với tên file 'keys.json'
            self.keys_file_path = os.path.join(script_dir, 'keys.json')
        except NameError:
            # Fallback cho các môi trường không định nghĩa __file__ (ví dụ: khi đóng gói)
            # Giả định rằng thư mục làm việc hiện tại là thư mục gốc của dự án
            self.keys_file_path = os.path.join('core', 'keys.json')

        self.keys_data = self._load_keys()

    def _load_keys(self):
        """Tải cơ sở dữ liệu keys từ file JSON."""
        # Kiểm tra xem tệp có tồn tại không trước khi mở
        if not os.path.exists(self.keys_file_path):
            print(f"LỖI: Không tìm thấy tệp keys.json tại đường dẫn: {self.keys_file_path}")
            return {}
        
        try:
            with open(self.keys_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Ghi lại lỗi để dễ dàng gỡ lỗi hơn
            print(f"LỖI: Không thể tải tệp keys.json. Lỗi: {e}")
            return {}

    def check_license(self, user_key):
        """
        Kiểm tra một key.
        Trả về một tuple: (status, expiry_date)
        - status: "VALID", "INVALID", "EXPIRED"
        - expiry_date: ngày hết hạn (str) hoặc None
        """
        if not self.keys_data:
            # Nếu không có dữ liệu key nào được tải, mọi key đều không hợp lệ.
            print("CẢNH BÁO: Cơ sở dữ liệu key rỗng. Mọi key sẽ bị từ chối.")
            return "INVALID", None

        if not user_key or user_key not in self.keys_data:
            return "INVALID", None

        encoded_data = self.keys_data[user_key]
        try:
            # Giải mã chuỗi base64
            decoded_str = base64.b64decode(encoded_data).decode('utf-8')
            # Chuyển chuỗi JSON thành đối tượng Python
            key_info = json.loads(decoded_str)
            
            expiry_str = key_info.get("expiry")
            if not expiry_str:
                return "INVALID", None

            # Chuyển đổi chuỗi ngày tháng (định dạng YYYY-MM-DD) thành đối tượng datetime
            expiration_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            
            # So sánh với ngày hiện tại
            if datetime.now() > expiration_date:
                # Trả về ngày hết hạn theo định dạng DD-MM-YYYY cho dễ đọc
                return "EXPIRED", expiration_date.strftime('%d-%m-%Y')
            else:
                # Trả về ngày hết hạn theo định dạng DD-MM-YYYY cho dễ đọc
                return "VALID", expiration_date.strftime('%d-%m-%Y')

        except Exception:
            # Nếu có bất kỳ lỗi nào trong quá trình giải mã hoặc xử lý,
            # coi như key không hợp lệ.
            return "INVALID", None
