# gui/settings_tab.py
import customtkinter as ctk
from tkinter import messagebox
import os
import sys

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self.hide_to_tray_var = ctk.StringVar(value="off")
        self.run_as_admin_var = ctk.StringVar(value="off")
        self.run_on_startup_var = ctk.StringVar(value="off")
        self.overlay_pos = {"x": 100, "y": 100}
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # XÓA BỎ: Khung tải/lưu cấu hình combo phụ đã được loại bỏ.
        
        # Khung cài đặt ứng dụng
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

    def get_config(self):
        return {
            "hide_to_tray": self.hide_to_tray_var.get(),
            "run_as_admin": self.run_as_admin_var.get(),
            "run_on_startup": self.run_on_startup_var.get(),
            "show_overlay": self.show_overlay_var.get(),
            "overlay_pos": self.overlay_pos,
        }

    def set_config(self, data):
        if not data: return
        self.hide_to_tray_var.set(data.get("hide_to_tray", "off"))
        self.run_as_admin_var.set(data.get("run_as_admin", "off"))
        self.overlay_pos = data.get("overlay_pos", {"x": 100, "y": 100})
        self.show_overlay_var.set(data.get("show_overlay", "off"))
        self.app.toggle_status_overlay(startup=True)
        
        startup_shortcut_exists = os.path.exists(os.path.join(self._get_startup_folder(), "MacroBNS_NEO_Startup.bat"))
        saved_startup_setting = data.get("run_on_startup", "off")
        self.run_on_startup_var.set("on" if (saved_startup_setting == "on" and startup_shortcut_exists) else "off")
    
    def _get_startup_folder(self):
        return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    def _toggle_startup(self):
        startup_folder = self._get_startup_folder()
        shortcut_path = os.path.join(startup_folder, "MacroBNS_NEO_Startup.bat")
        
        try:
            if self.run_on_startup_var.get() == "on":
                if not os.path.exists(shortcut_path):
                    executable_path = sys.executable
                    script_path = os.path.abspath(sys.argv[0])
                    with open(shortcut_path, "w") as f:
                        f.write(f'@echo off\n')
                        f.write(f'cd /d "{os.path.dirname(script_path)}"\n')
                        f.write(f'start "" "{executable_path}" "{script_path}"\n')
                    self.app.home_tab.log_message("Đã tạo shortcut khởi động cùng Windows.")
            else:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    self.app.home_tab.log_message("Đã xóa shortcut khởi động cùng Windows.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thay đổi cài đặt khởi động.\nLỗi: {e}", parent=self.app.root)
            self.run_on_startup_var.set("off")
