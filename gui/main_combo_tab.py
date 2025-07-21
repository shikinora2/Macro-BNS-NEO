# gui/main_combo_tab.py
import customtkinter as ctk
from gui.constants import KEY_OPTIONS
from gui.better_scrollable_frame import BetterScrollableFrame # --- IMPORT MỚI ---

class ComboTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.combo_rows = [] # Sử dụng list để lưu các dòng combo

        # Frame chính chứa các nút điều khiển và scroll frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkButton(controls_frame, text="Thêm dòng", command=self._add_combo_row).pack(side="left", padx=10, pady=5)
        
        # --- THAY ĐỔI: Sử dụng BetterScrollableFrame ---
        self.scroll_frame = BetterScrollableFrame(main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        # Thêm một vài dòng mặc định khi khởi tạo
        for _ in range(4):
            self._add_combo_row()

    def _add_combo_row(self, key="", delay=""):
        """Tạo và thêm một dòng combo mới vào UI và list."""
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=4, padx=2)
        row_frame.grid_columnconfigure(1, weight=1)

        delay_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        delay_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(delay_frame, text="Delay:").pack(side="left", padx=(0, 2))
        delay_entry = ctk.CTkEntry(delay_frame, width=60, placeholder_text="delay")
        delay_entry.pack(side="left", fill="x", expand=True)
        delay_entry.insert(0, delay)
        ctk.CTkLabel(delay_frame, text="ms").pack(side="left", padx=(2, 0))

        key_combo = ctk.CTkComboBox(
            row_frame,
            values=KEY_OPTIONS,
            width=90,
            command=lambda choice, entry=delay_entry: self._on_key_select(choice, entry)
        )
        key_combo.set(key)
        key_combo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        remove_button = ctk.CTkButton(row_frame, text="Xóa", width=40, fg_color="#c95151",
                                       command=lambda rf=row_frame: self._remove_combo_row(rf))
        remove_button.grid(row=0, column=2, padx=5, pady=5)

        # Lưu trữ các widget của dòng này
        self.combo_rows.append({'frame': row_frame, 'key': key_combo, 'delay': delay_entry})

    def _remove_combo_row(self, row_frame):
        """Xóa một dòng combo khỏi UI và list."""
        # Tìm và xóa widget khỏi list
        for i, row_data in enumerate(self.combo_rows):
            if row_data['frame'] == row_frame:
                del self.combo_rows[i]
                break
        # Xóa widget khỏi giao diện
        row_frame.destroy()

    def _on_key_select(self, choice, delay_entry):
        if choice == "":
            delay_entry.delete(0, "end")

    def get_config(self):
        # Trả về một list các dictionaries
        return [
            {"key": row['key'].get(), "delay": row['delay'].get()}
            for row in self.combo_rows
        ]

    def set_config(self, data):
        # Xóa tất cả các dòng hiện có
        for row_data in self.combo_rows:
            row_data['frame'].destroy()
        self.combo_rows.clear()

        # Tạo lại các dòng từ dữ liệu đã lưu
        if not data: # Nếu không có data, tạo vài dòng trống
             for _ in range(4): self._add_combo_row()
             return

        for item in data:
            self._add_combo_row(key=item.get("key", ""), delay=item.get("delay", ""))
