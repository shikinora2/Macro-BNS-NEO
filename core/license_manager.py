# core/license_manager.py
import json
import base64
import os
from datetime import datetime
from core.utils import resource_path # <-- Import hàm mới

class LicenseManager:
    def __init__(self):
        # Dùng hàm resource_path để tìm đúng đường dẫn của keys.json
        self.keys_file_path = resource_path(os.path.join('core', 'keys.json'))
        self.keys_data = self._load_keys()

    def _load_keys(self):
        """Tải cơ sở dữ liệu keys từ file JSON được đóng gói."""
        try:
            with open(self.keys_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Nếu không tìm thấy file keys.json, trả về một từ điển rỗng
            # để ứng dụng không bị crash.
            return {}

    def check_license(self, user_key):
        """
        Kiểm tra một key.
        Trả về một tuple: (status, expiry_date)
        - status: "VALID", "INVALID", "EXPIRED"
        - expiry_date: ngày hết hạn (str) hoặc None
        """
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

