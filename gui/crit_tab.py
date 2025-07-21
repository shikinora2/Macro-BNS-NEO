# gui/crit_tab.py
# --- SỬA LỖI ---
# Chuyển sang sử dụng import tương đối (relative import)
from .base_image_condition_tab import BaseImageConditionTab

class CritTab(BaseImageConditionTab):
    """
    Lớp cho Tab Crit.
    Kế thừa toàn bộ giao diện và logic từ BaseImageConditionTab.
    """
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, tab_name="Quy tắc Crit", **kwargs)
