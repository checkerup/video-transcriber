import logging
import os
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import AppConfig

logger = logging.getLogger(__name__)


class VideoFileHandler(FileSystemEventHandler):
    def __init__(self, config: AppConfig, queue: list[str], lock: threading.Lock):
        super().__init__()
        self.config = config
        self.queue = queue
        self.lock = lock
        self._timers: dict[str, threading.Timer] = {}

    def on_created(self, event):
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        if src_path.suffix.lower() not in self.config.watch.extensions:
            return

        logger.info("Detected new file: %s", src_path)

        if src_path.name in self._timers:
            self._timers[src_path.name].cancel()

        timer = threading.Timer(
            self.config.watch.delay_seconds,
            self._process_after_delay,
            args=[str(src_path)],
        )
        timer.daemon = True
        self._timers[src_path.name] = timer
        timer.start()

    def _process_after_delay(self, file_path: str):
        self._timers.pop(Path(file_path).name, None)

        if not self._is_file_stable(file_path):
            logger.warning("File not stable yet, re-queuing: %s", file_path)
            timer = threading.Timer(
                self.config.watch.delay_seconds,
                self._process_after_delay,
                args=[file_path],
            )
            timer.daemon = True
            self._timers[Path(file_path).name] = timer
            timer.start()
            return

        with self.lock:
            if file_path not in self.queue:
                self.queue.append(file_path)
                logger.info("Queued for processing: %s", file_path)

    @staticmethod
    def _is_file_stable(file_path: str, check_interval: float = 1.0, max_waits: int = 30) -> bool:
        try:
            size1 = os.path.getsize(file_path)
        except OSError:
            return False
        for _ in range(max_waits):
            time.sleep(check_interval)
            try:
                size2 = os.path.getsize(file_path)
            except OSError:
                return False
            if size1 == size2 and size1 > 0:
                return True
            size1 = size2
        return False


def start_watcher(config: AppConfig, queue: list[str], lock: threading.Lock) -> Observer:
    watch_dir = Path(config.watch.folder)
    watch_dir.mkdir(parents=True, exist_ok=True)

    handler = VideoFileHandler(config, queue, lock)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.daemon = True
    observer.start()
    logger.info("Watching folder: %s", watch_dir)
    return observer
