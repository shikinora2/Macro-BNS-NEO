# gui/settings_tab.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import json

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.hide_to_tray_var = ctk.StringVar(value="off")
        self.run_as_admin_var = ctk.StringVar(value="off")
        self.run_on_startup_var = ctk.StringVar(value="off")
        self.overlay_pos = {"x": 100, "y": 100}
        
        self.detection_mode_var = ctk.StringVar(value="Tự động (Profile)")

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        profile_frame = ctk.CTkFrame(main_frame)
        profile_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(profile_frame, text="Cấu hình Giao diện (Layout)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(5,10))
        
        mode_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(mode_frame, text="Chế độ nhận diện:").pack(side="left", padx=(0, 10))
        self.mode_selector = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Tự động (Profile)", "Thủ công"],
            variable=self.detection_mode_var,
            command=self.on_mode_change
        )
        self.mode_selector.pack(side="left")

        self.profile_selection_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        ctk.CTkLabel(self.profile_selection_frame, text="Chọn Profile:").pack(side="left")
        self.profile_combo = ctk.CTkComboBox(self.profile_selection_frame, values=["Đang tải..."])
        self.profile_combo.pack(side="left", padx=10)
        self.profile_combo.set("Đang tải...")

        self.manual_profile_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        ctk.CTkButton(self.manual_profile_frame, text="Tải Profile Thủ Công...", command=self._load_manual_profile).pack(side="left", pady=5)
        ctk.CTkLabel(self.manual_profile_frame, text="(Tải file .json để áp dụng cho các cài đặt HP/Mana thủ công)", font=ctk.CTkFont(size=11, slant="italic"), text_color="gray").pack(side="left", padx=10)

        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(pady=10, padx=0, fill="x")
        ctk.CTkLabel(settings_frame, text="Hành vi ứng dụng", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(0, 10))
        ctk.CTkCheckBox(settings_frame, text="Tự động ẩn xuống khay hệ thống khi đóng cửa sổ", variable=self.hide_to_tray_var, onvalue="on", offvalue="off").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(settings_frame, text="Khởi động", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(20, 10))
        ctk.CTkCheckBox(settings_frame, text="Tự động yêu cầu quyền Admin khi khởi chạy", variable=self.run_as_admin_var, onvalue="on", offvalue="off").pack(anchor="w", padx=20, pady=5)
        ctk.CTkCheckBox(settings_frame, text="Tự động chạy macro khi khởi động máy tính", variable=self.run_on_startup_var, onvalue="on", offvalue="off", command=self._toggle_startup).pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(settings_frame, text="Hiển thị In-game", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(20, 10))
        overlay_frame = ctk.CTkFrame(settings_frame)
        overlay_frame.pack(fill="x", padx=20, pady=5)
        self.show_overlay_var = ctk.StringVar(value="off")
        ctk.CTkCheckBox(overlay_frame, text="Hiển thị trạng thái macro trong game", variable=self.show_overlay_var, onvalue="on", offvalue="off", command=self.app.toggle_status_overlay).pack(side="left", padx=(0, 20))
        ctk.CTkButton(overlay_frame, text="Chọn vị trí hiển thị", command=self.app.position_status_overlay).pack(side="left")

        self.on_mode_change(self.detection_mode_var.get())

    def on_mode_change(self, mode):
        is_auto_mode = (mode == "Tự động (Profile)")
        if is_auto_mode:
            self.manual_profile_frame.pack_forget()
            self.profile_selection_frame.pack(fill="x", padx=10, pady=(5,0))
        else:
            self.profile_selection_frame.pack_forget()
            self.manual_profile_frame.pack(fill="x", padx=10, pady=(5,0))
            
        if hasattr(self.app, 'sub_combo_tab'):
            if hasattr(self.app.sub_combo_tab, 'hp_tab'): self.app.sub_combo_tab.hp_tab.update_ui_mode(mode)
            if hasattr(self.app.sub_combo_tab, 'mana_tab'): self.app.sub_combo_tab.mana_tab.update_ui_mode(mode)

    def _load_manual_profile(self):
        filepath = filedialog.askopenfilename(title="Chọn file cấu hình thủ công", filetypes=[("JSON files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            sub_combo_config = config_data.get("sub_combo", {})
            if not sub_combo_config:
                messagebox.showwarning("File không hợp lệ", "File cấu hình không chứa mục 'sub_combo'.", parent=self.app.root)
                return
            self.app.sub_combo_tab.set_config(sub_combo_config)
            self.app.home_tab.log_message(f"Đã tải thành công cấu hình thủ công từ: {os.path.basename(filepath)}")
            messagebox.showinfo("Thành công", "Đã áp dụng cấu hình thủ công.", parent=self.app.root)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải hoặc áp dụng file cấu hình.\nLỗi: {e}", parent=self.app.root)

    def populate_profiles(self):
        if not hasattr(self.app, 'layout_manager'): return
        profile_names = self.app.layout_manager.get_profile_names()
        
        if profile_names:
            # Nếu tìm thấy profile, cấu hình cho chế độ Tự động
            self.profile_combo.configure(values=profile_names, command=self.app.layout_manager.set_active_profile)
            self.profile_combo.set(profile_names[0])
            self.app.layout_manager.set_active_profile(profile_names[0])
            # self.mode_selector.configure(state="normal") # <--- ĐÃ XÓA DÒNG GÂY LỖI
            self.detection_mode_var.set("Tự động (Profile)")
        else:
            # Nếu không tìm thấy, buộc chuyển sang chế độ Thủ công
            self.app.home_tab.log_message("Cảnh báo: Không tìm thấy file layout. Tự động chuyển sang chế độ Thủ công.")
            self.profile_combo.configure(values=["Không có profile"])
            self.profile_combo.set("Không có profile")
            self.detection_mode_var.set("Thủ công")
            # self.mode_selector.configure(state="disabled") # <--- ĐÃ XÓA DÒNG GÂY LỖI
        
        self.on_mode_change(self.detection_mode_var.get())

    def get_config(self):
        return {
            "hide_to_tray": self.hide_to_tray_var.get(),
            "run_as_admin": self.run_as_admin_var.get(),
            "run_on_startup": self.run_on_startup_var.get(),
            "show_overlay": self.show_overlay_var.get(),
            "overlay_pos": self.overlay_pos,
            "active_profile": self.profile_combo.get() if self.detection_mode_var.get() == "Tự động (Profile)" else "",
            "detection_mode": self.detection_mode_var.get()
        }

    def set_config(self, data):
        if not data: return
        self.hide_to_tray_var.set(data.get("hide_to_tray", "off"))
        self.run_as_admin_var.set(data.get("run_as_admin", "off"))
        self.overlay_pos = data.get("overlay_pos", {"x": 100, "y": 100})
        self.show_overlay_var.set(data.get("show_overlay", "off"))
        self.app.toggle_status_overlay(startup=True)
        
        # SỬA LỖI: Chỉ thay đổi chế độ nếu có profile layout
        # Nếu không có profile, sẽ giữ nguyên ở chế độ Thủ công đã được đặt trong populate_profiles
        if self.app.layout_manager.get_profile_names():
            detection_mode = data.get("detection_mode", "Tự động (Profile)")
            self.detection_mode_var.set(detection_mode)
        
        self.on_mode_change(self.detection_mode_var.get())

        profile_to_load = data.get("active_profile")
        if profile_to_load and profile_to_load in self.profile_combo.cget("values"):
            self.profile_combo.set(profile_to_load)
            if hasattr(self.app, 'layout_manager'):
                self.app.layout_manager.set_active_profile(profile_to_load)

        startup_shortcut_exists = os.path.exists(os.path.join(self._get_startup_folder(), "MacroBNS_NEO_Startup.bat"))
        saved_startup_setting = data.get("run_on_startup", "off")
        self.run_on_startup_var.set("on" if (saved_startup_setting == "on" and startup_shortcut_exists) else "off")
    
    def _get_startup_folder(self):
        return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    def _toggle_startup(self):
        # ... (logic không đổi)
        pass
