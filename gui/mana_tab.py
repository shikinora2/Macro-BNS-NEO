# gui/mana_tab.py
import customtkinter as ctk
from .constants import KEY_OPTIONS, MANA_ORBS_COORDS, DEFAULT_MANA_COLOR_LIBRARY
from core.pickers import ScreenPicker
import ast

class ManaTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        # Tách biệt các dòng skill cho từng chế độ
        self.auto_skill_rows = []
        self.manual_skill_rows = []
        
        self.manual_mana_coords = [d.copy() for d in MANA_ORBS_COORDS]
        self.manual_color_library = DEFAULT_MANA_COLOR_LIBRARY[:]

        self.enabled_var = ctk.StringVar(value="off")
        self.threshold_var = ctk.IntVar(value=5)
        self.tolerance_var = ctk.StringVar(value="10")

        self.auto_mode_frame = ctk.CTkFrame(self)
        self.manual_mode_frame = ctk.CTkFrame(self)

        self._create_auto_mode_ui()
        self._create_manual_mode_ui()
        
        self.update_ui_mode("Tự động (Profile)")

    def update_ui_mode(self, mode):
        if mode == "Tự động (Profile)":
            self.manual_mode_frame.pack_forget()
            self.auto_mode_frame.pack(fill="both", expand=True)
        else:
            self.auto_mode_frame.pack_forget()
            self.manual_mode_frame.pack(fill="both", expand=True)

    def _create_auto_mode_ui(self):
        # --- GIAO DIỆN CHẾ ĐỘ TỰ ĐỘNG (KHÔNG ĐỔI) ---
        main_frame = ctk.CTkFrame(self.auto_mode_frame, border_width=1, border_color="gray25")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(title_frame, text="Quy tắc phục hồi Mana", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkCheckBox(title_frame, text="Bật quy tắc", variable=self.enabled_var, onvalue="on", offvalue="off").pack(side="right")
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        condition_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        condition_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(condition_frame, text="Điều kiện (Chế độ Tự động)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        locate_frame = ctk.CTkFrame(condition_frame)
        locate_frame.pack(fill="x", pady=5)
        ctk.CTkButton(locate_frame, text="Định vị tự động thanh Mana", command=self.locate_mana_bar).pack(side="left", padx=(0, 10))
        self.locate_status_label = ctk.CTkLabel(locate_frame, text="Trạng thái: Chưa định vị", text_color="gray")
        self.locate_status_label.pack(side="left")
        
        threshold_label_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        threshold_label_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(threshold_label_frame, text="Sử dụng combo khi Mana dưới:").pack(side="left")
        ctk.CTkLabel(threshold_label_frame, textvariable=self.threshold_var, font=ctk.CTkFont(weight="bold", size=16), text_color="#3399FF").pack(side="left", padx=5)
        ctk.CTkSlider(condition_frame, from_=1, to=10, number_of_steps=9, variable=self.threshold_var).pack(fill="x", pady=5)
        
        tolerance_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)
        
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="new", padx=5)
        
        skill_title_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        skill_title_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(skill_title_frame, text="Combo sử dụng:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, command=lambda: self._add_skill_row(self.auto_skills_container, self.auto_skill_rows)).pack(side="left", padx=10)
        
        self.auto_skills_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.auto_skills_container.pack(fill="x", expand=True)
        self._add_skill_row(self.auto_skills_container, self.auto_skill_rows)

    def _create_manual_mode_ui(self):
        # --- GIAO DIỆN CHẾ ĐỘ THỦ CÔNG (ĐÃ CẬP NHẬT) ---
        main_frame = ctk.CTkFrame(self.manual_mode_frame, border_width=1, border_color="gray25")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tiêu đề và nút bật/tắt chung
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(title_frame, text="Quy tắc phục hồi Mana (Thủ công)", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkCheckBox(title_frame, text="Bật quy tắc", variable=self.enabled_var, onvalue="on", offvalue="off").pack(side="right")

        # TabView chính để tách biệt cài đặt
        main_tab_view = ctk.CTkTabview(main_frame)
        main_tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        
        general_tab = main_tab_view.add("Cài đặt Chung")
        detection_tab = main_tab_view.add("Cài đặt Nhận diện")

        self._create_manual_general_settings_ui(general_tab)
        self._create_manual_detection_settings_ui(detection_tab)

    def _create_manual_general_settings_ui(self, parent_tab):
        """Tạo giao diện cho tab Cài đặt Chung (Ngưỡng & Combo)."""
        parent_tab.grid_columnconfigure(1, weight=1)

        # Cột trái: Điều kiện
        condition_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        condition_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        threshold_label_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        threshold_label_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(threshold_label_frame, text="Sử dụng combo khi Mana dưới:").pack(side="left")
        ctk.CTkLabel(threshold_label_frame, textvariable=self.threshold_var, font=ctk.CTkFont(weight="bold", size=16), text_color="#3399FF").pack(side="left", padx=5)
        ctk.CTkSlider(condition_frame, from_=1, to=10, number_of_steps=9, variable=self.threshold_var).pack(fill="x", pady=5)
        
        tolerance_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(15, 5))
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)

        # Cột phải: Combo
        action_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        skill_title_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        skill_title_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(skill_title_frame, text="Combo sử dụng:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, command=lambda: self._add_skill_row(self.manual_skills_container, self.manual_skill_rows)).pack(side="left", padx=10)
        
        self.manual_skills_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.manual_skills_container.pack(fill="both", expand=True)
        self._add_skill_row(self.manual_skills_container, self.manual_skill_rows)

    def _create_manual_detection_settings_ui(self, parent_tab):
        """Tạo giao diện cho tab Cài đặt Nhận diện (Tọa độ & Màu sắc)."""
        tab_view = ctk.CTkTabview(parent_tab)
        tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        coords_tab = tab_view.add("Chỉnh tọa độ")
        colors_tab = tab_view.add("Chỉnh màu sắc")

        # Tab con: Chỉnh tọa độ
        coords_scroll_frame = ctk.CTkScrollableFrame(coords_tab, label_text="Tọa độ các Orb Mana")
        coords_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.manual_widgets = []
        for i, orb_data in enumerate(self.manual_mana_coords):
            row_frame = ctk.CTkFrame(coords_scroll_frame)
            row_frame.pack(fill="x", pady=4, padx=5)
            row_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row_frame, text=f"Mana #{orb_data['id']}", width=70).grid(row=0, column=0, padx=5)
            coord_entry = ctk.CTkEntry(row_frame)
            coord_entry.insert(0, str(orb_data['coord']))
            coord_entry.grid(row=0, column=1, padx=5, sticky="ew")
            ctk.CTkButton(row_frame, text="Lấy tọa độ", width=100, command=lambda idx=i: self._pick_coordinate_for_orb_manual(idx)).grid(row=0, column=2, padx=5)
            self.manual_widgets.append({'coord_entry': coord_entry})
            
        # Tab con: Chỉnh màu sắc
        color_frame = ctk.CTkFrame(colors_tab, border_width=1, border_color="gray40")
        color_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(color_frame, text="Thư viện màu Mana", font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
        self.manual_color_swatch_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        self.manual_color_swatch_frame.pack(pady=5)
        color_buttons_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_buttons_frame.pack(pady=(0,10))
        ctk.CTkButton(color_buttons_frame, text="Thêm màu", command=self._add_color_to_manual_library).pack(side="left", padx=5)
        ctk.CTkButton(color_buttons_frame, text="Xóa màu cuối", fg_color="#c95151", command=self._delete_last_color_from_manual_library).pack(side="left", padx=5)
        self._update_manual_color_display()

    def locate_mana_bar(self):
        self.locate_status_label.configure(text="Trạng thái: Đang tìm...", text_color="orange")
        if not hasattr(self.app, 'layout_manager'): return
        success = self.app.layout_manager.locate_ui_element('MANA_ORBS_AREA')
        if success:
            coords = self.app.layout_manager.get_located_region('MANA_ORBS_AREA')
            self.locate_status_label.configure(text=f"Đã tìm thấy tại {coords}", text_color="lightgreen")
        else:
            self.locate_status_label.configure(text="Trạng thái: Không tìm thấy!", text_color="red")
    
    def _pick_coordinate_for_orb_manual(self, index):
        picker = ScreenPicker(self.app.root)
        result = picker.pick_coordinate()
        if result:
            coord_tuple = (result['x'], result['y'])
            self.manual_mana_coords[index]['coord'] = coord_tuple
            self.manual_widgets[index]['coord_entry'].delete(0, 'end')
            self.manual_widgets[index]['coord_entry'].insert(0, str(coord_tuple))

    def _update_manual_color_display(self):
        frame = self.manual_color_swatch_frame
        for widget in frame.winfo_children(): widget.destroy()
        if not self.manual_color_library:
            ctk.CTkLabel(frame, text="Thư viện trống", text_color="gray").pack()
        else:
            for color_hex in self.manual_color_library:
                ctk.CTkLabel(frame, text="", width=30, height=30, fg_color=color_hex, corner_radius=4).pack(side="left", padx=3)

    def _add_color_to_manual_library(self):
        picker = ScreenPicker(self.app.root)
        result = picker.pick_color()
        if result:
            hex_color = f'#{result["rgb"][0]:02x}{result["rgb"][1]:02x}{result["rgb"][2]:02x}'.upper()
            if hex_color not in self.manual_color_library:
                self.manual_color_library.append(hex_color)
                self._update_manual_color_display()

    def _delete_last_color_from_manual_library(self):
        if self.manual_color_library:
            self.manual_color_library.pop()
            self._update_manual_color_display()

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
        remove_button = ctk.CTkButton(row_frame, text="Xóa", width=40, height=20, fg_color="#c95151", command=lambda rw=row_widgets: self._remove_skill_row(rw, skill_list))
        remove_button.pack(side="left", padx=5)
        skill_list.append(row_widgets)

    def _remove_skill_row(self, row_widgets, skill_list):
        row_widgets['frame'].destroy()
        if row_widgets in skill_list:
            skill_list.remove(row_widgets)

    def get_config(self):
        # Lấy combo từ chế độ đang hoạt động
        current_mode = self.app.settings_tab.detection_mode_var.get()
        if current_mode == "Tự động (Profile)":
            combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in self.auto_skill_rows if r['key'].get()]
        else:
            combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in self.manual_skill_rows if r['key'].get()]

        for i, widgets in enumerate(self.manual_widgets):
            try:
                coord_tuple = ast.literal_eval(widgets['coord_entry'].get())
                if isinstance(coord_tuple, tuple) and len(coord_tuple) == 2:
                    self.manual_mana_coords[i]['coord'] = coord_tuple
            except (ValueError, SyntaxError): pass
            
        return {
            "enabled": self.enabled_var.get(),
            "threshold": self.threshold_var.get(),
            "tolerance": self.tolerance_var.get(),
            "combo": combo_list,
            "mana_coords_manual": self.manual_mana_coords,
            "mana_color_library_manual": self.manual_color_library
        }

    def set_config(self, data):
        if not data: return
        self.enabled_var.set(data.get("enabled", "off"))
        self.threshold_var.set(data.get("threshold", 5))
        self.tolerance_var.set(data.get("tolerance", "10"))
        
        self.manual_mana_coords = data.get("mana_coords_manual", [d.copy() for d in MANA_ORBS_COORDS])
        self.manual_color_library = data.get("mana_color_library_manual", DEFAULT_MANA_COLOR_LIBRARY[:])
        
        for i, orb_data in enumerate(self.manual_mana_coords):
            if i < len(self.manual_widgets):
                self.manual_widgets[i]['coord_entry'].delete(0, 'end')
                self.manual_widgets[i]['coord_entry'].insert(0, str(orb_data.get('coord', '')))
        self._update_manual_color_display()

        if hasattr(self.app, 'layout_manager') and self.app.layout_manager.get_located_region('MANA_ORBS_AREA'):
            self.locate_status_label.configure(text="Trạng thái: Đã định vị", text_color="lightgreen")

        # Xóa và tạo lại combo cho cả hai chế độ
        for row in self.auto_skill_rows: row['frame'].destroy()
        self.auto_skill_rows.clear()
        for row in self.manual_skill_rows: row['frame'].destroy()
        self.manual_skill_rows.clear()

        combo_list = data.get("combo", [])
        if not combo_list:
            self._add_skill_row(self.auto_skills_container, self.auto_skill_rows)
            self._add_skill_row(self.manual_skills_container, self.manual_skill_rows)
        else:
            for skill in combo_list:
                self._add_skill_row(self.auto_skills_container, self.auto_skill_rows, key=skill.get("key", ""), delay=skill.get("delay", ""))
                self._add_skill_row(self.manual_skills_container, self.manual_skill_rows, key=skill.get("key", ""), delay=skill.get("delay", ""))
