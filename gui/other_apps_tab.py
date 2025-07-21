# gui/other_apps_tab.py
import customtkinter as ctk

class OtherAppsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        label = ctk.CTkLabel(self, text="Nội dung cho tab Ứng Dụng Khác", font=ctk.CTkFont(size=14))
        label.pack(pady=20, padx=20)

    def get_config(self):
        # Sẽ được phát triển trong tương lai
        return {}

    def set_config(self, data):
        # Sẽ được phát triển trong tương lai
        pass