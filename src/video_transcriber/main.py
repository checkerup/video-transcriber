import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from .autostart import install_autostart, is_autostart_installed, uninstall_autostart
from .config import load_config
from .hardware import detect_hardware, print_hardware_report
from .pipeline import process_video
from .process_watcher import run_process_watcher
from .screen_recorder import start_recording, stop_recording
from .setup_wizard import is_setup_done, run_setup_wizard
from .watcher import start_watcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("video_transcriber")

queue: list[str] = []
lock = threading.Lock()
shutdown_event = threading.Event()


def _on_new_file(file_path: str, config):
    try:
        process_video(file_path, config)
    except Exception:
        logger.exception("Unhandled error processing: %s", file_path)


def _enqueue_file(file_path: str):
    with lock:
        if file_path not in queue:
            queue.append(file_path)
            logger.info("Queued for processing: %s", file_path)


def _signal_handler(sig, frame):
    logger.info("Shutdown signal received (%s)", sig)
    shutdown_event.set()


def queue_worker(queue: list[str], lock: threading.Lock, config, callback):
    while not shutdown_event.is_set():
        file_path = None
        with lock:
            if queue:
                file_path = queue.pop(0)
        if file_path:
            try:
                callback(file_path, config)
            except Exception:
                logger.exception("Error processing queued file: %s", file_path)
        else:
            time.sleep(0.1)


def run_once(config, video_path: str):
    result = process_video(video_path, config)
    if result["error"]:
        logger.error("Failed: %s", result["error"])
        sys.exit(1)
    logger.info("Done. Transcript: %s", result["transcript"])


def run_daemon(config):
    has_pw = config.process_watcher and config.process_watcher.program_names

    if has_pw:
        pw_thread = threading.Thread(
            target=run_process_watcher,
            args=(config, _enqueue_file, shutdown_event),
            daemon=True,
        )
        pw_thread.start()
        logger.info("Process watcher: monitoring %s", config.process_watcher.program_names)

    # Start queue worker thread
    worker_thread = threading.Thread(
        target=queue_worker,
        args=(queue, lock, config, _on_new_file),
        daemon=True
    )
    worker_thread.start()

    observer, handler = start_watcher(config, queue, lock)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info("Video Transcriber daemon running. Press Ctrl+C to stop.")
    logger.info("Watching: %s", config.watch.folder)
    logger.info("Output: %s", config.processing.output_folder)
    if has_pw:
        logger.info("Process watcher: %s", config.process_watcher.program_names)

    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    observer.stop()
    handler.cleanup()
    observer.join(timeout=5)
    worker_thread.join(timeout=5)
    if has_pw:
        pw_thread.join(timeout=5)
    logger.info("Stopped.")


def run_record(config):
    logger.info("Starting manual screen recording...")
    output = start_recording(config)
    if not output:
        logger.error("Failed to start recording")
        sys.exit(1)

    logger.info("Recording to: %s", output)
    logger.info("Press Ctrl+C to stop recording")

    signal.signal(signal.SIGINT, _signal_handler)
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    video_path = stop_recording()
    if video_path:
        logger.info("Recording saved: %s", video_path)
        result = process_video(video_path, config)
        if result["error"]:
            logger.error("Pipeline failed: %s", result["error"])
        else:
            logger.info("Done. Transcript: %s", result["transcript"])


def main():
    parser = argparse.ArgumentParser(
        description="Video Transcriber — auto-transcribe videos with Telegram notifications",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    parser.add_argument("--file", type=str, default=None, help="Process a single video file (one-shot mode)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--install-autostart", action="store_true", help="Install as autostart service")
    parser.add_argument("--uninstall-autostart", action="store_true", help="Remove autostart service")
    parser.add_argument("--check-hardware", action="store_true", help="Detect hardware and print report")
    parser.add_argument("--record", action="store_true", help="Manual screen recording mode (Ctrl+C to stop)")
    parser.add_argument(
        "--watch-process", type=str, default=None,
        help="Watch for process name and auto-record (e.g. 'Zoom.exe')",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config_path = Path(args.config) if args.config else None
    project_root = Path(__file__).resolve().parent.parent.parent

    if args.check_hardware:
        hw = detect_hardware()
        print_hardware_report(hw)
        return

    if args.install_autostart:
        ok = install_autostart(config_path=config_path)
        print("Autostart installed." if ok else "Autostart installation failed.")
        return

    if args.uninstall_autostart:
        ok = uninstall_autostart()
        print("Autostart removed." if ok else "Autostart removal failed.")
        return

    if args.setup or not is_setup_done(project_root):
        if not is_setup_done(project_root):
            logger.info("First run detected — launching setup wizard")
        run_setup_wizard(config_path=config_path if config_path else project_root / "config.yaml")
        if args.setup:
            return

    config = load_config(args.config)

    # Ensure watch and output folders exist
    Path(config.watch.folder).mkdir(parents=True, exist_ok=True)
    Path(config.processing.output_folder).mkdir(parents=True, exist_ok=True)

    if args.watch_process:
        config.process_watcher.program_names = [p.strip() for p in args.watch_process.split(",")]
        logger.info("CLI override: watching processes %s", config.process_watcher.program_names)

    hw = detect_hardware()
    logger.info(
        "Hardware: %s, RAM=%.1fGB, GPU=%s, model=%s/%s",
        hw.os_name, hw.ram_gb,
        hw.gpu_name if hw.has_cuda else "none",
        config.transcription.model_size,
        config.transcription.device,
    )

    if args.file:
        run_once(config, args.file)
    elif args.record:
        run_record(config)
    else:
        run_daemon(config)


if __name__ == "__main__":
    main()
