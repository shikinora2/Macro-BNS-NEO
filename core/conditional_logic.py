# core/conditional_logic.py
import cv2
import numpy as np
from PIL import ImageGrab
import time

from .utils import _hex_to_rgb, _are_colors_similar, base64_to_image

class ConditionalLogicHandler:
    def __init__(self, app_instance):
        self.app = app_instance

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
        """
        Quét các quy tắc và trả về một tập hợp (set) các phím bị vô hiệu hóa.
        """
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

    def check_for_sub_combo(self, sub_combo_full_config):
        # Thứ tự ưu tiên: HP > Mana > Skill > Crit
        
        # 1. Kiểm tra điều kiện HP
        hp_config = sub_combo_full_config.get("hp", {})
        if hp_config.get("enabled") == "on":
            if self._check_hp_threshold_condition(hp_config):
                actions = self._process_config_to_actions(hp_config.get("combo"))
                if actions:
                    return actions, f"HP (dưới {hp_config.get('threshold')}%)"

        # 2. Kiểm tra điều kiện Mana
        mana_config = sub_combo_full_config.get("mana", {})
        if mana_config.get("enabled") == "on":
            if self._check_mana_threshold_condition(mana_config):
                actions = self._process_config_to_actions(mana_config.get("combo"))
                if actions:
                    return actions, f"Mana (dưới {mana_config.get('threshold')})"

        # 3. Kiểm tra điều kiện Skill và Crit (dựa trên hình ảnh)
        image_based_rules = {
            "Skill": sub_combo_full_config.get("skill", {}),
            "Crit": sub_combo_full_config.get("crit", {})
        }
        for rule_name, rule_set in image_based_rules.items():
            for i, rule_config in enumerate(rule_set.get("rules", [])):
                is_enabled = rule_config.get("enabled") == "on"
                is_activate_rule = rule_config.get("rule_type") == "Kích hoạt Combo"
                
                if not (is_enabled and is_activate_rule):
                    continue

                logic_order = rule_config.get("logic_order")
                
                if logic_order == "Kiểm tra điều kiện rồi sử dụng Skill":
                    if self._check_image_condition(rule_config):
                        actions = self._process_config_to_actions(rule_config.get("combo"))
                        if actions:
                            return actions, f"{rule_name} #{i+1}"
                
                elif logic_order == "Sử dụng Skill rồi kiểm tra điều kiện":
                    pre_actions = self._process_config_to_actions(rule_config.get("combo"))
                    if not pre_actions: continue

                    # Thực thi combo "trước"
                    for key, delay_ms in pre_actions:
                        self.app.key_sender.send_key(key)
                        if delay_ms > 0: time.sleep(delay_ms / 1000.0)
                    
                    # Đợi một chút để game cập nhật giao diện
                    time.sleep(0.1) 

                    # Kiểm tra điều kiện
                    if self._check_image_condition(rule_config):
                        post_actions = self._process_config_to_actions(rule_config.get("combo_post"))
                        if post_actions:
                            return post_actions, f"{rule_name} #{i+1} (Sau ĐK)"
        
        return None, None

    def _check_image_condition(self, rule_config):
        # ... (logic không đổi)
        template_b64 = rule_config.get("template_image_b64")
        region = rule_config.get("monitor_region")
        confidence_str = rule_config.get("confidence", "80")

        if not template_b64 or not isinstance(region, tuple):
            return False
            
        try:
            confidence = float(confidence_str) / 100.0
        except (ValueError, TypeError):
            confidence = 0.8

        try:
            template_img = base64_to_image(template_b64)
            if template_img is None: return False
            
            screenshot = ImageGrab.grab(bbox=region)
            if template_img.width > screenshot.width or template_img.height > screenshot.height:
                return False

            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            template_cv = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2GRAY)

            result = cv2.matchTemplate(screenshot_cv, template_cv, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            return max_val >= confidence
        except Exception as e:
            self.app.root.after(0, self.app.home_tab.log_message, f"Lỗi kiểm tra ảnh: {e}")
            return False

    def get_current_hp_percentage(self, hp_config):
        # ... (logic không đổi)
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
        # ... (logic không đổi)
        current_hp = self.get_current_hp_percentage(hp_config)
        if current_hp is None: return False
        try:
            threshold = int(hp_config.get("threshold", 30))
            return current_hp < threshold
        except (ValueError, TypeError):
            return False

    def _check_mana_threshold_condition(self, mana_config):
        # ... (logic không đổi)
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

