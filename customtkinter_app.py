from tkinter_app import TkinterApp


class CustomTkinterApp(TkinterApp):
    def __init__(self):
        super().__init__()
        self.root.title(self.t("app_title"))