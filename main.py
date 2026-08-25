import importlib.util
import sys
import tkinter as tk
from tkinter import messagebox


def module_exists(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def choose_interface():
    if module_exists("customtkinter"):
        try:
            from customtkinter_app import CustomTkinterApp
            return CustomTkinterApp
        except Exception as exc:
            print(f"Cannot load CustomTkinter interface: {exc}")

    try:
        from tkinter_app import TkinterApp
        return TkinterApp
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Cannot start application", str(exc))
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    AppClass = choose_interface()
    app = AppClass()
    app.root.mainloop()