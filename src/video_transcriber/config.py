import os
import platform
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


def _default_videos_dir() -> Path:
    home = Path.home()
    if platform.system() == "Windows":
        videos = home / "Videos"
    else:
        videos = home / "Videos" if (home / "Videos").exists() else home / "videos"
    if not videos.exists():
        videos = home / "Videos"
        videos.mkdir(exist_ok=True)
    return videos


_DEFAULT_WATCH = str(_default_videos_dir() / "Incoming")
_DEFAULT_OUTPUT = str(_default_videos_dir() / "Processed")


@dataclass
class WatchConfig:
    folder: str = _DEFAULT_WATCH
    extensions: list[str] = field(default_factory=lambda: [".mp4", ".mkv", ".avi", ".mov", ".webm"])
    delay_seconds: int = 10


@dataclass
class ProcessingConfig:
    output_folder: str = _DEFAULT_OUTPUT
    audio_format: str = "mp3"
    audio_bitrate: str = "192k"
    keep_audio: bool = True


@dataclass
class TranscriptionConfig:
    model_size: str = "base"
    device: str = "auto"
    compute_type: str = "int8"
    language: str = "ru"
    output_format: str = "txt"
    word_timestamps: bool = True


@dataclass
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class RecorderConfig:
    fps: int = 30
    video_size: str | None = None


@dataclass
class ProcessWatcherConfig:
    program_names: list[str] = field(default_factory=list)
    poll_interval: int = 5


@dataclass
class AppConfig:
    watch: WatchConfig = field(default_factory=WatchConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    recorder: RecorderConfig = field(default_factory=RecorderConfig)
    process_watcher: ProcessWatcherConfig = field(default_factory=ProcessWatcherConfig)


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def load_config(config_path: str | Path | None = None) -> AppConfig:
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(project_root / ".env")

    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    raw: dict = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    watch_raw = raw.get("watch", {})
    proc_raw = raw.get("processing", {})
    trans_raw = raw.get("transcription", {})
    tg_raw = raw.get("telegram", {})
    rec_raw = raw.get("recorder", {})
    pw_raw = raw.get("process_watcher", {})

    bot_token = tg_raw.get("bot_token", "") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = tg_raw.get("chat_id", "") or os.getenv("TELEGRAM_CHAT_ID", "")

    device = _resolve_device(trans_raw.get("device", "auto"))

    default_watch = WatchConfig()
    default_proc = ProcessingConfig()
    default_trans = TranscriptionConfig()
    default_rec = RecorderConfig()
    default_pw = ProcessWatcherConfig()

    watch_folder = os.path.expanduser(watch_raw.get("folder", default_watch.folder))
    output_folder = os.path.expanduser(proc_raw.get("output_folder", default_proc.output_folder))

    cfg = AppConfig(
        watch=WatchConfig(
            folder=watch_folder,
            extensions=watch_raw.get("extensions", default_watch.extensions),
            delay_seconds=watch_raw.get("delay_seconds", default_watch.delay_seconds),
        ),
        processing=ProcessingConfig(
            output_folder=output_folder,
            audio_format=proc_raw.get("audio_format", default_proc.audio_format),
            audio_bitrate=proc_raw.get("audio_bitrate", default_proc.audio_bitrate),
            keep_audio=proc_raw.get("keep_audio", default_proc.keep_audio),
        ),
        transcription=TranscriptionConfig(
            model_size=trans_raw.get("model_size", default_trans.model_size),
            device=device,
            compute_type=trans_raw.get("compute_type", default_trans.compute_type),
            language=trans_raw.get("language", default_trans.language),
            output_format=trans_raw.get("output_format", default_trans.output_format),
            word_timestamps=trans_raw.get("word_timestamps", default_trans.word_timestamps),
        ),
        telegram=TelegramConfig(
            bot_token=bot_token,
            chat_id=chat_id,
        ),
        recorder=RecorderConfig(
            fps=rec_raw.get("fps", default_rec.fps),
            video_size=rec_raw.get("video_size", default_rec.video_size),
        ),
        process_watcher=ProcessWatcherConfig(
            program_names=pw_raw.get("program_names", default_pw.program_names),
            poll_interval=pw_raw.get("poll_interval", default_pw.poll_interval),
        ),
    )

    Path(cfg.watch.folder).mkdir(parents=True, exist_ok=True)
    Path(cfg.processing.output_folder).mkdir(parents=True, exist_ok=True)

    return cfg
