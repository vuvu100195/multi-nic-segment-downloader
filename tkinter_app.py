import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dependency_manager import DependencyManager
from hash_utils import calculate_hash_async
from network_utils import DownloadError, get_file_info, get_network_interfaces, has_module, make_bound_session, split_ranges, validate_url
from translations import TRANSLATIONS, normalize_language, tr

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def default_config():
    return {
        "language": "en",
        "output_dir": str(Path.home() / "Downloads"),
        "max_parallel_tasks": 1,
        "segments_per_interface": 2,
        "segment_max_retries": 5,
        "retry_delay_seconds": 3,
        "hash_algorithm": "SHA256",
        "selected_interfaces": [],
    }


def load_config():
    config = default_config()
    try:
        saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            config.update(saved)
    except (OSError, json.JSONDecodeError):
        pass
    config["language"] = normalize_language(config.get("language"))
    return config


def save_config(config):
    try:
        CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def safe_filename(value, fallback="download"):
    value = INVALID_FILENAME.sub("_", value or "").strip(" .")[:180]
    return fallback if not value or value.upper() in RESERVED_NAMES else value


def infer_filename(url):
    value = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    return safe_filename(value if "." in value else "download")


def format_bytes(value):
    try:
        value = max(0.0, float(value))
    except (TypeError, ValueError):
        return "0 B"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return "0 B"


def format_speed(value):
    return f"{format_bytes(value)}/s"


