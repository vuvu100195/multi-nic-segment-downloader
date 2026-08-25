import importlib.util
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from translations import tr

DEPENDENCIES = {
    "psutil": ("psutil", "Detect network interfaces and monitor speed."),
    "requests": ("requests", "Probe file size and HTTP Range support."),
}


def is_installed(module):
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


class DependencyManager:
    def __init__(self, parent, translate=lambda key, **kwargs: key):
        self.parent = parent
        self.t = translate
        self.window = None
        self.rows = {}

    def open(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.t("components_title"))
        self.window.geometry("700x260")
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=self.t("components_title"), font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(frame, text=self.t("restart_after_install")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 15))
        for row, (module, (package, description)) in enumerate(DEPENDENCIES.items(), 2):
            ttk.Label(frame, text=package, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8)
            ttk.Label(frame, text=description).grid(row=row, column=1, sticky="w", padx=15)
            status = ttk.Label(frame, width=12)
            status.grid(row=row, column=2, padx=8)
            button = ttk.Button(frame, width=12, command=lambda m=module: self.install(m))
            button.grid(row=row, column=3)
            self.rows[module] = (status, button)
            self.refresh(module)
        ttk.Label(frame, text=self.t("python_path", path=sys.executable), foreground="#555").grid(row=5, column=0, columnspan=4, sticky="w", pady=(14, 0))
        ttk.Button(frame, text=self.t("close"), command=self.close).grid(row=6, column=3, sticky="e", pady=(12, 0))

    def refresh(self, module):
        status, button = self.rows[module]
        if is_installed(module):
            status.configure(text=self.t("installed_label"), foreground="#16803c")
            button.configure(text=self.t("ready"), state="disabled")
        else:
            status.configure(text=self.t("not_installed_label"), foreground="#a15c00")
            button.configure(text=self.t("install"), state="normal")

    def install(self, module):
        package = DEPENDENCIES[module][0]
        status, button = self.rows[module]
        status.configure(text=self.t("installing"), foreground="#2563eb")
        button.configure(state="disabled")
        threading.Thread(target=self.worker, args=(module, package), daemon=True).start()

    def worker(self, module, package):
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            ok = result.returncode == 0 and is_installed(module)
            detail = (result.stderr or result.stdout or "").strip()[-2000:]
        except Exception as exc:
            ok, detail = False, str(exc)
        self.parent.after(0, lambda: self.finish(module, ok, detail))

    def finish(self, module, ok, detail):
        if not self.window or not self.window.winfo_exists():
            return
        self.refresh(module)
        if ok:
            messagebox.showinfo(self.t("success"), self.t("install_complete", package=DEPENDENCIES[module][0]), parent=self.window)
        else:
            self.rows[module][1].configure(text=self.t("retry_install"), state="normal")
            messagebox.showerror(self.t("install_failed"), detail or self.t("failure"), parent=self.window)

    def close(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None