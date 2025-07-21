# core/key_sender.py
import time
from pynput import keyboard

class KeySender:
    """
    Module riêng biệt để xử lý việc gửi phím bấm.
    Sử dụng pynput.keyboard.Controller.
    """
    def __init__(self, app_instance):
        """
        Khởi tạo KeySender.
        :param app_instance: Một tham chiếu đến instance chính của AutoKeySenderApp 
                              để có thể gọi các hàm log và cập nhật UI.
        """
        self.app = app_instance
        self.keyboard_controller = keyboard.Controller()

    def _get_pynput_key_code(self, key_str):
        """
        Chuyển đổi chuỗi ký tự (ví dụ: 'R', 'Tab', 'L-Shift') sang mã phím 
        mà pynput có thể hiểu được.
        """
        if not key_str:
            return None
        
        key_str_lower = key_str.lower()
        
        # Xử lý các phím chữ và số thông thường
        if len(key_str_lower) == 1 and key_str_lower.isalnum():
            return key_str_lower
            
        # Ánh xạ các phím đặc biệt từ chuỗi sang đối tượng Key của pynput
        special_keys = {
            'tab': keyboard.Key.tab,
            'f1': keyboard.Key.f1,
            'f2': keyboard.Key.f2,
            'f3': keyboard.Key.f3,
            'f4': keyboard.Key.f4,
            'f5': keyboard.Key.f5,
            'f6': keyboard.Key.f6,
            'f7': keyboard.Key.f7,
            'f8': keyboard.Key.f8,
            'f9': keyboard.Key.f9,
            'f10': keyboard.Key.f10,
            'f11': keyboard.Key.f11,
            'f12': keyboard.Key.f12,
            'space': keyboard.Key.space,
            'enter': keyboard.Key.enter,
            'l-shift': keyboard.Key.shift_l,
            'r-shift': keyboard.Key.shift_r,
            'l-ctrl': keyboard.Key.ctrl_l,
            'r-ctrl': keyboard.Key.ctrl_r,
            'l-alt': keyboard.Key.alt_l,
            'r-alt': keyboard.Key.alt_r,
        }
        
        # Xử lý chung cho shift, ctrl, alt nếu không phân biệt trái/phải
        if key_str_lower == 'shift': return keyboard.Key.shift
        if key_str_lower == 'ctrl': return keyboard.Key.ctrl
        if key_str_lower == 'alt': return keyboard.Key.alt

        return special_keys.get(key_str_lower)

    def send_key(self, key_str):
        """
        Gửi một phím bấm. Hàm này được thiết kế để chạy trực tiếp 
        từ luồng macro chính để đảm bảo hiệu suất.
        """
        # Cập nhật overlay (nếu được bật) bằng cách gọi hàm `after` trên luồng UI chính
        if self.app.settings_tab.show_overlay_var.get() == "on":
            self.app.root.after(0, self.app.status_overlay.update_status, f"Gửi phím: {key_str}")
    
        key_code = self._get_pynput_key_code(key_str)
        if key_code:
            try:
                self.keyboard_controller.press(key_code)
                # Thêm một khoảng trễ nhỏ giữa press và release để game có thể nhận phím
                time.sleep(0.02) 
                self.keyboard_controller.release(key_code)
            except Exception as e:
                # Ghi log lỗi thông qua luồng UI chính
                self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi gửi phím '{key_str}': {e}")
        else:
            # Ghi log lỗi thông qua luồng UI chính
            self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi: Không tìm thấy mã pynput cho '{key_str}'.")
