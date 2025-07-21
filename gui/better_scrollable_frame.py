import customtkinter as ctk
import sys

class BetterScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._parent_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._parent_canvas.bind("<Button-4>", self._on_mousewheel)
        self._parent_canvas.bind("<Button-5>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        if not self.winfo_ismapped() or self.winfo_toplevel().focus_get() != self._parent_canvas:
            return
        if not self._is_mouse_over_widget(event):
            return

        if event.num == "??": 
            if sys.platform.startswith("win"):
                self._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif sys.platform.startswith("darwin"):
                self._parent_canvas.yview_scroll(int(-1 * event.delta), "units")
            return

        if event.num == 4:
            self._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._parent_canvas.yview_scroll(1, "units")

    def _is_mouse_over_widget(self, event):
        widget_x = self.winfo_rootx()
        widget_y = self.winfo_rooty()
        widget_width = self.winfo_width()
        widget_height = self.winfo_height()

        pointer_x = event.x_root
        pointer_y = event.y_root

        return (widget_x <= pointer_x < widget_x + widget_width) and \
               (widget_y <= pointer_y < widget_y + widget_height)