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
        # Executor để chạy các tác vụ kiểm tra ảnh song song, giới hạn 10 luồng cùng lúc
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix='ImageCheck')

    def shutdown_executor(self):
        """Dọn dẹp và tắt ThreadPoolExecutor khi ứng dụng thoát."""
        print("Shutting down image checking thread pool...")
        # Tắt executor, không chờ các luồng hoàn thành và cố gắng hủy chúng
        self.executor.shutdown(wait=False, cancel_futures=True)

    def clear_template_cache(self):
        """Xóa bộ đệm ảnh mẫu khi tải cấu hình mới."""
        self.template_cache.clear()
        self.app.home_tab.log_message("Đã xóa cache ảnh mẫu.")

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
        """Quét các quy tắc và trả về một tập hợp (set) các phím bị vô hiệu hóa."""
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
        """Hàm tác vụ để kiểm tra một quy tắc ảnh, được thiết kế để chạy trong một luồng."""
        if self._check_image_condition(rule_config):
            actions = self._process_config_to_actions(rule_config.get("combo"))
            if actions:
                return actions, rule_name
        return None, None

    def check_for_sub_combo(self, sub_combo_full_config):
        """
        Kiểm tra các điều kiện combo phụ theo thứ tự ưu tiên:
        1. HP (tuần tự)
        2. Mana (tuần tự)
        3. Các quy tắc ảnh đơn giản (Skill, Crit) - kiểm tra song song
        4. Các quy tắc ảnh phức tạp ("act-then-check") - kiểm tra tuần tự
        """
        # Ưu tiên 1 & 2: Kiểm tra HP và Mana tuần tự vì chúng nhanh và quan trọng nhất
        hp_config = sub_combo_full_config.get("hp", {})
        if hp_config.get("enabled") == "on" and self._check_hp_threshold_condition(hp_config):
            actions = self._process_config_to_actions(hp_config.get("combo"))
            if actions: return actions, f"HP (dưới {hp_config.get('threshold')}%)"

        mana_config = sub_combo_full_config.get("mana", {})
        if mana_config.get("enabled") == "on" and self._check_mana_threshold_condition(mana_config):
            actions = self._process_config_to_actions(mana_config.get("combo"))
            if actions: return actions, f"Mana (dưới {mana_config.get('threshold')})"

        # Phân loại các quy tắc ảnh để xử lý
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

        # Ưu tiên 3: Kiểm tra song song các quy tắc ảnh đơn giản
        if simple_image_rules:
            future_to_rule = {self.executor.submit(self._check_image_rule_task, name, config): (name, config) for name, config in simple_image_rules}
            try:
                # Lấy kết quả của luồng nào hoàn thành trước
                for future in concurrent.futures.as_completed(future_to_rule):
                    actions, name = future.result()
                    if actions:
                        # Nếu tìm thấy, hủy các luồng khác và trả về kết quả ngay lập tức
                        for f in future_to_rule: f.cancel()
                        return actions, name
            except Exception:
                # Lỗi có thể xảy ra nếu cửa sổ đóng khi đang kiểm tra, bỏ qua
                pass

        # Ưu tiên 4: Kiểm tra tuần tự các quy tắc phức tạp ("act-then-check")
        # Chỉ chạy nếu không có quy tắc đơn giản nào khớp
        for rule_name, rule_config in complex_image_rules:
            pre_actions = self._process_config_to_actions(rule_config.get("combo"))
            if not pre_actions: continue
            
            # Thực thi hành động trước ngay tại đây
            for key, delay_ms in pre_actions:
                self.app.key_sender.send_key(key)
                if delay_ms > 0: time.sleep(delay_ms / 1000.0)
            
            time.sleep(0.0001) # Chờ game cập nhật giao diện
            
            # Sau đó kiểm tra điều kiện
            if self._check_image_condition(rule_config):
                post_actions = self._process_config_to_actions(rule_config.get("combo_post"))
                if post_actions:
                    # Nếu điều kiện đúng, trả về combo sau điều kiện
                    return post_actions, f"{rule_name} (Sau ĐK)"
        
        # Nếu không có quy tắc nào khớp, trả về None để chạy combo chính
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
                self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi chuyển đổi ảnh mẫu: {e}")
                return False

        try:
            match_location = self.image_recognizer.find_image(template_cv, region, confidence)
            return match_location is not None
        except Exception as e:
            self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi DXcam khi kiểm tra ảnh: {e}")
            return False

    def get_current_hp_percentage(self, hp_config):
        mode = self.app.settings_tab.detection_mode_var.get()
        
        if mode == "Tự động (Profile)":
            region = self.app.layout_manager.get_located_region('HP_BAR_AREA')
            profile_data = self.app.layout_manager.active_profile_data.get('HP_BAR_AREA', {})
            color_library = profile_data.get('hp_color_library', [])
        else: # Chế độ Thủ công
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
            self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi nhận diện HP: {e}")
            return None

    def _check_hp_threshold_condition(self, hp_config):
        current_hp = self.get_current_hp_percentage(hp_config)
        if current_hp is None: return False
        try:
            threshold = int(hp_config.get("threshold", 30))
            return current_hp < threshold
        except (ValueError, TypeError):
            return False

    def _check_mana_threshold_condition(self, mana_config):
        mode = self.app.settings_tab.detection_mode_var.get()
        
        try:
            threshold = int(mana_config.get("threshold", 1))
            
            if mode == "Tự động (Profile)":
                mana_area_coords = self.app.layout_manager.get_located_region('MANA_ORBS_AREA')
                if not mana_area_coords: return False
                profile_data = self.app.layout_manager.active_profile_data.get('MANA_ORBS_AREA', {})
                relative_orb_coords = profile_data.get('relative_orb_coords', [])
                color_library = profile_data.get('mana_color_library', [])
                if not relative_orb_coords or not color_library: return False
                relative_coord = relative_orb_coords[threshold - 1]
                absolute_coord = (mana_area_coords[0] + relative_coord[0], mana_area_coords[1] + relative_coord[1])
            else: # Chế độ Thủ công
                mana_coords = mana_config.get("mana_coords_manual", [])
                color_library = mana_config.get("mana_color_library_manual", [])
                if not mana_coords or not color_library: return False
                absolute_coord = mana_coords[threshold - 1]['coord']

            tolerance = int(mana_config.get("tolerance", 10))
            rgb_color_library = [_hex_to_rgb(c) for c in color_library]
            
            pixel_color_rgb = ImageGrab.grab(bbox=(absolute_coord[0], absolute_coord[1], absolute_coord[0] + 1, absolute_coord[1] + 1)).getpixel((0, 0))
            
            is_a_match = any(_are_colors_similar(pixel_color_rgb, mana_color, tolerance) for mana_color in rgb_color_library)
            return not is_a_match
        except (IndexError, ValueError, OSError, TypeError) as e:
            self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi nhận diện Mana: {e}")
            return False
