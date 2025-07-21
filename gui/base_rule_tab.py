# gui/base_rule_tab.py
import customtkinter as ctk
from .constants import KEY_OPTIONS
from .better_scrollable_frame import BetterScrollableFrame

class BaseRuleTab(ctk.CTkFrame):
    """
    Lớp cơ sở chung nhất cho một tab chứa danh sách các quy tắc.
    Chịu trách nhiệm tạo khung sườn và quản lý panel.
    Các lớp con phải tự định nghĩa phần 'Điều kiện' và 'Hành động'.
    """
    def __init__(self, master, app, tab_name="Quy tắc", **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.tab_name = tab_name
        self.panels = []
        self.panel_count = 0

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(controls_frame, text="Thêm Quy Tắc Mới", command=self.add_new_panel).pack(side="left", padx=10, pady=5)

        self.scroll_frame = BetterScrollableFrame(main_frame, label_text=f"Danh sách {self.tab_name}")
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Thêm một panel mặc định khi khởi tạo
        self.add_new_panel()

    def add_new_panel(self, config=None):
        """Thêm một panel quy tắc mới vào giao diện."""
        self.panel_count += 1
        panel_id = f"{self.tab_name.lower().replace(' ', '_')}_{self.panel_count}"
        if config is None: config = {}
        
        # Lớp con sẽ định nghĩa _create_single_panel để tạo giao diện và dữ liệu
        panel_frame, panel_data = self._create_single_panel(self.scroll_frame, panel_id, config)
        self.panels.append({'id': panel_id, 'frame': panel_frame, 'data': panel_data})

    def _remove_panel(self, panel_id):
        """Xóa một panel quy tắc khỏi giao diện."""
        panel_to_remove = next((panel for panel in self.panels if panel['id'] == panel_id), None)
        if panel_to_remove:
            panel_to_remove['frame'].destroy()
            self.panels.remove(panel_to_remove)

    def _add_skill_row(self, parent, skill_rows_list, key="", delay=""):
        """
        Thêm một dòng kỹ năng (hành động) vào một container cha.
        Hàm này giờ linh hoạt hơn, nhận vào một list cụ thể để thêm vào.
        """
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        key_combo = ctk.CTkComboBox(row_frame, values=KEY_OPTIONS, width=70)
        key_combo.set(key)
        key_combo.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(row_frame, text="Delay:").pack(side="left")
        delay_entry = ctk.CTkEntry(row_frame, width=50, placeholder_text="ms")
        delay_entry.insert(0, str(delay)) # Dùng str() để đảm bảo an toàn
        delay_entry.pack(side="left", padx=5)
        
        row_widgets = {'frame': row_frame, 'key': key_combo, 'delay': delay_entry}
        
        remove_button = ctk.CTkButton(row_frame, text="Xóa", width=40, height=20, fg_color="#c95151",
                                       command=lambda sl=skill_rows_list, rw=row_widgets: self._remove_skill_row(sl, rw))
        remove_button.pack(side="left", padx=5)
        
        skill_rows_list.append(row_widgets)

    def _remove_skill_row(self, skill_rows_list, row_widgets):
        """Xóa một dòng kỹ năng khỏi UI và khỏi list tương ứng."""
        row_widgets['frame'].destroy()
        if row_widgets in skill_rows_list:
            skill_rows_list.remove(row_widgets)

    # --- Các phương thức trừu tượng mà lớp con PHẢI định nghĩa ---
    def _create_single_panel(self, parent, panel_id, config):
        """Lớp con phải triển khai để tạo toàn bộ một panel."""
        raise NotImplementedError

    def _create_condition_panel(self, parent, panel_id, panel_data):
        """Lớp con phải triển khai để tạo giao diện cho phần 'Điều kiện'."""
        raise NotImplementedError

    def get_config(self):
        """Lớp con phải triển khai để lấy cấu hình."""
        raise NotImplementedError

    def set_config(self, data):
        """Lớp con phải triển khai để thiết lập cấu hình."""
        for panel in self.panels:
            panel['frame'].destroy()
        self.panels.clear()
        self.panel_count = 0
        rules_data = data.get("rules", [])
        if not rules_data:
            self.add_new_panel()
            return
        for conf in rules_data:
            self.add_new_panel(config=conf)
