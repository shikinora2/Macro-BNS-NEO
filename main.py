# main.py
import customtkinter as ctk
import threading
import time
import os
import pygetwindow as gw
from tkinter import messagebox
from pynput import mouse
import sys
import ctypes
import json

from core.license_manager import LicenseManager
from core.layout_manager import LayoutManager
from gui.status_overlay import StatusOverlay
from core.pickers import ScreenPicker
from core.utils import resource_path, image_to_base64
from gui.home_tab import HomeTab
from gui.main_combo_tab import ComboTab
from gui.sub_combo_tab import SubComboTab
from gui.settings_tab import SettingsTab
from gui.other_apps_tab import OtherAppsTab
from core.conditional_logic import ConditionalLogicHandler
from core.key_sender import KeySender

class AutoKeySenderApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Macro BNS NEO")
        self.root.geometry("720x680")
        self.root.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.is_hotkey_pressed = False
        self.is_macro_manager_running = False
        self.is_macro_toggled_on = False
        self.tray_icon = None
        self.last_config_path = None 
        
        self.is_license_valid = False
        self.license_manager = LicenseManager()
        self.key_sender = KeySender(self)
        
        self._setup_ui() 
        
        self.layout_manager = LayoutManager(self)
        self.condition_handler = ConditionalLogicHandler(self)

        self.settings_tab.populate_profiles()

        self.status_overlay = StatusOverlay(self.root)
        self.status_overlay.hide()
        self._start_listeners()
        
        self._auto_load_last_config()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        notebook = ctk.CTkTabview(self.root, corner_radius=8)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        notebook.add("Trang Chủ")
        notebook.add("Combo Chính")
        notebook.add("Combo Phụ")
        notebook.add("Cài Đặt")
        notebook.add("Ứng Dụng Khác")

        self.home_tab = HomeTab(master=notebook.tab("Trang Chủ"), app=self)
        self.main_combo_tab = ComboTab(master=notebook.tab("Combo Chính"))
        self.sub_combo_tab = SubComboTab(master=notebook.tab("Combo Phụ"), app=self)
        self.settings_tab = SettingsTab(master=notebook.tab("Cài Đặt"), app=self)
        self.other_apps_tab = OtherAppsTab(master=notebook.tab("Ứng Dụng Khác"))

        self.home_tab.pack(fill="both", expand=True)
        self.main_combo_tab.pack(fill="both", expand=True)
        self.sub_combo_tab.pack(fill="both", expand=True)
        self.settings_tab.pack(fill="both", expand=True)
        self.other_apps_tab.pack(fill="both", expand=True)
        
        self.main_combo_tab_lock = ctk.CTkFrame(self.main_combo_tab, fg_color=("gray90", "gray15"))
        ctk.CTkLabel(self.main_combo_tab_lock, text="Vui lòng kích hoạt License Key để sử dụng tính năng này.", font=ctk.CTkFont(size=14)).pack(expand=True)

        self.sub_combo_tab_lock = ctk.CTkFrame(self.sub_combo_tab, fg_color=("gray90", "gray15"))
        ctk.CTkLabel(self.sub_combo_tab_lock, text="Vui lòng kích hoạt License Key để sử dụng tính năng này.", font=ctk.CTkFont(size=14)).pack(expand=True)
        
        self.toggle_combo_tabs_lock(True) 
        notebook.set("Trang Chủ")

    def toggle_combo_tabs_lock(self, locked):
        if locked:
            self.main_combo_tab_lock.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.sub_combo_tab_lock.place(relx=0, rely=0, relwidth=1, relheight=1)
        else:
            self.main_combo_tab_lock.place_forget()
            self.sub_combo_tab_lock.place_forget()
    
    def activate_license(self):
        user_key = self.home_tab.license_key_entry.get()
        if not user_key:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập License Key.", parent=self.root)
            return
        status, expiry_date = self.license_manager.check_license(user_key)
        if status == "VALID":
            self.is_license_valid = True
            self.toggle_combo_tabs_lock(False)
            self.home_tab.update_expiration_date(expiry_date, "valid")
            self.home_tab._silent_autosave()
        elif status == "EXPIRED":
            self.is_license_valid = False
            self.toggle_combo_tabs_lock(True)
            self.home_tab.update_expiration_date(expiry_date, "expired")
            self.home_tab.log_message(f"Key đã hết hạn vào ngày: {expiry_date}")
            messagebox.showerror("Key hết hạn", f"Key của bạn đã hết hạn vào ngày {expiry_date}.\nVui lòng liên hệ nhà phát triển để gia hạn.", parent=self.root)
        else:
            self.is_license_valid = False
            self.toggle_combo_tabs_lock(True)
            self.home_tab.update_expiration_date("Không hợp lệ", "invalid")
            self.home_tab.log_message("Key không hợp lệ hoặc không tồn tại.")
            messagebox.showerror("Key không hợp lệ", "License key bạn nhập không đúng hoặc không tồn tại.\nVui lòng kiểm tra lại.", parent=self.root)

    def _on_mouse_click(self, x, y, button, pressed):
        try:
            self.root.after(0, self._handle_mouse_click_safely, x, y, button, pressed)
        except (NotImplementedError, RuntimeError):
            pass

    def _handle_mouse_click_safely(self, x, y, button, pressed):
        if not self.is_license_valid:
            if pressed: self.home_tab.log_message("Lỗi: Vui lòng kích hoạt License Key hợp lệ để sử dụng macro.")
            return
        hotkey_map = {"Chuột giữa": mouse.Button.middle, "Chuột cạnh dưới": mouse.Button.x1, "Chuột cạnh trên": mouse.Button.x2}
        selected_hotkey_name = self.home_tab.hotkey_combo.get()
        selected_mode = self.home_tab.hotkey_mode_combo.get()
        target_hotkey = hotkey_map.get(selected_hotkey_name)
        if button != target_hotkey: return
        if selected_mode == "Giữ để chạy":
            if pressed:
                if not self.is_hotkey_pressed:
                    self.is_hotkey_pressed = True
                    self.home_tab.update_status("running") 
                    if not self.is_macro_manager_running:
                        self.is_macro_manager_running = True
                        threading.Thread(target=self._run_macro, daemon=True).start()
            else:
                if self.is_hotkey_pressed:
                    self.is_hotkey_pressed = False
                    self.home_tab.update_status("stopped")
        elif selected_mode == "Nhấn để Bật/Tắt":
            if pressed:
                self.is_macro_toggled_on = not self.is_macro_toggled_on
                if self.is_macro_toggled_on:
                    self.is_hotkey_pressed = True
                    self.home_tab.update_status("running")
                    if not self.is_macro_manager_running:
                        self.is_macro_manager_running = True
                        threading.Thread(target=self._run_macro, daemon=True).start()
                else:
                    self.is_hotkey_pressed = False
                    self.home_tab.update_status("stopped")
    
    def _on_close(self):
        if self.settings_tab.hide_to_tray_var.get() == "on":
            self._hide_to_tray()
        else: self._quit_app()

    def _quit_app(self):
        if self.tray_icon: self.tray_icon.stop()
        self.is_hotkey_pressed = False
        self.root.quit()
        self.root.destroy()

    def _hide_to_tray(self):
        self.root.withdraw()
        try:
            from PIL import Image
            import pystray
            from pystray import MenuItem as item, Menu as menu
            icon_path = resource_path("icon.ico")
            image = Image.open(icon_path)
            tray_menu = menu(item('Hiện ứng dụng', self._show_from_tray, default=True), item('Thoát', self._quit_app))
            self.tray_icon = pystray.Icon("Macro BNS NEO", image, "Macro BNS NEO", tray_menu)
            self.tray_icon.run_detached()
        except (ImportError, FileNotFoundError) as e:
            self.home_tab.log_message(f"Lỗi hide to tray: {e}. Vui lòng cài đặt pystray.")
            self._quit_app()

    def _show_from_tray(self):
        if self.tray_icon: self.tray_icon.stop()
        self.tray_icon = None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _process_config_to_actions(self, combo_config):
        actions = []
        if not combo_config: return actions
        for item in combo_config:
            key = item.get("key")
            delay_str = item.get("delay")
            if key and delay_str and delay_str.isdigit():
                actions.append((key, int(delay_str)))
        return actions

    def _run_macro(self):
        target_title = self.home_tab.window_combo.get()
        game_window = gw.getWindowsWithTitle(target_title)
        if not game_window:
            self.root.after(0, self.home_tab.log_message, "Cảnh báo: Không tìm thấy cửa sổ game.")
            self.is_macro_manager_running = False
            return
        game_window = game_window[0]
        
        main_actions = self._process_config_to_actions(self.main_combo_tab.get_config())
        sub_combo_full_config = self.sub_combo_tab.get_config()
        
        if main_actions:
            self.root.after(0, self.home_tab.log_message, "Chạy macro với Combo Chính...")
            
            last_sent_times = {}
            last_condition_check_time = 0
            condition_check_interval = 0.1
            
            current_active_actions = main_actions
            last_used_combo_name = "Chính"
            self.root.after(0, self.home_tab.log_message, f"Sử dụng Combo {last_used_combo_name}.")

            while self.is_hotkey_pressed:
                current_time = time.time()
                
                if (current_time - last_condition_check_time > condition_check_interval):
                    last_condition_check_time = current_time
                    
                    if not game_window.isActive:
                        try: 
                            game_window.activate()
                            time.sleep(0.05) 
                        except Exception: 
                            pass 

                    sub_actions, sub_combo_name = self.condition_handler.check_for_sub_combo(sub_combo_full_config)
                    
                    next_actions = sub_actions if sub_actions is not None else main_actions
                    next_combo_name = sub_combo_name if sub_combo_name is not None else "Chính"

                    if next_combo_name != last_used_combo_name:
                        last_used_combo_name = next_combo_name
                        self.root.after(0, self.home_tab.log_message, f"Sử dụng Combo {last_used_combo_name}.")
                    
                    current_active_actions = next_actions
                
                if current_active_actions:
                    # Lấy danh sách các phím bị vô hiệu hóa
                    disabled_keys = self.condition_handler.get_disabled_keys(sub_combo_full_config)

                    for key, delay_ms in current_active_actions:
                        # Bỏ qua phím nếu nó nằm trong danh sách bị vô hiệu hóa
                        if key in disabled_keys:
                            continue

                        cooldown_sec = delay_ms / 1000.0
                        if cooldown_sec <= 0: cooldown_sec = 0.01 
                        
                        if current_time - last_sent_times.get(key, 0) >= cooldown_sec:
                            self.key_sender.send_key(key)
                            last_sent_times[key] = current_time
                
                time.sleep(0.001) 
        else:
            hp_enabled = sub_combo_full_config.get("hp", {}).get("enabled") == "on"
            mana_enabled = sub_combo_full_config.get("mana", {}).get("enabled") == "on"
            skill_enabled = any(rule.get("enabled") == "on" for rule in sub_combo_full_config.get("skill", {}).get("rules", []))
            crit_enabled = any(rule.get("enabled") == "on" for rule in sub_combo_full_config.get("crit", {}).get("rules", []))

            if not (hp_enabled or mana_enabled or skill_enabled or crit_enabled):
                self.root.after(0, self.home_tab.log_message, "Lỗi: Combo Chính trống và không có Combo Phụ nào được bật.")
                self.is_macro_manager_running = False
                return

            self.root.after(0, self.home_tab.log_message, "Chạy macro ở chế độ chỉ kiểm tra Combo Phụ...")
            
            while self.is_hotkey_pressed:
                if not game_window.isActive:
                    try: 
                        game_window.activate()
                        time.sleep(0.05) 
                    except Exception: 
                        pass 

                sub_actions, sub_combo_name = self.condition_handler.check_for_sub_combo(sub_combo_full_config)
                
                if sub_actions:
                    self.root.after(0, self.home_tab.log_message, f"Thực thi Combo Phụ: {sub_combo_name}.")
                    for key, delay_ms in sub_actions:
                        if not self.is_hotkey_pressed:
                            break
                        self.key_sender.send_key(key)
                        if delay_ms > 0:
                            time.sleep(delay_ms / 1000.0)
                
                time.sleep(0.05)

        self.root.after(0, self.home_tab.log_message, "Macro đã dừng.")
        self.is_macro_manager_running = False

    def _start_listeners(self):
        mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        threading.Thread(target=mouse_listener.start, daemon=True).start()

    def _auto_load_last_config(self):
        config_path_to_load = None
        if os.path.exists("autosave.path"):
            with open("autosave.path", "r") as f:
                last_config_path = f.read().strip()
                if last_config_path and os.path.exists(last_config_path):
                    config_path_to_load = last_config_path
        
        if not config_path_to_load and os.path.exists("autosave_config.json"):
            config_path_to_load = "autosave_config.json"

        if config_path_to_load:
            try:
                self.home_tab.log_message(f"Tự động tải từ: {config_path_to_load}")
                self.home_tab.load_configuration(filepath=config_path_to_load)
            except Exception as e:
                self.home_tab.log_message(f"Lỗi khi auto-load: {e}")
    
    def toggle_status_overlay(self, startup=False):
        if self.settings_tab.show_overlay_var.get() == "on":
            pos = self.settings_tab.overlay_pos
            self.status_overlay.move_window(pos['x'], pos['y'])
            self.status_overlay.show()
            if not startup: self.home_tab.log_message("Overlay trạng thái đã Bật.")
        else:
            self.status_overlay.hide()
            if not startup: self.home_tab.log_message("Overlay trạng thái đã Tắt.")

    def position_status_overlay(self):
        self.home_tab.log_message("Chọn một điểm trên màn hình để đặt overlay...")
        picker = ScreenPicker(self.root)
        result = picker.pick_coordinate()
        if result:
            self.settings_tab.overlay_pos = result
            self.status_overlay.move_window(result['x'], result['y'])
            self.home_tab.log_message(f"Đã di chuyển overlay đến: ({result['x']}, {result['y']})")
            self.home_tab._silent_autosave()

    def test_single_image_condition(self, panel_data):
        self.home_tab.log_message("Bắt đầu kiểm tra điều kiện hình ảnh...")
        pil_image = panel_data.get("template_image")
        if not pil_image:
            messagebox.showerror("Lỗi", "Không có ảnh mẫu để kiểm tra.", parent=self.root)
            return
        temp_rule_config = {
            "template_image_b64": image_to_base64(pil_image),
            "monitor_region": panel_data.get("monitor_region"),
            "confidence": panel_data.get("confidence").get()
        }
        is_match = self.condition_handler._check_image_condition(temp_rule_config)
        if is_match:
            message = "Thành công! Ảnh mẫu được tìm thấy trong vùng giám sát."
            self.home_tab.log_message(message)
            messagebox.showinfo("Kiểm tra thành công", message, parent=self.root)
        else:
            message = "Thất bại. Không tìm thấy ảnh mẫu trong vùng giám sát với ngưỡng tin cậy đã đặt."
            self.home_tab.log_message(message)
            messagebox.showwarning("Kiểm tra thất bại", message, parent=self.root)

    def test_hp_detection(self):
        self.home_tab.log_message("Đang kiểm tra nhận diện HP...")
        hp_config = self.sub_combo_tab.hp_tab.get_config()
        current_hp = self.condition_handler.get_current_hp_percentage(hp_config)
        if current_hp is not None:
            message = f"Nhận diện thành công! HP hiện tại: {current_hp:.2f}%"
            self.home_tab.log_message(message)
            messagebox.showinfo("Kiểm tra HP", message, parent=self.root)
        else:
            message = "Nhận diện thất bại. Vui lòng kiểm tra lại cấu hình HP."
            self.home_tab.log_message(message)
            messagebox.showerror("Kiểm tra HP", message, parent=self.root)


