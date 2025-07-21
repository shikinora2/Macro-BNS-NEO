# gui/skill_tab.py
from .base_image_condition_tab import BaseImageConditionTab

class SkillTab(BaseImageConditionTab):
    """
    Lớp cho Tab Skill.
    Kế thừa toàn bộ giao diện và logic từ BaseImageConditionTab.
    """
    def __init__(self, master, app, **kwargs):
        # Chỉ cần gọi lớp cha và truyền vào tên của tab này là "Quy tắc Skill"
        super().__init__(master, app, tab_name="Quy tắc Skill", **kwargs)
