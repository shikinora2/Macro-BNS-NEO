# gui/home_tab.py
import customtkinter as ctk
import json
import pygetwindow as gw
from tkinter import filedialog, messagebox, TclError
from datetime import datetime
import os
import threading
import queue

class HomeTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.window_list_queue = queue.Queue()

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 7))
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(top_frame, text="License Key:", font=ctk.CTkFont(weight="bold", size=12), width=100, anchor="w").grid(row=0, column=0, padx=(0, 5), pady=(0, 8), sticky="w")
        self.license_key_entry = ctk.CTkEntry(top_frame, placeholder_text="Nhập key của bạn tại đây")
        self.license_key_entry.grid(row=0, column=1, columnspan=2, padx=(0, 5), pady=(0, 8), sticky="ew")
        
        self.activate_btn = ctk.CTkButton(top_frame, text="Kích hoạt", width=90, command=self.app.activate_license)
        self.activate_btn.grid(row=0, column=3, pady=(0, 8), sticky="w")

        ctk.CTkLabel(top_frame, text="Hạn sử dụng:", font=ctk.CTkFont(weight="bold", size=12), width=90, anchor="w").grid(row=0, column=4, padx=(10, 5), pady=(0, 8), sticky="w")
        self.expiration_label = ctk.CTkLabel(top_frame, text="Chưa kích hoạt", font=ctk.CTkFont(weight="bold"), text_color="gray", anchor="w")
        self.expiration_label.grid(row=0, column=5, pady=(0, 8), sticky="w")

        ctk.CTkLabel(top_frame, text="HOTKEY:", font=ctk.CTkFont(weight="bold", size=12), width=100, anchor="w").grid(row=1, column=0, padx=(0, 5), pady=(0, 8), sticky="w")
        self.hotkey_combo = ctk.CTkComboBox(top_frame, values=["Chuột giữa", "Chuột cạnh dưới", "Chuột cạnh trên"], state="readonly", width=150)
        self.hotkey_combo.grid(row=1, column=1, padx=(0, 5), pady=(0, 8), sticky="w")
        self.hotkey_combo.set("Chuột giữa")

        ctk.CTkLabel(top_frame, text="Chế độ Hotkey:", font=ctk.CTkFont(size=12)).grid(row=1, column=2, padx=(10, 5), pady=(0, 8), sticky="w")
        self.hotkey_mode_combo = ctk.CTkComboBox(top_frame, values=["Giữ để chạy", "Nhấn để Bật/Tắt"], state="readonly", width=150)
        self.hotkey_mode_combo.grid(row=1, column=3, pady=(0, 8), sticky="w")
        self.hotkey_mode_combo.set("Giữ để chạy")

        ctk.CTkLabel(top_frame, text="TRẠNG THÁI:", font=ctk.CTkFont(weight="bold", size=12), width=90, anchor="w").grid(row=1, column=4, padx=(10, 5), pady=(0, 8), sticky="w")
        self.status_label = ctk.CTkLabel(top_frame, text="Sẵn sàng", font=ctk.CTkFont(weight="bold"), text_color="#5cb85c", anchor="w")
        self.status_label.grid(row=1, column=5, pady=(0, 8), sticky="w")

        ctk.CTkLabel(top_frame, text="Cửa sổ Game:", font=ctk.CTkFont(weight="bold", size=12), width=100, anchor="w").grid(row=2, column=0, padx=(0, 5), pady=(0, 8), sticky="w")
        self.window_combo = ctk.CTkComboBox(top_frame, values=[""], state="readonly")
        self.window_combo.grid(row=2, column=1, columnspan=3, padx=(0, 5), pady=(0, 8), sticky="ew")
        self.refresh_button = ctk.CTkButton(top_frame, text="Làm mới", width=80, font=ctk.CTkFont(size=11), command=self._refresh_window_list)
        self.refresh_button.grid(row=2, column=4, columnspan=2, padx=(5,0), pady=(0, 8), sticky="w")

        ctk.CTkLabel(top_frame, text="HIỆU SUẤT:", font=ctk.CTkFont(weight="bold", size=12), width=100, anchor="w").grid(row=3, column=0, padx=(0, 5), pady=(0, 8), sticky="w")
        self.fps_label = ctk.CTkLabel(top_frame, text="N/A", font=ctk.CTkFont(weight="bold"), text_color="cyan", anchor="w")
        self.fps_label.grid(row=3, column=1, pady=(0, 8), sticky="w")
        
        info_notebook = ctk.CTkTabview(self, corner_radius=6)
        info_notebook.pack(fill="both", expand=True, padx=5, pady=3)
        info_notebook.add("Nhật ký")
        self.log_text = ctk.CTkTextbox(info_notebook.tab("Nhật ký"), wrap="word", font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=3, pady=3)
        self.log_text.configure(state="disabled")

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=5, pady=(3, 5))
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="Lưu Cấu hình", command=self.save_configuration, font=ctk.CTkFont(size=11)).pack(side="left", padx=3, pady=3, expand=True)
        ctk.CTkButton(btn_frame, text="Tải Cấu hình", command=self.load_configuration, font=ctk.CTkFont(size=11)).pack(side="left", padx=3, pady=3, expand=True)
        ctk.CTkButton(btn_frame, text="Xóa Log", command=self.clear_log, font=ctk.CTkFont(size=11), fg_color="#c95151").pack(side="left", padx=3, pady=3, expand=True)
        
        credit_label = ctk.CTkLabel(bottom_frame, text="Phần mềm được phát triển bởi ShikiNora", font=ctk.CTkFont(size=13, slant="italic"), text_color="gray50")
        credit_label.pack(pady=(5,0))

        self.log_message("Ứng dụng đã sẵn sàng. Vui lòng kích hoạt License Key.")
        self.after(150, self._refresh_window_list)
    
    def _get_all_configs(self, save_key=False):
        # SỬA LỖI: Sử dụng đúng tên thuộc tính đã được định nghĩa trong main.py
        config = {
            "home": { 
                "hotkey": self.hotkey_combo.get(), 
                "hotkey_mode": self.hotkey_mode_combo.get(), 
                "target_window": self.window_combo.get(),
            },
            "main_combo": self.app.combo_chinh_tab.get_config(), 
            "hp": self.app.hp_tab.get_config(),
            "mana": self.app.mana_tab.get_config(),
            "skill": self.app.skill_tab.get_config(),
            "crit": self.app.crit_tab.get_config(),
            "settings": self.app.cai_dat_tab.get_config(), 
        }
        if save_key:
            config["home"]["license_key"] = self.license_key_entry.get()
        return config

    def _set_all_configs(self, config_data):
        # SỬA LỖI: Sử dụng đúng tên thuộc tính đã được định nghĩa trong main.py
        home_config = config_data.get("home", {})
        self.hotkey_combo.set(home_config.get("hotkey", "Chuột giữa"))
        self.hotkey_mode_combo.set(home_config.get("hotkey_mode", "Giữ để chạy"))
        
        target_window = home_config.get("target_window", "")
        if target_window and target_window in self.window_combo.cget("values"):
            self.window_combo.set(target_window)
        
        saved_key = home_config.get("license_key")
        if saved_key:
            self.license_key_entry.delete(0, "end")
            self.license_key_entry.insert(0, saved_key)
            self.app.activate_license()

        self.app.combo_chinh_tab.set_config(config_data.get("main_combo", {}))
        self.app.hp_tab.set_config(config_data.get("hp", {}))
        self.app.mana_tab.set_config(config_data.get("mana", {}))
        self.app.skill_tab.set_config(config_data.get("skill", {}))
        self.app.crit_tab.set_config(config_data.get("crit", {}))
        self.app.cai_dat_tab.set_config(config_data.get("settings", {}))
        
        self.app.condition_handler.clear_template_cache()
        
        self.update_status("ready")
        self.log_message("Tải cấu hình hoàn tất.")

    def update_performance_display(self, fps):
        try:
            if not self.winfo_exists(): return
            if fps > 0:
                self.fps_label.configure(text=f"{fps:.1f} FPS")
            else:
                self.fps_label.configure(text="N/A")
        except (RuntimeError, TclError):
            pass

    def _refresh_window_list(self):
        self.refresh_button.configure(state="disabled", text="Đang tải...")
        threading.Thread(target=self._threaded_get_windows, daemon=True).start()
        self.after(100, self._process_window_list_queue)

    def _threaded_get_windows(self):
        try:
            window_titles = [win.title for win in gw.getAllWindows() if win.title]
            self.window_list_queue.put(window_titles)
        except Exception as e:
            self.window_list_queue.put(e)

    def _process_window_list_queue(self):
        try:
            result = self.window_list_queue.get_nowait()
            if isinstance(result, Exception):
                self._update_window_list_ui(None, error=result)
            else:
                self._update_window_list_ui(result)
        except queue.Empty:
            self.after(100, self._process_window_list_queue)
        except (RuntimeError, TclError):
            pass

    def _update_window_list_ui(self, window_titles, error=None):
        try:
            if not self.winfo_exists():
                return
        except (RuntimeError, TclError):
            return

        if error:
            self.log_message(f"Lỗi khi lấy danh sách cửa sổ: {error}")
        
        elif window_titles is not None:
            current_selection = self.window_combo.get()
            self.window_combo.configure(values=window_titles)
            if current_selection in window_titles:
                self.window_combo.set(current_selection)
            elif any("Blade & Soul" in title for title in window_titles):
                    self.window_combo.set([title for title in window_titles if "Blade & Soul" in title][0])
            elif window_titles:
                self.window_combo.set(window_titles[0])
            else:
                self.window_combo.configure(values=["Không tìm thấy cửa sổ nào"])
                self.window_combo.set("Không tìm thấy cửa sổ nào")

        self.refresh_button.configure(state="normal", text="Làm mới")

    def update_expiration_date(self, date_text, status):
        color_map = { "valid": "#5cb85c", "expired": "#d9534f", "invalid": "gray" }
        self.expiration_label.configure(text=date_text, text_color=color_map.get(status, "gray"))

    def update_status(self, status_type):
        if status_type == "running": self.status_label.configure(text="Đang chạy...", text_color="#f0ad4e")
        elif status_type == "stopped": self.status_label.configure(text="Đã dừng", text_color="#d9534f")
        else: self.status_label.configure(text="Sẵn sàng", text_color="#5cb85c")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_message("Đã xóa nhật ký.")

    def log_message(self, message):
        try:
            if not self.winfo_exists(): return
            self.log_text.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("0.0", f"[{timestamp}] {message}\n")
            self.log_text.configure(state="disabled")
        except (RuntimeError, TclError):
            pass
    
    def reset_to_default(self):
        """Reset các cài đặt trên tab Trang Chủ về mặc định."""
        self.license_key_entry.delete(0, "end")
        self.update_expiration_date("Chưa kích hoạt", "invalid")
        self.hotkey_combo.set("Chuột giữa")
        self.hotkey_mode_combo.set("Giữ để chạy")
        self.update_status("ready")
        self.app.combo_chinh_tab.set_config([])
        self.app.hp_tab.set_config({})
        self.app.mana_tab.set_config({})
        self.app.skill_tab.set_config({})
        self.app.crit_tab.set_config({})
        self.app.cai_dat_tab.set_config({})


    def _save_last_config_path(self, path):
        try:
            with open("autosave.path", "w") as f: f.write(path)
        except Exception as e:
            self.log_message(f"Lỗi khi lưu đường dẫn auto-save: {e}")

    def _silent_autosave(self):
        default_autosave_path = "autosave_config.json"
        config_data = self._get_all_configs(save_key=self.app.is_license_valid)
        
        try:
            with open(default_autosave_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            self.app.last_config_path = default_autosave_path
            self._save_last_config_path(default_autosave_path)
            self.log_message("Kích hoạt thành công, tự động lưu cấu hình.")
        except Exception as e:
            self.log_message(f"Lỗi khi tự động lưu cấu hình: {e}")

    def save_configuration(self):
        config_data = self._get_all_configs(save_key=self.app.is_license_valid)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", 
            filetypes=[("JSON files", "*.json")],
            title="Lưu cấu hình"
        )
            
        if not file_path:
            self.log_message("Đã hủy lưu cấu hình.")
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            self.log_message(f"Đã lưu cấu hình vào: {file_path}")
            self._save_last_config_path(file_path)
            self.app.last_config_path = file_path
        except Exception as e:
            self.log_message(f"Lỗi khi lưu cấu hình: {e}")
            messagebox.showerror("Lỗi Lưu File", f"Không thể lưu cấu hình vào file.\n\nChi tiết: {e}", parent=self.app.root)

    def load_configuration(self, filepath=None):
        file_path = filepath
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            if filepath is None: self.log_message("Đã hủy tải cấu hình.")
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f: config_data = json.load(f)
            self.app.last_config_path = file_path
            self._save_last_config_path(file_path)
            self._set_all_configs(config_data)
        except FileNotFoundError:
            self.log_message(f"Auto-load: Không tìm thấy file config '{file_path}'.")
        except Exception as e:
            self.log_message(f"Lỗi khi tải cấu hình: {e}")
            messagebox.showerror("Lỗi Tải File", f"Không thể đọc file cấu hình.\nFile có thể bị hỏng hoặc không đúng định dạng.\n\nChi tiết: {e}", parent=self.app.root)
