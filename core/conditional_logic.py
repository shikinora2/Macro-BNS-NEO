# core/conditional_logic.py
import cv2
import numpy as np
from PIL import ImageGrab
import time
import concurrent.futures

from .utils import _hex_to_rgb, _are_colors_similar, base64_to_image

class ConditionalLogicHandler:
    def __init__(self, app_instance, image_recognizer):
        self.app = app_instance
        self.image_recognizer = image_recognizer
        self.template_cache = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='ImageCheck')

    def shutdown_executor(self):
        print("Shutting down image checking thread pool...")
        self.executor.shutdown(wait=False, cancel_futures=True)

    def clear_template_cache(self):
        self.template_cache.clear()
        self.app.trang_chu_tab.log_message("Đã xóa cache ảnh mẫu.")

    def _process_config_to_actions(self, combo_config):
        actions = []
        if not combo_config: return actions
        for item in combo_config:
            key = item.get("key")
            delay_str = item.get("delay")
            if key and delay_str and delay_str.isdigit():
                actions.append((key, int(delay_str)))
        return actions

    def get_disabled_keys(self, sub_combo_full_config):
        disabled_keys = set()
        image_based_rules = {
            "Skill": sub_combo_full_config.get("skill", {}),
            "Crit": sub_combo_full_config.get("crit", {})
        }
        for rule_name, rule_set in image_based_rules.items():
            for rule_config in rule_set.get("rules", []):
                is_enabled = rule_config.get("enabled") == "on"
                is_disable_rule = rule_config.get("rule_type") == "Vô hiệu hóa phím"
                
                if is_enabled and is_disable_rule:
                    if self._check_image_condition(rule_config):
                        key_to_disable = rule_config.get("disabled_key")
                        if key_to_disable:
                            disabled_keys.add(key_to_disable)
        return disabled_keys

    def _check_image_rule_task(self, rule_name, rule_config):
        if self._check_image_condition(rule_config):
            actions = self._process_config_to_actions(rule_config.get("combo"))
            if actions:
                return actions, rule_name
        return None, None

    def get_current_mana_level(self, mana_config):
        """
        Xác định mức mana hiện tại bằng cách tìm orb đầu tiên ở trạng thái "Tắt".
        """
        detection_config = mana_config.get("detection", {})
        coords_list = detection_config.get("coords_manual", [])
        
        # Lấy cả hai thư viện màu
        color_library_on = detection_config.get("color_library_manual_on", [])
        color_library_off = detection_config.get("color_library_manual_off", [])

        if not coords_list or not color_library_on or not color_library_off:
            return None # Cần tất cả cấu hình để tiếp tục

        try:
            tolerance = int(detection_config.get("tolerance", 10))
            rgb_colors_on = [_hex_to_rgb(c) for c in color_library_on]
            rgb_colors_off = [_hex_to_rgb(c) for c in color_library_off]
            
            # Chụp ảnh màn hình một lần duy nhất để tối ưu hiệu suất
            screenshot = ImageGrab.grab()
            
            # Duyệt ngược từ orb cao nhất (orb #10) xuống thấp nhất
            # Tọa độ trong coords_list được sắp xếp từ 1 đến 10
            for i in range(len(coords_list) - 1, -1, -1):
                orb_data = coords_list[i]
                coord = orb_data.get('coord')

                if not coord:
                    continue

                pixel_color_rgb = screenshot.getpixel(coord)

                # Kiểm tra xem màu pixel có khớp với thư viện màu "Bật" không
                is_on = any(_are_colors_similar(pixel_color_rgb, on_color, tolerance) for on_color in rgb_colors_on)
                
                # Kiểm tra xem màu pixel có khớp với thư viện màu "Tắt" không
                is_off = any(_are_colors_similar(pixel_color_rgb, off_color, tolerance) for off_color in rgb_colors_off)

                # LOGIC CHÍNH: Nếu orb này không phải màu "Bật" VÀ là màu "Tắt",
                # thì đây là orb đầu tiên bị mất mana.
                # Mức mana hiện tại là mức của orb ngay trước nó.
                if not is_on and is_off:
                    # Mức mana hiện tại là chỉ số của orb này (ví dụ: orb thứ 5 có chỉ số 4)
                    return i 

            # Nếu vòng lặp kết thúc mà không tìm thấy orb nào ở trạng thái "Tắt",
            # có nghĩa là tất cả các orb đều đang đầy.
            return 10

        except (IndexError, ValueError, OSError, TypeError) as e:
            self.app.trang_chu_tab.log_message(f"Lỗi nhận diện Mana: {e}")
            return None

    def check_for_sub_combo(self, sub_combo_full_config):
        # Ưu tiên 1: HP
        hp_config = sub_combo_full_config.get("hp", {})
        if hp_config.get("enabled") == "on" and self._check_hp_threshold_condition(hp_config):
            actions = self._process_config_to_actions(hp_config.get("combo"))
            if actions: return actions, f"HP (dưới {hp_config.get('threshold')}%)"

        # Ưu tiên 2: Mana (Sử dụng logic khớp chính xác)
        mana_config = sub_combo_full_config.get("mana", {})
        if mana_config:
            current_mana_level = self.get_current_mana_level(mana_config)
            if current_mana_level is not None:
                # Tìm quy tắc có mức mana khớp chính xác với mana hiện tại
                for rule in mana_config.get("rules", []):
                    if rule.get("enabled") == "on" and rule.get("level") == current_mana_level:
                        actions = self._process_config_to_actions(rule.get("combo"))
                        if actions:
                            return actions, f"Mana (mức {current_mana_level})"
                        break

        # Ưu tiên 3 & 4: Các quy tắc ảnh
        simple_image_rules = []
        complex_image_rules = []
        image_based_configs = {
            "Skill": sub_combo_full_config.get("skill", {}),
            "Crit": sub_combo_full_config.get("crit", {})
        }
        for type_name, rule_set in image_based_configs.items():
            for i, config in enumerate(rule_set.get("rules", [])):
                if config.get("enabled") == "on" and config.get("rule_type") == "Kích hoạt Combo":
                    rule_name = f"{type_name} #{i+1}"
                    if config.get("logic_order") == "Kiểm tra điều kiện rồi sử dụng Skill":
                        simple_image_rules.append((rule_name, config))
                    else:
                        complex_image_rules.append((rule_name, config))

        if simple_image_rules:
            future_to_rule = {self.executor.submit(self._check_image_rule_task, name, config): (name, config) for name, config in simple_image_rules}
            try:
                for future in concurrent.futures.as_completed(future_to_rule):
                    actions, name = future.result()
                    if actions:
                        for f in future_to_rule: f.cancel()
                        return actions, name
            except Exception:
                pass

        for rule_name, rule_config in complex_image_rules:
            pre_actions = self._process_config_to_actions(rule_config.get("combo"))
            if not pre_actions: continue
            
            for key, delay_ms in pre_actions:
                self.app.key_sender.send_key(key)
                if delay_ms > 0: time.sleep(delay_ms / 1000.0)
            
            time.sleep(0.0001)
            
            if self._check_image_condition(rule_config):
                post_actions = self._process_config_to_actions(rule_config.get("combo_post"))
                if post_actions:
                    return post_actions, f"{rule_name} (Sau ĐK)"
        
        return None, None

    def _check_image_condition(self, rule_config):
        template_b64 = rule_config.get("template_image_b64")
        region = rule_config.get("monitor_region")
        confidence_str = rule_config.get("confidence", "80")

        if not template_b64 or not isinstance(region, tuple):
            return False
            
        try:
            confidence = float(confidence_str) / 100.0
        except (ValueError, TypeError):
            confidence = 0.8
        
        template_cv = self.template_cache.get(template_b64)
        
        if template_cv is None:
            try:
                template_pil = base64_to_image(template_b64)
                if template_pil is None: return False
                template_cv = cv2.cvtColor(np.array(template_pil), cv2.COLOR_RGB2BGR)
                self.template_cache[template_b64] = template_cv
            except Exception as e:
                self.app.trang_chu_tab.log_message(f"Lỗi chuyển đổi ảnh mẫu: {e}")
                return False

        try:
            match_location = self.image_recognizer.find_image(template_cv, region, confidence)
            return match_location is not None
        except Exception as e:
            self.app.trang_chu_tab.log_message(f"Lỗi DXcam khi kiểm tra ảnh: {e}")
            return False

    def get_current_hp_percentage(self, hp_config):
        region = hp_config.get("hp_bar_region_manual")
        color_library = hp_config.get("hp_color_library_manual", [])

        if not region or not color_library:
            return None

        try:
            bar_image = ImageGrab.grab(bbox=region)
            bar_np = np.array(bar_image.convert("RGB"))
            bar_height, bar_width, _ = bar_np.shape
            
            if bar_width == 0: return 0

            horizontal_sample_points = max(1, bar_width // 10)
            vertical_sample_indices = [int(bar_height * 0.25), int(bar_height * 0.5), int(bar_height * 0.75)]
            filled_width = 0
            tolerance = int(hp_config.get("tolerance", 15))
            rgb_color_library = [_hex_to_rgb(c) for c in color_library]
            
            for x in range(bar_width - 1, -1, -1):
                if x % horizontal_sample_points == 0 or x == bar_width - 1:
                    match_count = 0
                    for y in vertical_sample_indices:
                        pixel_rgb = bar_np[y, x]
                        if any(_are_colors_similar(pixel_rgb, hp_color, tolerance) for hp_color in rgb_color_library):
                            match_count += 1
                    if match_count >= 2:
                        filled_width = x + 1
                        break 
            
            return (filled_width / bar_width) * 100
        except Exception as e:
            self.app.trang_chu_tab.log_message(f"Lỗi nhận diện HP: {e}")
            return None

    def _check_hp_threshold_condition(self, hp_config):
        current_hp = self.get_current_hp_percentage(hp_config)
        if current_hp is None: return False
        try:
            threshold = int(hp_config.get("threshold", 30))
            return current_hp < threshold
        except (ValueError, TypeError):
            return False
