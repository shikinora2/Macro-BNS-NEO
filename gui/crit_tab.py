# gui/crit_tab.py
from gui.base_image_condition_tab import BaseImageConditionTab

class CritTab(BaseImageConditionTab):
    """
    Lớp cho Tab Crit.
    Kế thừa toàn bộ giao diện và logic từ BaseImageConditionTab.
    """
    def __init__(self, master, app, **kwargs):
        # Chỉ cần gọi lớp cha và truyền vào tên của tab này là "Quy tắc Crit"
        super().__init__(master, app, tab_name="Quy tắc Crit", **kwargs)

