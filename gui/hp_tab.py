# gui/hp_tab.py
import customtkinter as ctk
from .constants import KEY_OPTIONS, DEFAULT_HP_COLOR_LIBRARY
from core.pickers import ScreenPicker, RegionPicker
from PIL import ImageGrab
import ast

class HPTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        # CHỈNH SỬA: Chỉ cần một danh sách skill
        self.skill_rows = []
        
        # Dữ liệu cho chế độ thủ công
        self.manual_hp_bar_region = None
        self.manual_color_library = DEFAULT_HP_COLOR_LIBRARY[:]

        # Biến điều khiển chung
        self.enabled_var = ctk.StringVar(value="off")
        self.threshold_var = ctk.IntVar(value=30)
        self.tolerance_var = ctk.StringVar(value="15")

        # CHỈNH SỬA: Xóa bỏ frame auto và manual, tạo UI trực tiếp
        self._create_manual_mode_ui()

    # XÓA BỎ: update_ui_mode
    # XÓA BỎ: _create_auto_mode_ui

    def _create_manual_mode_ui(self):
        # CHỈNH SỬA: Frame này giờ là frame chính của tab
        main_frame = ctk.CTkFrame(self, border_width=1, border_color="gray25")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(title_frame, text="Quy tắc phục hồi HP (Máu)", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkCheckBox(title_frame, text="Bật quy tắc", variable=self.enabled_var, onvalue="on", offvalue="off").pack(side="right")
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        condition_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        condition_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(condition_frame, text="Điều kiện", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        region_frame = ctk.CTkFrame(condition_frame)
        region_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(region_frame, text="Vùng thanh HP:").pack(side="left", padx=(0, 5))
        self.manual_region_label = ctk.CTkLabel(region_frame, text="Chưa đặt", text_color="yellow")
        self.manual_region_label.pack(side="left", padx=5)
        ctk.CTkButton(region_frame, text="Chọn vùng", command=self._pick_hp_bar_region_manual).pack(side="right", padx=5)
        
        threshold_label_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        threshold_label_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(threshold_label_frame, text="Sử dụng combo khi HP dưới (%):").pack(side="left")
        ctk.CTkLabel(threshold_label_frame, textvariable=self.threshold_var, font=ctk.CTkFont(weight="bold", size=16), text_color="#E53935").pack(side="left", padx=5)
        ctk.CTkSlider(condition_frame, from_=1, to=100, number_of_steps=99, variable=self.threshold_var).pack(fill="x", pady=5)
        
        color_lib_frame = ctk.CTkFrame(condition_frame)
        color_lib_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(color_lib_frame, text="Thư viện màu HP:", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.manual_color_swatch_frame = ctk.CTkFrame(color_lib_frame, fg_color="transparent")
        self.manual_color_swatch_frame.pack(pady=5)
        color_buttons_frame = ctk.CTkFrame(color_lib_frame, fg_color="transparent")
        color_buttons_frame.pack(pady=(0,10))
        ctk.CTkButton(color_buttons_frame, text="Thêm màu", command=self._add_color_to_manual_library).pack(side="left", padx=5)
        ctk.CTkButton(color_buttons_frame, text="Xóa màu cuối", fg_color="#c95151", command=self._delete_last_color_from_manual_library).pack(side="left", padx=5)
        
        tolerance_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)
        ctk.CTkButton(condition_frame, text="Kiểm tra nhận diện HP", command=self.app.test_hp_detection, fg_color="#5bc0de").pack(fill="x", pady=(15, 5))
        
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="new", padx=5)
        
        skill_title_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        skill_title_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(skill_title_frame, text="Combo sử dụng:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, command=lambda: self._add_skill_row(self.skills_container, self.skill_rows)).pack(side="left", padx=10)
        
        self.skills_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.skills_container.pack(fill="x", expand=True)
        self._add_skill_row(self.skills_container, self.skill_rows, key="4")
        self._update_manual_color_display()

    # XÓA BỎ: locate_hp_bar

    def _pick_hp_bar_region_manual(self):
        self.app.root.withdraw()
        self.app.root.after(200, self._show_region_picker_manual)

    def _show_region_picker_manual(self):
        try:
            screenshot = ImageGrab.grab()
            picker = RegionPicker(self.app.root, screenshot=screenshot)
            coords = picker.pick_region()
            if coords:
                self.manual_hp_bar_region = coords
                self.manual_region_label.configure(text=f"({coords[0]},{coords[1]}) - ({coords[2]},{coords[3]})")
        finally:
            self.app.root.deiconify()

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
        # CHỈNH SỬA: Lấy combo trực tiếp
        combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in self.skill_rows if r['key'].get()]
            
        return {
            "enabled": self.enabled_var.get(),
            "threshold": self.threshold_var.get(),
            "tolerance": self.tolerance_var.get(),
            "combo": combo_list,
            "hp_bar_region_manual": self.manual_hp_bar_region,
            "hp_color_library_manual": self.manual_color_library
        }

    def set_config(self, data):
        if not data: data = {} # Đảm bảo data là dict
        self.enabled_var.set(data.get("enabled", "off"))
        self.threshold_var.set(data.get("threshold", 30))
        self.tolerance_var.set(data.get("tolerance", "15"))
        
        self.manual_hp_bar_region = data.get("hp_bar_region_manual")
        if self.manual_hp_bar_region:
             self.manual_region_label.configure(text=f"({self.manual_hp_bar_region[0]},{self.manual_hp_bar_region[1]}) - ({self.manual_hp_bar_region[2]},{self.manual_hp_bar_region[3]})")
        else:
             self.manual_region_label.configure(text="Chưa đặt")
        self.manual_color_library = data.get("hp_color_library_manual", DEFAULT_HP_COLOR_LIBRARY[:])
        self._update_manual_color_display()

        # CHỈNH SỬA: Xóa và tạo lại combo
        for row in self.skill_rows: row['frame'].destroy()
        self.skill_rows.clear()

        combo_list = data.get("combo", [])
        if not combo_list:
            self._add_skill_row(self.skills_container, self.skill_rows)
        else:
            for skill in combo_list:
                self._add_skill_row(self.skills_container, self.skill_rows, key=skill.get("key", ""), delay=skill.get("delay", ""))