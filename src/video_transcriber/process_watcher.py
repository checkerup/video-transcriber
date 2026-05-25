import logging
import threading
import time

import psutil

from .config import AppConfig
from .pipeline import process_file
from .screen_recorder import is_recording, start_recording, stop_recording

logger = logging.getLogger(__name__)


def _find_process_by_name(name: str) -> bool:
    name_lower = name.lower()
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == name_lower:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def _find_process_by_names(names: list[str]) -> str | None:
    for name in names:
        name_lower = name.lower()
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == name_lower:
                    return name
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return None


def watch_processes(config: AppConfig, on_recording_done=None, stop_event: threading.Event | None = None) -> None:
    proc_cfg = getattr(config, "process_watcher", None)
    if not proc_cfg or not proc_cfg.program_names:
        logger.error("No process names configured for watching")
        return

    programs = proc_cfg.program_names
    poll_interval = proc_cfg.poll_interval

    logger.info("Process watcher started. Monitoring: %s (poll every %ds)", programs, poll_interval)

    was_running = False

    try:
        while not (stop_event and stop_event.is_set()):
            found = _find_process_by_names(programs)

            if found and not was_running:
                logger.info("Process '%s' detected — starting recording", found)
                output = start_recording(config)
                if output:
                    was_running = True
                else:
                    logger.error("Failed to start recording for '%s'", found)

            elif not found and was_running:
                logger.info("Target process exited — stopping recording")
                video_path = stop_recording()

                if video_path and on_recording_done:
                    logger.info("Triggering pipeline for: %s", video_path)
                    threading.Thread(
                        target=on_recording_done,
                        args=(video_path,),
                        daemon=True,
                    ).start()

                was_running = False

            for _ in range(poll_interval):
                if stop_event and stop_event.is_set():
                    break
                time.sleep(1)
    finally:
        if was_running:
            logger.info("Process watcher shutting down - stopping active recording gracefully")
            stop_recording()


def run_process_watcher(config: AppConfig, on_recording_done=None, stop_event: threading.Event | None = None) -> None:
    if on_recording_done is None:
        def _on_recording_done(video_path: str):
            try:
                # Note: this will become process_file in Task 7
                process_file(video_path, config)
            except Exception:
                logger.exception("Pipeline failed for recorded video: %s", video_path)
        on_recording_done = _on_recording_done

    watch_processes(config, on_recording_done=on_recording_done, stop_event=stop_event)
