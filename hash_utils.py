import hashlib
import threading
from pathlib import Path


def calculate_hash(path, algorithm="sha256", callback=None, cancel_event=None):
    path = Path(path)
    hasher = hashlib.new(algorithm.lower())
    total = path.stat().st_size
    processed = 0
    with path.open("rb") as source:
        while True:
            if cancel_event and cancel_event.is_set():
                return None
            block = source.read(4 * 1024 * 1024)
            if not block:
                break
            hasher.update(block)
            processed += len(block)
            if callback:
                callback(processed, total)
    return hasher.hexdigest()


def calculate_hash_async(path, algorithm, callback, finished, cancel_event=None):
    def worker():
        try:
            value = calculate_hash(path, algorithm, callback, cancel_event)
            finished(value, None)
        except Exception as exc:
            finished(None, exc)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread