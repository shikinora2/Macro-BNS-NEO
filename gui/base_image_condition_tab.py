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
        section_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray25")
        section_frame.pack(fill="x", expand=False, padx=5, pady=5)
        
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
        
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(title_frame, text=f"{self.tab_name} #{self.panel_count}", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkCheckBox(title_frame, text="Bật", variable=panel_data["var"], onvalue="on", offvalue="off").pack(side="right", padx=(10,0))
        ctk.CTkButton(title_frame, text="Xóa Quy Tắc", width=80, fg_color="#c95151", command=lambda: self._remove_panel(panel_id)).pack(side="right")

        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=5, pady=5)
        content_frame.grid_columnconfigure(1, weight=1)

        self._create_action_panel(content_frame, panel_id, panel_data, config)
        self._create_condition_panel(content_frame, panel_id, panel_data)

        self._update_panel_ui(panel_data)

        return section_frame, panel_data

    def _update_panel_ui(self, panel_data):
        rule_type = panel_data['rule_type'].get()
        logic_order = panel_data['logic_order'].get()

        if rule_type == "Kích hoạt Combo":
            panel_data['logic_order_combo'].grid()
            panel_data['disabled_key_frame'].grid_remove()
            panel_data['action_frame_pre'].grid()
            
            if logic_order == "Sử dụng Skill rồi kiểm tra điều kiện":
                panel_data['action_frame_post'].grid()
                panel_data['action_title_pre'].configure(text="Hành động Trước điều kiện:")
            else:
                panel_data['action_frame_post'].grid_remove()
                panel_data['action_title_pre'].configure(text="Hành động (Combo):")
        
        elif rule_type == "Vô hiệu hóa phím":
            panel_data['logic_order_combo'].grid_remove()
            panel_data['action_frame_pre'].grid_remove()
            panel_data['action_frame_post'].grid_remove()
            panel_data['disabled_key_frame'].grid()

    def _create_action_panel(self, parent, panel_id, panel_data, config):
        action_section_frame = ctk.CTkFrame(parent)
        action_section_frame.grid(row=0, column=0, padx=(5, 10), pady=5, sticky="new")
        
        ctk.CTkLabel(action_section_frame, text="Hành động", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(0,5))
        
        ctk.CTkLabel(action_section_frame, text="Loại quy tắc:").pack(anchor="w", padx=5, pady=(5,0))
        rule_type_options = ["Kích hoạt Combo", "Vô hiệu hóa phím"]
        ctk.CTkComboBox(action_section_frame, values=rule_type_options, 
                        variable=panel_data['rule_type'], state="readonly",
                        command=lambda choice: self._update_panel_ui(panel_data)).pack(fill="x", padx=5, pady=(0, 10))
        ctk.CTkLabel(action_section_frame, text="Chọn loại quy tắc để áp dụng", wraplength=100, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=2)

        logic_options = ["Kiểm tra điều kiện rồi sử dụng Skill", "Sử dụng Skill rồi kiểm tra điều kiện"]
        panel_data['logic_order_combo'] = ctk.CTkComboBox(action_section_frame, values=logic_options, 
                        variable=panel_data['logic_order'], state="readonly",
                        command=lambda choice: self._update_panel_ui(panel_data))
        ctk.CTkLabel(action_section_frame, text="Chọn thứ tự thực hiện hành động và điều kiện", wraplength=100, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=2)

        panel_data['action_frame_pre'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        skill_title_frame_pre = ctk.CTkFrame(panel_data['action_frame_pre'], fg_color="transparent")
        skill_title_frame_pre.pack(fill="x", padx=5, pady=(5, 0))
        panel_data['action_title_pre'] = ctk.CTkLabel(skill_title_frame_pre, text="Hành động (Combo):", font=ctk.CTkFont(weight="bold"))
        panel_data['action_title_pre'].pack(side="left")
        ctk.CTkButton(skill_title_frame_pre, text="(+) Thêm", width=60, height=20, 
                      command=lambda: self._add_skill_row(skills_container_pre, panel_data['skill_rows'])).pack(side="left", padx=10)
        ctk.CTkLabel(skill_title_frame_pre, text="Thêm phím vào combo", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
        skills_container_pre = ctk.CTkFrame(panel_data['action_frame_pre'], fg_color="transparent")
        skills_container_pre.pack(fill="x", expand=True)

        panel_data['action_frame_post'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        skill_title_frame_post = ctk.CTkFrame(panel_data['action_frame_post'], fg_color="transparent")
        skill_title_frame_post.pack(fill="x", padx=5, pady=(5, 0))
        ctk.CTkLabel(skill_title_frame_post, text="Hành động Sau điều kiện:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(skill_title_frame_post, text="(+) Thêm", width=60, height=20, 
                      command=lambda: self._add_skill_row(skills_container_post, panel_data['skill_rows_post'])).pack(side="left", padx=10)
        ctk.CTkLabel(skill_title_frame_post, text="Thêm phím vào combo sau điều kiện", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
        skills_container_post = ctk.CTkFrame(panel_data['action_frame_post'], fg_color="transparent")
        skills_container_post.pack(fill="x", expand=True)

        panel_data['disabled_key_frame'] = ctk.CTkFrame(action_section_frame, fg_color="transparent")
        ctk.CTkLabel(panel_data['disabled_key_frame'], text="Phím bị vô hiệu hóa:").pack(side="left", padx=(5,5))
        ctk.CTkComboBox(panel_data['disabled_key_frame'], values=KEY_OPTIONS, width=90, variable=panel_data['disabled_key']).pack(side="left")
        ctk.CTkLabel(panel_data['disabled_key_frame'], text="Chọn phím để vô hiệu hóa", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)

        combo_pre = config.get("combo", [])
        if not combo_pre: 
            self._add_skill_row(skills_container_pre, panel_data['skill_rows'])
        else:
            for skill in combo_pre:
                self._add_skill_row(skills_container_pre, panel_data['skill_rows'], key=skill.get("key", ""), delay=skill.get("delay", ""))
        
        combo_post = config.get("combo_post", [])
        if not combo_post: 
            self._add_skill_row(skills_container_post, panel_data['skill_rows_post'])
        else:
            for skill in combo_post:
                self._add_skill_row(skills_container_post, panel_data['skill_rows_post'], key=skill.get("key", ""), delay=skill.get("delay", ""))

    def _create_condition_panel(self, parent, panel_id, panel_data):
        condition_section_frame = ctk.CTkFrame(parent)
        condition_section_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        condition_section_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(condition_section_frame, text="Điều kiện (Nhận diện ảnh)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        region_frame = ctk.CTkFrame(condition_section_frame, fg_color="transparent")
        region_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        ctk.CTkButton(region_frame, text="Chọn Vùng giám sát", command=lambda pd=panel_data: self.image_handler.get_monitor_region(pd)).pack(side="left")
        ctk.CTkLabel(region_frame, text="Chọn khu vực trên màn hình để giám sát", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
        
        region_text = str(panel_data["monitor_region"]) if panel_data["monitor_region"] != "Chưa có" else "Chưa có"
        panel_data["monitor_label"] = ctk.CTkLabel(region_frame, text=region_text, wraplength=150)
        panel_data["monitor_label"].pack(side="left", padx=10)

        image_frame = ctk.CTkFrame(condition_section_frame)
        image_frame.grid(row=2, column=0, pady=10, sticky="ns")
        
        panel_data["img_label"] = ctk.CTkLabel(image_frame, text="Chưa có ảnh mẫu", fg_color="gray20", corner_radius=6)
        panel_data["img_label"].configure(width=int(self.app.root.winfo_screenwidth() * 0.1), height=int(self.app.root.winfo_screenheight() * 0.1))
        panel_data["img_label"].pack(pady=5, padx=5)
        
        image_buttons_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        image_buttons_frame.pack(pady=5, padx=5, fill="x")
        ctk.CTkButton(image_buttons_frame, text="Chụp ảnh", command=lambda pd=panel_data: self.image_handler.get_template_image(panel_id, pd)).pack(side="left", expand=True, padx=2)
        ctk.CTkLabel(image_buttons_frame, text="Chụp ảnh từ màn hình", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=2)
        ctk.CTkButton(image_buttons_frame, text="Tải ảnh", command=lambda pd=panel_data: self.image_handler.load_template_image(panel_id, pd)).pack(side="left", expand=True, padx=2)
        ctk.CTkLabel(image_buttons_frame, text="Tải ảnh từ file", wraplength=100, font=ctk.CTkFont(size=10)).pack(side="left", padx=2)
        
        if panel_data["template_image"]:
            self.image_handler.update_template_image(panel_data, panel_data["template_image"])

        controls_frame = ctk.CTkFrame(condition_section_frame, fg_color="transparent")
        controls_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        controls_frame.grid_columnconfigure(1, weight=1)

        # Đảm bảo nút "Ngưỡng chính xác (%)" và "Kiểm tra nhận diện" luôn hiển thị
        ctk.CTkLabel(controls_frame, text="Ngưỡng chính xác (%):").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        ctk.CTkEntry(controls_frame, textvariable=panel_data["confidence"]).grid(row=0, column=1, pady=5, sticky="ew")
        ctk.CTkLabel(controls_frame, text="Đặt mức độ chính xác nhận diện ảnh", wraplength=100, font=ctk.CTkFont(size=10)).grid(row=1, column=0, columnspan=2, pady=2)
        
        ctk.CTkButton(controls_frame, text="Kiểm tra nhận diện", fg_color="#5bc0de", command=lambda pd=panel_data: self.image_handler.test_image_match(pd)).grid(row=2, column=0, columnspan=2, pady=(20, 5), sticky="ew")
        ctk.CTkLabel(controls_frame, text="Kiểm tra khả năng nhận diện ảnh mẫu", wraplength=100, font=ctk.CTkFont(size=10)).grid(row=3, column=0, columnspan=2, pady=2)

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