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
        
        # SỬA LỖI: Tách biệt danh sách skill cho từng chế độ
        self.auto_skill_rows = []
        self.manual_skill_rows = []
        
        # Dữ liệu cho chế độ thủ công
        self.manual_hp_bar_region = None
        self.manual_color_library = DEFAULT_HP_COLOR_LIBRARY[:]

        # Biến điều khiển chung
        self.enabled_var = ctk.StringVar(value="off")
        self.threshold_var = ctk.IntVar(value=30)
        self.tolerance_var = ctk.StringVar(value="15")

        # --- Frame chính chứa 2 chế độ ---
        self.auto_mode_frame = ctk.CTkFrame(self)
        self.manual_mode_frame = ctk.CTkFrame(self)

        self._create_auto_mode_ui()
        self._create_manual_mode_ui()

        # Mặc định hiển thị chế độ tự động
        self.update_ui_mode("Tự động (Profile)")

    def update_ui_mode(self, mode):
        """Hiển thị giao diện tương ứng với chế độ được chọn."""
        if mode == "Tự động (Profile)":
            self.manual_mode_frame.pack_forget()
            self.auto_mode_frame.pack(fill="both", expand=True)
        else: # Chế độ Thủ công
            self.auto_mode_frame.pack_forget()
            self.manual_mode_frame.pack(fill="both", expand=True)

    def _create_auto_mode_ui(self):
        main_frame = ctk.CTkFrame(self.auto_mode_frame, border_width=1, border_color="gray25")
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
        ctk.CTkLabel(condition_frame, text="Điều kiện (Chế độ Tự động)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        locate_frame = ctk.CTkFrame(condition_frame)
        locate_frame.pack(fill="x", pady=5)
        ctk.CTkButton(locate_frame, text="Định vị tự động thanh HP", command=self.locate_hp_bar).pack(side="left", padx=(0, 10))
        self.locate_status_label = ctk.CTkLabel(locate_frame, text="Trạng thái: Chưa định vị", text_color="gray")
        self.locate_status_label.pack(side="left")
        
        threshold_label_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        threshold_label_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(threshold_label_frame, text="Sử dụng combo khi HP dưới (%):").pack(side="left")
        ctk.CTkLabel(threshold_label_frame, textvariable=self.threshold_var, font=ctk.CTkFont(weight="bold", size=16), text_color="#E53935").pack(side="left", padx=5)
        ctk.CTkSlider(condition_frame, from_=1, to=100, number_of_steps=99, variable=self.threshold_var).pack(fill="x", pady=5)
        
        tolerance_frame = ctk.CTkFrame(condition_frame, fg_color="transparent")
        tolerance_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(tolerance_frame, text="Sai số màu (%):").pack(side="left")
        ctk.CTkEntry(tolerance_frame, textvariable=self.tolerance_var, width=60).pack(side="left", padx=5)
        
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="new", padx=5)
        
        skill_title_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        skill_title_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(skill_title_frame, text="Combo sử dụng:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        # SỬA LỖI: Thêm skill vào đúng danh sách
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, command=lambda: self._add_skill_row(self.auto_skills_container, self.auto_skill_rows)).pack(side="left", padx=10)
        
        self.auto_skills_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.auto_skills_container.pack(fill="x", expand=True)
        self._add_skill_row(self.auto_skills_container, self.auto_skill_rows, key="4")

    def _create_manual_mode_ui(self):
        main_frame = ctk.CTkFrame(self.manual_mode_frame, border_width=1, border_color="gray25")
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
        ctk.CTkLabel(condition_frame, text="Điều kiện (Chế độ Thủ công)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
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
        # SỬA LỖI: Thêm skill vào đúng danh sách
        ctk.CTkButton(skill_title_frame, text="(+) Thêm", width=60, height=20, command=lambda: self._add_skill_row(self.manual_skills_container, self.manual_skill_rows)).pack(side="left", padx=10)
        
        self.manual_skills_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.manual_skills_container.pack(fill="x", expand=True)
        self._add_skill_row(self.manual_skills_container, self.manual_skill_rows, key="4")
        self._update_manual_color_display()

    def locate_hp_bar(self):
        self.locate_status_label.configure(text="Trạng thái: Đang tìm...", text_color="orange")
        success = self.app.layout_manager.locate_ui_element('HP_BAR_AREA')
        if success:
            coords = self.app.layout_manager.get_located_region('HP_BAR_AREA')
            self.locate_status_label.configure(text=f"Đã tìm thấy tại {coords}", text_color="lightgreen")
        else:
            self.locate_status_label.configure(text="Trạng thái: Không tìm thấy!", text_color="red")

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

    # SỬA LỖI: Cập nhật hàm để nhận vào danh sách skill cụ thể
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

    # SỬA LỖI: Cập nhật hàm để nhận vào danh sách skill cụ thể
    def _remove_skill_row(self, row_widgets, skill_list):
        row_widgets['frame'].destroy()
        if row_widgets in skill_list:
            skill_list.remove(row_widgets)

    def get_config(self):
        # SỬA LỖI: Lấy combo từ chế độ đang hoạt động
        current_mode = self.app.settings_tab.detection_mode_var.get()
        if current_mode == "Tự động (Profile)":
            combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in self.auto_skill_rows if r['key'].get()]
        else:
            combo_list = [{"key": r['key'].get(), "delay": r['delay'].get()} for r in self.manual_skill_rows if r['key'].get()]
            
        return {
            "enabled": self.enabled_var.get(),
            "threshold": self.threshold_var.get(),
            "tolerance": self.tolerance_var.get(),
            "combo": combo_list,
            "hp_bar_region_manual": self.manual_hp_bar_region,
            "hp_color_library_manual": self.manual_color_library
        }

    def set_config(self, data):
        if not data: return
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

        if self.app.layout_manager.get_located_region('HP_BAR_AREA'):
            self.locate_status_label.configure(text="Trạng thái: Đã định vị", text_color="lightgreen")

        # SỬA LỖI: Xóa và tạo lại combo cho cả hai chế độ một cách riêng biệt
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
                # Khi tải, áp dụng combo cho cả hai chế độ để đồng bộ
                self._add_skill_row(self.auto_skills_container, self.auto_skill_rows, key=skill.get("key", ""), delay=skill.get("delay", ""))
                self._add_skill_row(self.manual_skills_container, self.manual_skill_rows, key=skill.get("key", ""), delay=skill.get("delay", ""))