def format_eta(seconds):
    if seconds is None or seconds < 0:
        return "--"
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def interruptible_sleep(task, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if task.pause_event.is_set() or task.cancel_event.is_set():
            return False
        time.sleep(min(0.15, deadline - time.monotonic()))
    return True


@dataclass
class Segment:
    index: int
    part_index: int
    start: int
    end: int
    interface: dict
    path: Path
    status: str = "waiting"
    downloaded: int = 0
    speed_bps: float = 0.0
    error: str = ""
    retry_count: int = 0
    max_retries: int = 5

    @property
    def size(self):
        return self.end - self.start + 1


@dataclass
class NetworkPart:
    index: int
    interface: dict
    segments: list = field(default_factory=list)

    @property
    def downloaded(self):
        return sum(segment.downloaded for segment in self.segments)

    @property
    def total_size(self):
        return sum(segment.size for segment in self.segments)

    @property
    def complete_count(self):
        return sum(segment.status == "complete" for segment in self.segments)

    @property
    def retrying_count(self):
        return sum(segment.status == "retrying" for segment in self.segments)

    @property
    def error_count(self):
        return sum(segment.status == "error" for segment in self.segments)

    @property
    def speed_bps(self):
        return sum(segment.speed_bps for segment in self.segments)


@dataclass
class DownloadTask:
    number: int
    url: str
    output_dir: Path
    filename: str
    interfaces: list
    segments_per_interface: int
    max_retries: int
    retry_delay: int
    hash_algorithm: str
    status: str = "waiting"
    final_url: str = ""
    total_size: int = 0
    downloaded: int = 0
    speed_bps: float = 0.0
    error: str = ""
    parts: list = field(default_factory=list)
    pause_event: threading.Event = field(default_factory=threading.Event)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    hash_value: str = ""
    hash_status: str = "not_checked"
    hash_progress: int = 0
    hash_cancel_event: threading.Event = field(default_factory=threading.Event)

    @property
    def total_segments(self):
        return sum(len(part.segments) for part in self.parts)

    @property
    def completed_segments(self):
        return sum(part.complete_count for part in self.parts)


class DownloadManager:
    def __init__(self, on_change, max_parallel_tasks=1):
        self.on_change = on_change
        self.max_parallel_tasks = max(1, int(max_parallel_tasks))
        self.tasks = []
        self.lock = threading.RLock()

    def notify(self, task):
        self.on_change(task)

    def add(self, task):
        with self.lock:
            self.tasks.append(task)
            self.notify(task)
            self.start_waiting()

    def set_max_parallel_tasks(self, value):
        with self.lock:
            self.max_parallel_tasks = max(1, int(value))
            self.start_waiting()

    def active_count(self):
        return sum(task.status in {"downloading", "retrying", "merging", "hashing"} for task in self.tasks)

    def start_waiting(self):
        with self.lock:
            while self.active_count() < self.max_parallel_tasks:
                task = next((item for item in self.tasks if item.status == "waiting"), None)
                if task is None:
                    return
                task.status = "downloading"
                task.pause_event.clear()
                task.cancel_event.clear()
                threading.Thread(target=self.run_task, args=(task,), daemon=True).start()
                self.notify(task)

    def pause(self, task):
        if task.status in {"downloading", "retrying"}:
            task.pause_event.set()
            task.status = "paused"
            self.notify(task)
            self.start_waiting()

    def resume(self, task):
        if task.status not in {"paused", "stopped", "error"}:
            return
        task.error = ""
        task.pause_event.clear()
        task.cancel_event.clear()
        for part in task.parts:
            for segment in part.segments:
                if segment.status != "complete":
                    segment.status = "waiting"
        task.status = "waiting"
        self.notify(task)
        self.start_waiting()

    def stop(self, task):
        task.cancel_event.set()
        task.pause_event.clear()
        task.status = "stopped"
        self.notify(task)
        self.start_waiting()

    def run_task(self, task):
        try:
            task.output_dir.mkdir(parents=True, exist_ok=True)
            if not task.parts:
                self.initialize_task(task)
            if task.pause_event.is_set() or task.cancel_event.is_set():
                return
            workers = []
            for part in task.parts:
                for segment in part.segments:
                    if segment.status != "complete":
                        worker = threading.Thread(target=self.download_segment, args=(task, segment), daemon=True)
                        workers.append(worker)
                        worker.start()
            for worker in workers:
                worker.join()
            if task.pause_event.is_set() or task.cancel_event.is_set():
                return
            if any(segment.status != "complete" for part in task.parts for segment in part.segments):
                raise DownloadError("segment_failed")
            task.status = "merging"
            self.notify(task)
            final_path = self.merge_task(task)
            if final_path.stat().st_size != task.total_size:
                raise DownloadError("merge_size_mismatch")
            task.downloaded = task.total_size
            task.speed_bps = 0.0
            task.status = "complete"
            self.notify(task)
            self.start_hash(task)
        except Exception as exc:
            if not task.pause_event.is_set() and not task.cancel_event.is_set():
                task.status = "error"
                task.error = exc.code if isinstance(exc, DownloadError) else str(exc)
                self.notify(task)
        finally:
            self.start_waiting()

    def initialize_task(self, task):
        info = get_file_info(task.url)
        if task.pause_event.is_set() or task.cancel_event.is_set():
            return
        task.final_url = info["final_url"]
        task.total_size = info["size"]
        count = len(task.interfaces) * task.segments_per_interface
        ranges = split_ranges(task.total_size, count)
        if len(ranges) != count:
            raise DownloadError("file_too_small")
        task.parts = [NetworkPart(index=i, interface=interface) for i, interface in enumerate(task.interfaces)]
        for index, (start, end) in enumerate(ranges):
            part_index = index % len(task.interfaces)
            part = task.parts[part_index]
            segment = Segment(index, part_index, start, end, part.interface, task.output_dir / f".{task.filename}.segment-{index:04d}.part", max_retries=task.max_retries)
            if segment.path.is_file():
                try:
                    segment.downloaded = min(segment.path.stat().st_size, segment.size)
                except OSError:
                    segment.downloaded = 0
                if segment.downloaded == segment.size:
                    segment.status = "complete"
            part.segments.append(segment)
        self.refresh_progress(task)
        self.notify(task)

    def download_segment(self, task, segment):
        while not task.pause_event.is_set() and not task.cancel_event.is_set():
            try:
                self.download_segment_once(task, segment)
                if segment.status == "complete" or task.pause_event.is_set() or task.cancel_event.is_set():
                    return
                raise DownloadError("segment_failed")
            except Exception as exc:
                if task.pause_event.is_set() or task.cancel_event.is_set():
                    segment.status = "paused" if task.pause_event.is_set() else "stopped"
                    segment.speed_bps = 0.0
                    self.refresh_progress(task)
                    self.notify(task)
                    return
                segment.retry_count += 1
                segment.speed_bps = 0.0
                segment.error = exc.code if isinstance(exc, DownloadError) else str(exc)
                if segment.retry_count > segment.max_retries:
                    segment.status = "error"
                    self.refresh_progress(task)
                    self.notify(task)
                    return
                segment.status = "retrying"
                self.refresh_progress(task)
                self.notify(task)
                if not interruptible_sleep(task, task.retry_delay * min(segment.retry_count, 4)):
                    segment.status = "paused" if task.pause_event.is_set() else "stopped"
                    self.refresh_progress(task)
                    self.notify(task)
                    return

    def download_segment_once(self, task, segment):
        segment.status = "downloading"
        segment.error = ""
        self.notify(task)
        session = None
        try:
            session = make_bound_session(segment.interface["ip"])
            existing = segment.path.stat().st_size if segment.path.is_file() else 0
            if existing > segment.size:
                segment.path.unlink(missing_ok=True)
                existing = 0
            segment.downloaded = existing
            request_start = segment.start + existing
            if request_start > segment.end:
                segment.status = "complete"
                self.refresh_progress(task)
                self.notify(task)
                return
            headers = {"Range": f"bytes={request_start}-{segment.end}", "Accept-Encoding": "identity", "User-Agent": "MultiNIC-Downloader/1.0"}
            with session.get(task.final_url, headers=headers, stream=True, timeout=(15, 45)) as response:
                if response.status_code != 206:
                    raise DownloadError("range_not_supported")
                expected = f"bytes {request_start}-{segment.end}/"
                if not response.headers.get("Content-Range", "").lower().startswith(expected.lower()):
                    raise DownloadError("range_mismatch")
                with segment.path.open("ab") as output:
                    last_time = time.monotonic()
                    last_bytes = segment.downloaded
                    for block in response.iter_content(chunk_size=1024 * 1024):
                        if task.pause_event.is_set() or task.cancel_event.is_set():
                            break
                        if not block:
                            continue
                        output.write(block)
                        segment.downloaded += len(block)
                        now = time.monotonic()
                        if now - last_time >= 0.25:
                            segment.speed_bps = (segment.downloaded - last_bytes) / (now - last_time)
                            last_time, last_bytes = now, segment.downloaded
                            self.refresh_progress(task)
                            self.notify(task)
                if task.pause_event.is_set() or task.cancel_event.is_set():
                    segment.status = "paused" if task.pause_event.is_set() else "stopped"
                    segment.speed_bps = 0.0
                    self.refresh_progress(task)
                    self.notify(task)
                    return
                actual = segment.path.stat().st_size if segment.path.is_file() else 0
                if actual != segment.size:
                    raise DownloadError("received_bytes", actual=actual, expected=segment.size)
                segment.downloaded = actual
                segment.speed_bps = 0.0
                segment.status = "complete"
                self.refresh_progress(task)
                self.notify(task)
        finally:
            if session is not None:
                session.close()

    def refresh_progress(self, task):
        downloaded = 0
        speed = 0.0
        for part in task.parts:
            for segment in part.segments:
                if segment.path.is_file():
                    try:
                        segment.downloaded = min(segment.path.stat().st_size, segment.size)
                    except OSError:
                        pass
                downloaded += segment.downloaded
                speed += segment.speed_bps
        task.downloaded = min(downloaded, task.total_size)
        task.speed_bps = speed

    def merge_task(self, task):
        temporary = task.output_dir / f".{task.filename}.merging"
        final_path = task.output_dir / task.filename
        ordered = sorted((segment for part in task.parts for segment in part.segments), key=lambda segment: segment.index)
        with temporary.open("wb") as destination:
            for segment in ordered:
                with segment.path.open("rb") as source:
                    while True:
                        block = source.read(4 * 1024 * 1024)
                        if not block:
                            break
                        destination.write(block)
        temporary.replace(final_path)
        for segment in ordered:
            segment.path.unlink(missing_ok=True)
        return final_path

    def start_hash(self, task):
        task.status = "hashing"
        task.hash_status = "hashing"
        task.hash_progress = 0
        self.notify(task)
        calculate_hash_async(task.output_dir / task.filename, task.hash_algorithm, lambda done, total: self.hash_progress(task, done, total), lambda value, error: self.hash_finished(task, value, error), task.hash_cancel_event)

    def hash_progress(self, task, done, total):
        task.hash_progress = int(done / total * 100) if total else 0
        self.notify(task)

    def hash_finished(self, task, value, error):
        if error:
            task.hash_status = "hash_error"
        elif value:
            task.hash_value = value.upper()
            task.hash_status = f"{task.hash_algorithm}: {task.hash_value}"
        else:
            task.hash_status = "hash_cancelled"
        task.status = "complete"
        task.hash_progress = 100 if value else task.hash_progress
        self.notify(task)


class TkinterApp:
    def __init__(self):
        self.config = load_config()
        self.language = self.config["language"]
        self.root = tk.Tk()
        self.root.title(self.t("app_title"))
        self.root.geometry("1180x880")
        self.root.minsize(720, 520)
        self.events = queue.Queue()
        self.cards = {}
        self.interfaces = []
        self.interface_vars = []
        self.text_widgets = {}
        self.frame_widgets = {}
        self.option_labels = {}
        self.manager = DownloadManager(self.queue_event, self.config["max_parallel_tasks"])
        self.build_ui()
        self.refresh_interfaces()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.process_events()

    def t(self, key, **kwargs):
        return tr(self.language, key, **kwargs)

    def queue_event(self, task):
        self.events.put(task)

    def register_text(self, key, widget):
        self.text_widgets[key] = widget
        return widget

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        outer = ttk.Frame(self.root)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        self.main_canvas = tk.Canvas(outer, highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.main_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        main = ttk.Frame(self.main_canvas, padding=14)
        self.main_window = self.main_canvas.create_window((0, 0), window=main, anchor="nw")
        main.columnconfigure(0, weight=1)
        main.bind("<Configure>", lambda _: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<Configure>", lambda event: self.main_canvas.itemconfigure(self.main_window, width=event.width))

        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        self.register_text("app_title", ttk.Label(header, text=self.t("app_title"), font=("Segoe UI", 19, "bold"))).grid(row=0, column=0, sticky="w")
        self.register_text("subtitle", ttk.Label(header, text=self.t("subtitle"), foreground="#555")).grid(row=1, column=0, sticky="w", pady=(2, 0))
        lang_box = ttk.Frame(header)
        lang_box.grid(row=0, column=1, sticky="e")
        self.register_text("language", ttk.Label(lang_box, text=self.t("language"))).pack(side="left", padx=(0, 6))
        self.language_var = tk.StringVar(value=self.language)
        self.language_combo = ttk.Combobox(lang_box, textvariable=self.language_var, values=("en", "vi"), state="readonly", width=10)
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", self.change_language)

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value=self.config["output_dir"])
        self.filename_var = tk.StringVar()
        self.segments_var = tk.IntVar(value=max(1, int(self.config["segments_per_interface"])))
        self.parallel_var = tk.IntVar(value=max(1, int(self.config["max_parallel_tasks"])))
        self.retries_var = tk.IntVar(value=max(0, int(self.config["segment_max_retries"])))
        self.delay_var = tk.IntVar(value=max(1, int(self.config["retry_delay_seconds"])))
        self.hash_algorithm_var = tk.StringVar(value=self.config["hash_algorithm"])
        self.summary_var = tk.StringVar()

        form = ttk.LabelFrame(main, text=self.t("create_download"), padding=10)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self.frame_widgets["create_download"] = form
        self.add_field(form, 0, "direct_link", self.url_var)
        self.add_field(form, 1, "output_folder", self.output_var, self.choose_output)
        self.add_field(form, 2, "file_name", self.filename_var)

        options = ttk.Frame(form)
        options.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        option_specs = [
            ("segments_per_card", self.segments_var, 1, 16, 6),
            ("parallel_tasks", self.parallel_var, 1, 4, 6),
            ("retry_per_segment", self.retries_var, 0, 12, 5),
            ("retry_delay", self.delay_var, 1, 30, 5),
        ]
        for column, (key, variable, low, high, width) in enumerate(option_specs):
            base = column * 2
            label = ttk.Label(options, text=self.t(key))
            label.grid(row=0, column=base, sticky="w")
            self.option_labels[key] = label
            ttk.Spinbox(options, from_=low, to=high, textvariable=variable, width=width).grid(row=0, column=base + 1, padx=(6, 16))
        hash_label = ttk.Label(options, text=self.t("hash"))
        hash_label.grid(row=0, column=8, sticky="w")
        self.option_labels["hash"] = hash_label
        ttk.Combobox(options, textvariable=self.hash_algorithm_var, values=("SHA256", "SHA1", "MD5"), state="readonly", width=8).grid(row=0, column=9, padx=(6, 0))
        ttk.Label(options, textvariable=self.summary_var, foreground="#075985").grid(row=1, column=0, columnspan=10, sticky="w", pady=(7, 0))
        self.segments_var.trace_add("write", lambda *_: self.update_summary())
        self.parallel_var.trace_add("write", lambda *_: self.update_summary())

        nic_box = ttk.LabelFrame(main, text=self.t("network_cards"), padding=10)
        nic_box.grid(row=2, column=0, sticky="ew", pady=(10, 8))
        self.frame_widgets["network_cards"] = nic_box
        self.nic_list = ttk.Frame(nic_box)
        self.nic_list.grid(row=0, column=0, sticky="w")
        controls = ttk.Frame(nic_box)
        controls.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.register_text("rescan_cards", ttk.Button(controls, text=self.t("rescan_cards"), command=self.refresh_interfaces)).pack(side="left")
        self.register_text("diagnostics", ttk.Button(controls, text=self.t("diagnostics"), command=self.show_diagnostics)).pack(side="left", padx=7)
        self.register_text("components", ttk.Button(controls, text=self.t("components"), command=lambda: DependencyManager(self.root, self.t).open())).pack(side="left")
        self.nic_status = ttk.Label(controls)
        self.nic_status.pack(side="left", padx=12)

        self.register_text("note", ttk.Label(main, text=self.t("note"), foreground="#7c2d12")).grid(row=3, column=0, sticky="w", pady=(0, 7))

        queue_box = ttk.LabelFrame(main, text=self.t("queue"), padding=8)
        queue_box.grid(row=4, column=0, sticky="nsew")
        self.frame_widgets["queue"] = queue_box
        queue_box.columnconfigure(0, weight=1)
        queue_box.rowconfigure(0, weight=1)
        self.queue_canvas = tk.Canvas(queue_box, highlightthickness=0)
        self.queue_canvas.grid(row=0, column=0, sticky="nsew")
        queue_bar = ttk.Scrollbar(queue_box, orient="vertical", command=self.queue_canvas.yview)
        queue_bar.grid(row=0, column=1, sticky="ns")
        self.queue_canvas.configure(yscrollcommand=queue_bar.set)
        self.cards_frame = ttk.Frame(self.queue_canvas)
        self.queue_window = self.queue_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.bind("<Configure>", lambda _: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all")))
        self.queue_canvas.bind("<Configure>", lambda event: self.queue_canvas.itemconfigure(self.queue_window, width=event.width))

        bottom = ttk.Frame(main)
        bottom.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        bottom.columnconfigure(0, weight=1)
        self.register_text("add_queue", ttk.Button(bottom, text=self.t("add_queue"), command=self.add_download)).grid(row=0, column=0, sticky="ew")
        self.register_text("open_output", ttk.Button(bottom, text=self.t("open_output"), command=self.open_output)).grid(row=0, column=1, padx=7)
        self.register_text("save_settings", ttk.Button(bottom, text=self.t("save_settings"), command=self.persist_config)).grid(row=0, column=2, padx=7)
        self.register_text("exit", ttk.Button(bottom, text=self.t("exit"), command=self.close)).grid(row=0, column=3)

    def add_field(self, parent, row, key, variable, command=None):
        self.register_text(key, ttk.Label(parent, text=self.t(key))).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        if command:
            self.register_text(f"browse_{key}", ttk.Button(parent, text=self.t("browse"), command=command)).grid(row=row, column=2, padx=(7, 0), pady=4)

    def change_language(self, _event=None):
        self.language = normalize_language(self.language_var.get())
        self.persist_config()
        self.refresh_texts()

    def refresh_texts(self):
        self.root.title(self.t("app_title"))
        for key, widget in self.text_widgets.items():
            translation_key = "browse" if key.startswith("browse_") else key
            widget.configure(text=self.t(translation_key))
        for key, widget in self.frame_widgets.items():
            widget.configure(text=self.t(key))
        for key, widget in self.option_labels.items():
            widget.configure(text=self.t(key))
        self.update_summary()
        self.refresh_interfaces()
        for task in list(self.manager.tasks):
            self.refresh_card(task)

    def refresh_interfaces(self):
        selected_now = {interface["ip"] for variable, interface in self.interface_vars if variable.get()}
        selected = selected_now or set(self.config.get("selected_interfaces", []))
        for widget in self.nic_list.winfo_children():
            widget.destroy()
        self.interfaces = get_network_interfaces()
        self.interface_vars = []
        if not self.interfaces:
            ttk.Label(self.nic_list, text=self.t("no_cards"), foreground="#b45309").pack(anchor="w")
            self.nic_status.configure(text=self.t("no_cards"))
            self.update_summary()
            return
        for row, interface in enumerate(self.interfaces):
            variable = tk.BooleanVar(value=interface["ip"] in selected if selected else True)
            variable.trace_add("write", lambda *_: self.update_summary())
            self.interface_vars.append((variable, interface))
            ttk.Checkbutton(self.nic_list, text=f"{interface['name']} — {interface['ip']}", variable=variable).grid(row=row, column=0, sticky="w", pady=2)
        self.nic_status.configure(text=self.t("cards_found", count=len(self.interfaces)))
        self.update_summary()

    def selected_interfaces(self):
        return [interface for variable, interface in self.interface_vars if variable.get()]

    def update_summary(self):
        try:
            cards = len(self.selected_interfaces())
            segments = max(1, int(self.segments_var.get()))
            parallel = max(1, int(self.parallel_var.get()))
        except (ValueError, tk.TclError):
            self.summary_var.set(self.t("invalid_settings"))
            return
        total = cards * segments
        maximum = total * parallel
        warning = self.t("high_config") if maximum > 32 else ""
        self.summary_var.set(f"Cards: {cards} | Parts: {cards} | {self.t('segments')}/file: {total} | Max connections: {maximum}{warning}")

    def choose_output(self):
        path = filedialog.askdirectory(title=self.t("output_folder"))
        if path:
            self.output_var.set(path)

    def open_folder(self, path):
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except OSError as exc:
            messagebox.showerror(self.t("open_folder_error"), str(exc), parent=self.root)

    def open_output(self):
        self.open_folder(self.output_var.get().strip())

    def add_download(self):
        url = self.url_var.get().strip()
        output = self.output_var.get().strip()
        interfaces = self.selected_interfaces()
        try:
            segments = int(self.segments_var.get())
            parallel = int(self.parallel_var.get())
            retries = int(self.retries_var.get())
            delay = int(self.delay_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror(self.t("invalid_values"), self.t("value_limits"), parent=self.root)
            return
        if not validate_url(url):
            messagebox.showerror(self.t("link_not_supported"), self.t("http_only"), parent=self.root)
            return
        if not output or not interfaces:
            messagebox.showerror(self.t("missing_information"), self.t("need_folder_card"), parent=self.root)
            return
        if not 1 <= segments <= 16 or not 1 <= parallel <= 4 or not 0 <= retries <= 12 or not 1 <= delay <= 30:
            messagebox.showerror(self.t("invalid_values"), self.t("value_limits"), parent=self.root)
            return
        maximum = len(interfaces) * segments * parallel
        if maximum > 32 and not messagebox.askyesno(self.t("many_connections"), self.t("continue_question", count=maximum), parent=self.root):
            return
        filename = safe_filename(self.filename_var.get().strip() or infer_filename(url))
        self.manager.set_max_parallel_tasks(parallel)
        task = DownloadTask(len(self.manager.tasks) + 1, url, Path(output), filename, interfaces, segments, retries, delay, self.hash_algorithm_var.get())
        self.manager.add(task)
        self.url_var.set("")
        self.filename_var.set("")
        self.persist_config()

    def persist_config(self):
        try:
            segments = max(1, int(self.segments_var.get()))
            parallel = max(1, int(self.parallel_var.get()))
            retries = max(0, int(self.retries_var.get()))
            delay = max(1, int(self.delay_var.get()))
        except (ValueError, tk.TclError):
            segments, parallel, retries, delay = 2, 1, 5, 3
        self.config = {
            "language": self.language,
            "output_dir": self.output_var.get().strip(),
            "max_parallel_tasks": parallel,
            "segments_per_interface": segments,
            "segment_max_retries": retries,
            "retry_delay_seconds": delay,
            "hash_algorithm": self.hash_algorithm_var.get(),
            "selected_interfaces": [item["ip"] for item in self.selected_interfaces()],
        }
        save_config(self.config)

    def create_card(self, task):
        card = ttk.LabelFrame(self.cards_frame, text=self.t("task_number", number=task.number), padding=9)
        card.grid(row=len(self.cards), column=0, sticky="ew", pady=6)
        card.columnconfigure(0, weight=1)
        title = ttk.Label(card, font=("Segoe UI", 10, "bold"))
        title.grid(row=0, column=0, sticky="w")
        folder = ttk.Label(card, foreground="#555")
        folder.grid(row=1, column=0, sticky="w")
        status = ttk.Label(card)
        status.grid(row=2, column=0, sticky="w", pady=(4, 0))
        progress = ttk.Progressbar(card, maximum=100)
        progress.grid(row=3, column=0, sticky="ew", pady=5)
        details = ttk.Label(card)
        details.grid(row=4, column=0, sticky="w")
        hash_label = ttk.Label(card, foreground="#164e63", wraplength=1000)
        hash_label.grid(row=5, column=0, sticky="w", pady=(4, 0))
        parts = ttk.Label(card, foreground="#555", wraplength=1000, justify="left")
        parts.grid(row=6, column=0, sticky="w", pady=(3, 0))
        actions = ttk.Frame(card)
        actions.grid(row=7, column=0, sticky="w", pady=(7, 0))
        toggle = ttk.Button(actions, command=lambda item=task: self.toggle_task(item))
        toggle.pack(side="left")
        stop = ttk.Button(actions, command=lambda item=task: self.manager.stop(item))
        stop.pack(side="left", padx=6)
        copy = ttk.Button(actions, command=lambda item=task: self.copy_hash(item))
        copy.pack(side="left")
        folder_button = ttk.Button(actions, command=lambda item=task: self.open_folder(item.output_dir))
        folder_button.pack(side="left", padx=6)
        remove = ttk.Button(actions, command=lambda item=task: self.remove_task(item))
        remove.pack(side="left")
        self.cards[task.number] = {"frame": card, "title": title, "folder": folder, "status": status, "progress": progress, "details": details, "hash": hash_label, "parts": parts, "toggle": toggle, "stop": stop, "copy": copy, "folder_button": folder_button, "remove": remove}

    def refresh_card(self, task):
        if task.number not in self.cards:
            self.create_card(task)
        card = self.cards[task.number]
        card["frame"].configure(text=self.t("task_number", number=task.number))
        percent = task.downloaded / task.total_size * 100 if task.total_size else 0.0
        status_text = self.t(task.status) if task.status in TRANSLATIONS["en"] else task.status
        if task.error:
            status_text += f" — {self.t(task.error) if task.error in TRANSLATIONS['en'] else task.error}"
        eta = (task.total_size - task.downloaded) / task.speed_bps if task.speed_bps > 0 else None
        card["title"].configure(text=task.filename)
        card["folder"].configure(text=f"{self.t('save_to')}: {task.output_dir}")
        card["status"].configure(text=status_text)
        card["progress"].configure(value=percent)
        card["details"].configure(text=f"{percent:.1f}% | {format_bytes(task.downloaded)} / {format_bytes(task.total_size)} | {format_speed(task.speed_bps)} | ETA: {format_eta(eta)} | {self.t('segments')}: {task.completed_segments}/{task.total_segments}")
        if task.hash_value:
            hash_text = f"{task.hash_algorithm}: {task.hash_value}"
        else:
            hash_text = self.t(task.hash_status) if task.hash_status in TRANSLATIONS["en"] else task.hash_status
            if task.status == "hashing":
                hash_text += f" ({task.hash_progress}%)"
        card["hash"].configure(text=hash_text)
        lines = []
        for part in task.parts:
            part_percent = part.downloaded / part.total_size * 100 if part.total_size else 0.0
            states = []
            if part.retrying_count:
                states.append(self.t("retry_count", count=part.retrying_count))
            if part.error_count:
                states.append(self.t("error_count", count=part.error_count))
            suffix = f" | {', '.join(states)}" if states else ""
            lines.append(f"{self.t('part')} {part.index + 1} — {part.interface['name']} ({part.interface['ip']}): {part.complete_count}/{len(part.segments)} {self.t('segments')}, {part_percent:.1f}%, {format_speed(part.speed_bps)}{suffix}")
        card["parts"].configure(text="\n".join(lines) if lines else self.t("checking_range"))
        card["toggle"].configure(text=self.t("pause") if task.status in {"downloading", "retrying"} else self.t("resume"), state="normal" if task.status in {"downloading", "retrying", "paused", "stopped", "error"} else "disabled")
        card["stop"].configure(text=self.t("stop"), state="normal" if task.status in {"downloading", "retrying", "paused", "merging", "hashing"} else "disabled")
        card["copy"].configure(text=self.t("copy_hash"))
        card["folder_button"].configure(text=self.t("open_folder"))
        card["remove"].configure(text=self.t("remove_queue"))

    def copy_hash(self, task):
        if not task.hash_value:
            messagebox.showinfo(self.t("hash_unavailable"), self.t("hash_after_complete"), parent=self.root)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(task.hash_value)
        self.root.update()
        messagebox.showinfo(self.t("copied"), self.t("copied_hash", algorithm=task.hash_algorithm), parent=self.root)

    def remove_task(self, task):
        if task.status in {"downloading", "retrying", "merging", "hashing"}:
            messagebox.showwarning(self.t("cannot_remove"), self.t("remove_active"), parent=self.root)
            return
        if not messagebox.askyesno(self.t("remove_title"), self.t("remove_question", number=task.number), parent=self.root):
            return
        self.manager.tasks = [item for item in self.manager.tasks if item is not task]
        card = self.cards.pop(task.number, None)
        if card:
            card["frame"].destroy()

    def toggle_task(self, task):
        if task.status in {"downloading", "retrying"}:
            self.manager.pause(task)
        elif task.status in {"paused", "stopped", "error"}:
            self.manager.resume(task)

    def show_diagnostics(self):
        lines = [
            f"{self.t('python')}: {sys.executable}",
            f"{self.t('python_64')}: {sys.maxsize > 2**32}",
            f"requests: {self.t('installed') if has_module('requests') else self.t('not_installed')}",
            f"psutil: {self.t('installed') if has_module('psutil') else self.t('not_installed')}",
            "",
            f"{self.t('detected_cards')}",
        ]
        lines.extend(f"- {item['name']}: {item['ip']}" for item in self.interfaces)
        messagebox.showinfo(self.t("diagnostics_title"), "\n".join(lines), parent=self.root)

    def process_events(self):
        try:
            while True:
                self.refresh_card(self.events.get_nowait())
        except queue.Empty:
            pass
        self.root.after(200, self.process_events)

    def close(self):
        active = [task for task in self.manager.tasks if task.status in {"downloading", "retrying", "merging", "hashing"}]
        if active and not messagebox.askyesno(self.t("exit"), self.t("exit_question"), parent=self.root):
            return
        for task in active:
            self.manager.stop(task)
        self.persist_config()
        self.root.destroy()


if __name__ == "__main__":
    TkinterApp().root.mainloop()