def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def get_last_config():
    try:
        path_to_check = None
        if os.path.exists("autosave.path"):
            with open("autosave.path", "r") as f:
                path_to_check = f.read().strip()
        elif os.path.exists("autosave_config.json"):
            path_to_check = "autosave_config.json"
        
        if path_to_check and os.path.exists(path_to_check):
            with open(path_to_check, 'r', encoding='utf-8') as f_json:
                return json.load(f_json)
    except Exception: 
        return {}
    return {}

if __name__ == "__main__":
    try:
        config = get_last_config()
        settings = config.get("settings", {})
        if settings.get("run_as_admin") == "on" and not is_admin():
            run_as_admin()
            sys.exit()
        app = AutoKeySenderApp()
        app.root.mainloop()
    except Exception as e:
        # Ghi log lỗi vào file
        with open("error_log.txt", "a", encoding='utf-8') as f:
            import traceback
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Unhandled exception:\n")
            traceback.print_exc(file=f)
            f.write("\n")
        # Hiển thị thông báo lỗi cho người dùng
        messagebox.showerror("Lỗi nghiêm trọng", f"Ứng dụng đã gặp lỗi không xác định và sẽ thoát.\n\nChi tiết: {e}\n\nVui lòng kiểm tra file error_log.txt.")
        sys.exit(1)
