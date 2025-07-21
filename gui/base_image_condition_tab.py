# Tệp: gui/base_image_condition_tab.py
#
# PHIÊN BẢN TỐI ƯU HÓA GIAO DIỆN
# - Giao diện được thiết kế lại để gọn gàng, co giãn tốt hơn.
# - Sử dụng .grid() một cách nhất quán để quản lý layout.

import customtkinter as ctk
from core.utils import image_to_base64, base64_to_image
from .image_logic_mixin import ImageLogicMixin
from .base_rule_tab import BaseRuleTab
from .constants import KEY_OPTIONS

class BaseImageConditionTab(BaseRuleTab):
    def __init__(self, master, app, tab_name="Quy tắc", **kwargs):
        super().__init__(master, app, tab_name, **kwargs)
        self.image_handler = ImageLogicMixin(self.app)

    def _create_single_panel(self, parent, panel_id, config):
        """Tạo một panel quy tắc với layout đã được tối ưu."""
        section_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray25")
        section_frame.pack(fill="x", expand=True, padx=5, pady=5)
        
        panel_data = {
            'var': ctk.StringVar(value=config.get("enabled", "on")),
            'rule_type': ctk.StringVar(value=config.get("rule_type", "Kích hoạt Combo")),
            'logic_order': ctk.StringVar(value=config.get("logic_order", "Kiểm tra điều kiện rồi sử dụng Skill")),
            'disabled_key': ctk.StringVar(value=config.get("disabled_key", "")),
            'template_image': base64_to_image(config.get("template_image_b64")),
            'monitor_region': tuple(config.get("monitor_region")) if isinstance(config.get("monitor_region"), list) else config.get("monitor_region", "Chưa có"),
            'confidence': ctk.StringVar(value=config.get("confidence", "80")),
            'skill_rows': [],
            'skill_rows_post': []
        }
        
        # --- Khung tiêu đề ---
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(title_frame, text=f"{self.tab_name} #{self.panel_count}", font=ctk.CTkFont(weight="bold")).pack(side="left", expand=True, anchor="w")
        ctk.CTkCheckBox(title_frame, text="Bật", variable=panel_data["var"], onvalue="on", offvalue="off").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="Xóa Quy Tắc", width=100, fg_color="#c95151", command=lambda: self._remove_panel(panel_id)).pack(side="right")

        # --- Khung nội dung chính (sử dụng grid) ---
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=3) # Cột Hành động
        content_frame.grid_columnconfigure(1, weight=4) # Cột Điều kiện
        content_frame.grid_rowconfigure(0, weight=1)

        # Tạo và đặt các khung con vào grid
        action_panel = self._create_action_panel(content_frame, panel_id, panel_data, config)
        condition_panel = self._create_condition_panel(content_frame, panel_id, panel_data)
        
        action_panel.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        condition_panel.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")

        self._update_panel_ui(panel_data)

        return section_frame, panel_data

    def _update_panel_ui(self, panel_data):
        """Cập nhật hiển thị của các thành phần dựa trên lựa chọn."""
        rule_type = panel_data['rule_type'].get()
        logic_order = panel_data['logic_order'].get()

        # Sử dụng grid_remove() và grid() để ẩn/hiện các frame
        if rule_type == "Kích hoạt Combo":
            panel_data['logic_order_combo_frame'].grid()
            panel_data['disabled_key_frame'].grid_remove()
            panel_data['action_frame_pre'].grid()
            
            if logic_order == "Sử dụng Skill rồi kiểm tra điều kiện":
                panel_data['action_frame_post'].grid()
                panel_data['action_title_pre'].configure(text="Hành động Trước ĐK:")
            else:
                panel_data['action_frame_post'].grid_remove()
                panel_data['action_title_pre'].configure(text="Hành động (Combo):")
        
        elif rule_type == "Vô hiệu hóa phím":
            panel_data['logic_order_combo_frame'].grid_remove()
            panel_data['action_frame_pre'].grid_remove()
            panel_data['action_frame_post'].grid_remove()
            panel_data['disabled_key_frame'].grid()

    def _create_action_panel(self, parent, panel_id, panel_data, config):
        """Tạo khung chứa các thiết lập về 'Hành động'."""
        action_section_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray40")
        action_section_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(action_section_frame, text="Hành động", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(5,10))
        
        ctk.CTkLabel(action_section_frame, text="Loại quy tắc:").grid(row=1, column=0, sticky="w", padx=10, pady=(5,0))
        rule_type_options = ["Kích hoạt Combo", "Vô hiệu hóa phím"]
        ctk.CTkComboBox(action_section_frame, values=rule_type_options,
                        variable=panel_data['rule_type'], state="readonly",
                        command=lambda choice: self._update_panel_ui(panel_data)).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Frame cho logic order
        panel_data['logic_order_combo_frame'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        panel_data['logic_order_combo_frame'].grid(row=3, column=0, sticky="ew", padx=5)
        panel_data['logic_order_combo_frame'].grid_columnconfigure(0, weight=1)
        logic_options = ["Kiểm tra điều kiện rồi sử dụng Skill", "Sử dụng Skill rồi kiểm tra điều kiện"]
        panel_data['logic_order_combo'] = ctk.CTkComboBox(panel_data['logic_order_combo_frame'], values=logic_options,
                                        variable=panel_data['logic_order'], state="readonly",
                                        command=lambda choice: self._update_panel_ui(panel_data))
        panel_data['logic_order_combo'].pack(fill="x", expand=True)

        # Frame cho combo trước điều kiện
        panel_data['action_frame_pre'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        panel_data['action_frame_pre'].grid(row=4, column=0, sticky="ew", pady=5, padx=5)
        skill_title_frame_pre = ctk.CTkFrame(panel_data['action_frame_pre'], fg_color="transparent")
        skill_title_frame_pre.pack(fill="x", pady=(5, 0))
        panel_data['action_title_pre'] = ctk.CTkLabel(skill_title_frame_pre, text="Hành động (Combo):", font=ctk.CTkFont(weight="bold"))
        panel_data['action_title_pre'].pack(side="left")
        ctk.CTkButton(skill_title_frame_pre, text="(+)", width=30, height=20, command=lambda: self._add_skill_row(skills_container_pre, panel_data['skill_rows'])).pack(side="left", padx=5)
        skills_container_pre = ctk.CTkScrollableFrame(panel_data['action_frame_pre'], label_text="", fg_color="transparent")
        skills_container_pre.pack(fill="both", expand=True, pady=(0,5))

        # Frame cho combo sau điều kiện
        panel_data['action_frame_post'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        panel_data['action_frame_post'].grid(row=5, column=0, sticky="ew", pady=5, padx=5)
        skill_title_frame_post = ctk.CTkFrame(panel_data['action_frame_post'], fg_color="transparent")
        skill_title_frame_post.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(skill_title_frame_post, text="Hành động Sau ĐK:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(skill_title_frame_post, text="(+)", width=30, height=20, command=lambda: self._add_skill_row(skills_container_post, panel_data['skill_rows_post'])).pack(side="left", padx=5)
        skills_container_post = ctk.CTkScrollableFrame(panel_data['action_frame_post'], label_text="", fg_color="transparent")
        skills_container_post.pack(fill="both", expand=True, pady=(0,5))

        # Frame cho phím bị vô hiệu hóa
        panel_data['disabled_key_frame'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        panel_data['disabled_key_frame'].grid(row=6, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(panel_data['disabled_key_frame'], text="Phím bị vô hiệu hóa:").pack(side="left", padx=(0,5))
        ctk.CTkComboBox(panel_data['disabled_key_frame'], values=KEY_OPTIONS, width=90, variable=panel_data['disabled_key']).pack(side="left")

        # Tải cấu hình
        combo_pre = config.get("combo", [])
        if not combo_pre: self._add_skill_row(skills_container_pre, panel_data['skill_rows'])
        else:
            for skill in combo_pre: self._add_skill_row(skills_container_pre, panel_data['skill_rows'], key=skill.get("key", ""), delay=skill.get("delay", ""))
        
        combo_post = config.get("combo_post", [])
        if not combo_post: self._add_skill_row(skills_container_post, panel_data['skill_rows_post'])
        else:
            for skill in combo_post: self._add_skill_row(skills_container_post, panel_data['skill_rows_post'], key=skill.get("key", ""), delay=skill.get("delay", ""))
        
        return action_section_frame

    def _create_condition_panel(self, parent, panel_id, panel_data):
        """Tạo khung chứa các thiết lập về 'Điều kiện'."""
        condition_section_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray40")
        condition_section_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(condition_section_frame, text="Điều kiện (Nhận diện ảnh)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5,10), sticky="w")
        
        # --- Ảnh mẫu và các nút điều khiển ---
        image_frame = ctk.CTkFrame(condition_section_frame, fg_color="transparent")
        image_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        image_frame.grid_columnconfigure(0, weight=1)
        
        panel_data["img_label"] = ctk.CTkLabel(image_frame, text="Chưa có ảnh mẫu", fg_color="gray20", corner_radius=6)
        panel_data["img_label"].configure(height=120) # Chiều cao cố định để gọn hơn
        panel_data["img_label"].grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,5))
        
        ctk.CTkButton(image_frame, text="Chụp ảnh", command=lambda pd=panel_data: self.image_handler.get_template_image(panel_id, pd)).grid(row=1, column=0, padx=(0,2), sticky="ew")
        ctk.CTkButton(image_frame, text="Tải ảnh", command=lambda pd=panel_data: self.image_handler.load_template_image(panel_id, pd)).grid(row=1, column=1, padx=(2,0), sticky="ew")
        
        if panel_data["template_image"]:
            self.image_handler.update_template_image(panel_data, panel_data["template_image"])

        # --- Các thiết lập khác ---
        ctk.CTkLabel(condition_section_frame, text="Vùng giám sát:").grid(row=2, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
        region_frame = ctk.CTkFrame(condition_section_frame, fg_color="transparent")
        region_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,5), sticky="ew")
        region_text = str(panel_data["monitor_region"]) if panel_data["monitor_region"] != "Chưa có" else "Chưa có"
        panel_data["monitor_label"] = ctk.CTkLabel(region_frame, text=region_text, wraplength=180, justify="left")
        panel_data["monitor_label"].pack(side="left", fill="x", expand=True)
        ctk.CTkButton(region_frame, text="Chọn", width=60, command=lambda pd=panel_data: self.image_handler.get_monitor_region(pd)).pack(side="right")

        ctk.CTkLabel(condition_section_frame, text="Ngưỡng chính xác (%):").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(condition_section_frame, textvariable=panel_data["confidence"]).grid(row=4, column=1, padx=10, pady=5, sticky="e")
        
        ctk.CTkButton(condition_section_frame, text="Kiểm tra nhận diện", fg_color="#5bc0de", command=lambda pd=panel_data: self.image_handler.test_image_match(pd)).grid(row=5, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="ew")

        return condition_section_frame

    def get_config(self):
        config_data = {"rules": []}
        for panel in self.panels:
            data = panel['data']
            
            combo = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in data['skill_rows'] if r['key'].get()]
            combo_post = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in data['skill_rows_post'] if r['key'].get()]

            rule = {
                "enabled": data["var"].get(),
                "rule_type": data["rule_type"].get(),
                "logic_order": data["logic_order"].get(),
                "disabled_key": data["disabled_key"].get(),
                "combo": combo,
                "combo_post": combo_post,
                "template_image_b64": image_to_base64(data.get("template_image")),
                "monitor_region": data.get("monitor_region"),
                "confidence": data.get("confidence").get(),
            }
            config_data["rules"].append(rule)
        return config_data
