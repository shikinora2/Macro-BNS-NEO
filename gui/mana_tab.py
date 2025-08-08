# gui/mana_tab.py
import customtkinter as ctk
from .constants import KEY_OPTIONS, MANA_ORBS_COORDS, DEFAULT_MANA_COLOR_LIBRARY
from .better_scrollable_frame import BetterScrollableFrame
from core.pickers import ScreenPicker
import ast

class ManaTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.mana_rules_ui = {}
        
        self.detection_coords = [d.copy() for d in MANA_ORBS_COORDS]
        self.detection_color_library_on = DEFAULT_MANA_COLOR_LIBRARY[:]
        self.detection_color_library_off = ["#474747", "#363636"] 
        self.tolerance_var = ctk.StringVar(value="10")
        
        main_tab_view = ctk.CTkTabview(self)
        main_tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        
        rules_tab = main_tab_view.add("Quy tắc Combo")
        detection_tab = main_tab_view.add("Cài đặt Nhận diện")

        self._create_rules_tab(rules_tab)
        self._create_detection_settings_ui(detection_tab)

    def _create_rules_tab(self, parent_tab):
        orb_selector_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        orb_selector_frame.pack(fill="x", pady=(10, 5), padx=10)
        
        ctk.CTkLabel(orb_selector_frame, text="Chọn mức Mana để cấu hình:").pack(side="left", padx=(0, 15))

        self.selected_orb_var = ctk.StringVar(value="10")
        orb_values = [str(i) for i in range(1, 11)]
        orb_selector = ctk.CTkSegmentedButton(
            orb_selector_frame, 
            values=orb_values,
            variable=self.selected_orb_var,
            command=self._on_orb_selected
        )
        orb_selector.pack(fill="x", expand=True)

        self.config_container = ctk.CTkFrame(parent_tab, fg_color="transparent")
        self.config_container.pack(fill="x", pady=5, padx=5, anchor="n")

        for i in range(1, 11):
            panel = self._create_single_config_panel(self.config_container, level=i)
            self.mana_rules_ui[i] = panel
        
        self._show_config_for_level(10)

    def _create_single_config_panel(self, parent, level):
        panel_frame = ctk.CTkFrame(parent, border_width=1, border_color="gray25")
        
        rule_data = {
            "panel": panel_frame,
            "level": level,
            "enabled_var": ctk.StringVar(value="off"),
            "skill_rows": []
        }

        title_frame = ctk.CTkFrame(panel_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text=f"Khi Mana còn {level}", font=ctk.CTkFont(weight="bold", size=14)).pack(side="left")
        ctk.CTkCheckBox(title_frame, text="Bật quy tắc", variable=rule_data["enabled_var"], onvalue="on", offvalue="off").pack(side="right")

        action_frame = ctk.CTkFrame(panel_frame, fg_color="transparent")
        action_frame.pack(fill="x", expand=True, padx=10, pady=(0, 10))

        skill_title_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        skill_title_frame.pack(fill="x")
        ctk.CTkLabel(skill_title_frame, text="Combo sử dụng:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        skills_container = BetterScrollableFrame(action_frame, fg_color="transparent", height=135)
        skills_container.pack(fill="x", pady=(5,0))
        
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, 
                      command=lambda s=skills_container, r=rule_data['skill_rows']: self._add_skill_row(s, r)).pack(side="left", padx=10)

        self._add_skill_row(skills_container, rule_data['skill_rows'])
        
        rule_data["skills_container"] = skills_container
        return rule_data

    def _on_orb_selected(self, selected_level_str):
        level = int(selected_level_str)
        self._show_config_for_level(level)

    def _show_config_for_level(self, level_to_show):
        for level, ui_data in self.mana_rules_ui.items():
            if level == level_to_show:
                ui_data["panel"].pack(fill="x", padx=5, pady=5)
            else:
                ui_data["panel"].pack_forget()

    def _create_detection_settings_ui(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        parent_tab.grid_columnconfigure(1, weight=1)
        
        # --- CỘT TRÁI: TỌA ĐỘ VÀ NÚT KIỂM TRA ---
        coords_frame = ctk.CTkFrame(parent_tab)
        coords_frame.grid(row=0, column=0, padx=(0,5), pady=5, sticky="nsew")
        
        # TỐI ƯU HÓA: Bỏ thanh cuộn, dùng Frame thường và grid layout
        coords_container = ctk.CTkFrame(coords_frame)
        coords_container.pack(fill="x", expand=True, padx=5, pady=5)
        ctk.CTkLabel(coords_container, text="Tọa độ các Orb Mana", font=ctk.CTkFont(weight="bold")).pack(pady=(5,10))

        self.detection_widgets = []
        for i, orb_data in enumerate(self.detection_coords):
            row_frame = ctk.CTkFrame(coords_container)
            row_frame.pack(fill="x", pady=3, padx=5)
            row_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row_frame, text=f"Mana #{orb_data['id']}", width=70).grid(row=0, column=0, padx=5)
            coord_entry = ctk.CTkEntry(row_frame)
            coord_entry.insert(0, str(orb_data['coord']))
            coord_entry.grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkButton(row_frame, text="Lấy tọa độ", width=100, command=lambda idx=i: self._pick_coordinate_for_orb(idx)).grid(row=0, column=2, padx=5)
            self.detection_widgets.append({'coord_entry': coord_entry})
        
        # THÊM MỚI: Nút kiểm tra mana
        ctk.CTkButton(coords_frame, text="Kiểm tra Mana hiện tại", fg_color="#5bc0de", command=self.app.test_current_mana).pack(fill="x", padx=10, pady=10)

        # --- CỘT PHẢI: THƯ VIỆN MÀU VÀ SAI SỐ ---
        colors_tolerance_frame = ctk.CTkFrame(parent_tab)
        colors_tolerance_frame.grid(row=0, column=1, padx=(5,0), pady=5, sticky="nsew")

        color_on_frame = self._create_color_library_frame(colors_tolerance_frame, "Thư viện màu Mana (Khi Đầy)", self.detection_color_library_on)
        color_on_frame.pack(fill="x", expand=True, padx=5, pady=(0, 10))
        
        color_off_frame = self._create_color_library_frame(colors_tolerance_frame, "Thư viện màu Mana (Khi Tắt)", self.detection_color_library_off)
        color_off_frame.pack(fill="x", expand=True, padx=5, pady=5)

        tolerance_frame = ctk.CTkFrame(colors_tolerance_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(15, 5), padx=10)
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)

    def _create_color_library_frame(self, parent, title, color_library):
        frame = ctk.CTkFrame(parent, border_width=1, border_color="gray40")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
        
        swatch_frame = ctk.CTkFrame(frame, fg_color="transparent")
        swatch_frame.pack(pady=5)
        
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(0,10))
        
        ctk.CTkButton(buttons_frame, text="Thêm màu", command=lambda: self._add_color_to_library(color_library, swatch_frame)).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Xóa màu cuối", fg_color="#c95151", command=lambda: self._delete_last_color_from_library(color_library, swatch_frame)).pack(side="left", padx=5)
        
        self._update_color_display(swatch_frame, color_library)
        return frame

    def _pick_coordinate_for_orb(self, index):
        picker = ScreenPicker(self.app.root)
        result = picker.pick_coordinate()
        if result:
            coord_tuple = (result['x'], result['y'])
            self.detection_coords[index]['coord'] = coord_tuple
            self.detection_widgets[index]['coord_entry'].delete(0, 'end')
            self.detection_widgets[index]['coord_entry'].insert(0, str(coord_tuple))

    def _update_color_display(self, swatch_frame, color_library):
        for widget in swatch_frame.winfo_children(): widget.destroy()
        if not color_library:
            ctk.CTkLabel(swatch_frame, text="Thư viện trống", text_color="gray").pack()
        else:
            for color_hex in color_library:
                ctk.CTkLabel(swatch_frame, text="", width=30, height=30, fg_color=color_hex, corner_radius=4).pack(side="left", padx=3)

    def _add_color_to_library(self, color_library, swatch_frame):
        picker = ScreenPicker(self.app.root)
        result = picker.pick_color()
        if result:
            hex_color = f'#{result["rgb"][0]:02x}{result["rgb"][1]:02x}{result["rgb"][2]:02x}'.upper()
            if hex_color not in color_library:
                color_library.append(hex_color)
                self._update_color_display(swatch_frame, color_library)

    def _delete_last_color_from_library(self, color_library, swatch_frame):
        if color_library:
            color_library.pop()
            self._update_color_display(swatch_frame, color_library)

    def _add_skill_row(self, parent, skill_list, key="", delay="100"):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        key_combo = ctk.CTkComboBox(row_frame, values=KEY_OPTIONS, width=70)
        key_combo.set(key)
        key_combo.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(row_frame, text="Delay:").pack(side="left")
        delay_entry = ctk.CTkEntry(row_frame, width=50, placeholder_text="ms")
        delay_entry.insert(0, delay)
        delay_entry.pack(side="left", padx=5)
        row_widgets = {'frame': row_frame, 'key': key_combo, 'delay': delay_entry}
        remove_button = ctk.CTkButton(row_frame, text="Xóa", width=40, height=20, fg_color="#c95151", command=lambda sl=skill_list, rw=row_widgets: self._remove_skill_row(sl, rw))
        remove_button.pack(side="left", padx=5)
        skill_list.append(row_widgets)

    def _remove_skill_row(self, skill_list, row_widgets):
        row_widgets['frame'].destroy()
        if row_widgets in skill_list:
            skill_list.remove(row_widgets)

    def get_config(self):
        for i, widgets in enumerate(self.detection_widgets):
            try:
                coord_tuple = ast.literal_eval(widgets['coord_entry'].get())
                if isinstance(coord_tuple, tuple) and len(coord_tuple) == 2:
                    self.detection_coords[i]['coord'] = coord_tuple
            except (ValueError, SyntaxError): pass
            
        config = {
            "detection": {
                "coords_manual": self.detection_coords,
                "color_library_manual_on": self.detection_color_library_on,
                "color_library_manual_off": self.detection_color_library_off,
                "tolerance": self.tolerance_var.get()
            },
            "rules": []
        }
        
        for level, ui_data in self.mana_rules_ui.items():
            combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in ui_data['skill_rows'] if r['key'].get()]
            config["rules"].append({
                "level": ui_data["level"],
                "enabled": ui_data["enabled_var"].get(),
                "combo": combo_list
            })
            
        return config

    def set_config(self, data):
        if not data: data = {}

        detection_data = data.get("detection", {})
        self.detection_coords = detection_data.get("coords_manual", [d.copy() for d in MANA_ORBS_COORDS])
        self.detection_color_library_on = detection_data.get("color_library_manual_on", DEFAULT_MANA_COLOR_LIBRARY[:])
        self.detection_color_library_off = detection_data.get("color_library_manual_off", ["#474747", "#363636"])
        self.tolerance_var.set(detection_data.get("tolerance", "10"))
        
        for i, orb_data in enumerate(self.detection_coords):
            if i < len(self.detection_widgets):
                self.detection_widgets[i]['coord_entry'].delete(0, 'end')
                self.detection_widgets[i]['coord_entry'].insert(0, str(orb_data.get('coord', '')))
        
        # Cần cập nhật lại cả hai thư viện màu trên UI
        # Lấy frame cha của các thư viện màu để cập nhật
        color_parent_frame = self.winfo_children()[0].winfo_children()[1].winfo_children()[1]
        for widget in color_parent_frame.winfo_children():
            widget.destroy() # Xóa UI cũ
        # Tạo lại UI màu sắc và sai số
        color_on_frame = self._create_color_library_frame(color_parent_frame, "Thư viện màu Mana (Khi Đầy)", self.detection_color_library_on)
        color_on_frame.pack(fill="x", expand=True, padx=5, pady=(0, 10))
        color_off_frame = self._create_color_library_frame(color_parent_frame, "Thư viện màu Mana (Khi Tắt)", self.detection_color_library_off)
        color_off_frame.pack(fill="x", expand=True, padx=5, pady=5)
        tolerance_frame = ctk.CTkFrame(color_parent_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(15, 5), padx=10)
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)


        rules_data = data.get("rules", [])
        for rule_config in rules_data:
            level = rule_config.get("level")
            if level in self.mana_rules_ui:
                ui_data = self.mana_rules_ui[level]
                ui_data["enabled_var"].set(rule_config.get("enabled", "off"))
                
                for row in ui_data["skill_rows"]:
                    row['frame'].destroy()
                ui_data["skill_rows"].clear()
                
                combo_list = rule_config.get("combo", [])
                if not combo_list:
                     self._add_skill_row(ui_data["skills_container"], ui_data["skill_rows"])
                else:
                    for skill in combo_list:
                        self._add_skill_row(ui_data["skills_container"], ui_data["skill_rows"], key=skill.get("key", ""), delay=skill.get("delay", ""))
