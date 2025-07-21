# gui/sub_combo_tab.py
import customtkinter as ctk

from .mana_tab import ManaTab
from .hp_tab import HPTab  # <-- IMPORT MỚI
from .skill_tab import SkillTab
from .crit_tab import CritTab

class SubComboTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app

        tab_view = ctk.CTkTabview(self, corner_radius=8)
        tab_view.pack(fill="both", expand=True, padx=5, pady=5)

        # Thêm tab HP và đặt nó ở đầu tiên
        self.hp_tab = HPTab(master=tab_view.add("HP"), app=self.app)
        self.mana_tab = ManaTab(master=tab_view.add("Mana"), app=self.app)
        self.skill_tab = SkillTab(master=tab_view.add("Skill"), app=self.app)
        self.crit_tab = CritTab(master=tab_view.add("Crit"), app=self.app)
        
        self.hp_tab.pack(fill="both", expand=True)
        self.mana_tab.pack(fill="both", expand=True)
        self.skill_tab.pack(fill="both", expand=True)
        self.crit_tab.pack(fill="both", expand=True)

        tab_view.set("HP") # Đặt HP làm tab mặc định

    def get_config(self):
        return {
            "hp": self.hp_tab.get_config(), # <-- THÊM MỚI
            "mana": self.mana_tab.get_config(),
            "skill": self.skill_tab.get_config(),
            "crit": self.crit_tab.get_config()
        }

    def set_config(self, data):
        if not data: return
        self.hp_tab.set_config(data.get("hp", {})) # <-- THÊM MỚI
        self.mana_tab.set_config(data.get("mana", {}))
        self.skill_tab.set_config(data.get("skill", {}))
        self.crit_tab.set_config(data.get("crit", {}))
