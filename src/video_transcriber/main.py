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


def _signal_handler(sig, frame):
    logger.info("Shutdown signal received (%s)", sig)
    shutdown_event.set()


def run_once(config, video_path: str):
    result = process_video(video_path, config)
    if result["error"]:
        logger.error("Failed: %s", result["error"])
        sys.exit(1)
    logger.info("Done. Transcript: %s", result["transcript"])


def run_daemon(config):
    observer = start_watcher(config, lambda p: _on_new_file(p, config), queue, lock)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info("Video Transcriber daemon running. Press Ctrl+C to stop.")
    logger.info("Watching: %s", config.watch.folder)
    logger.info("Output: %s", config.processing.output_folder)

    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    observer.stop()
    observer.join(timeout=5)
    logger.info("Stopped.")


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
    else:
        run_daemon(config)


if __name__ == "__main__":
    main()
