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
class AppConfig:
    watch: WatchConfig = field(default_factory=WatchConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def load_config(config_path: str | Path | None = None) -> AppConfig:
    load_dotenv()

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

    bot_token = tg_raw.get("bot_token", "") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = tg_raw.get("chat_id", "") or os.getenv("TELEGRAM_CHAT_ID", "")

    device = _resolve_device(trans_raw.get("device", "auto"))

    cfg = AppConfig(
        watch=WatchConfig(
            folder=watch_raw.get("folder", WatchConfig.folder),
            extensions=watch_raw.get("extensions", WatchConfig.extensions),
            delay_seconds=watch_raw.get("delay_seconds", WatchConfig.delay_seconds),
        ),
        processing=ProcessingConfig(
            output_folder=proc_raw.get("output_folder", ProcessingConfig.output_folder),
            audio_format=proc_raw.get("audio_format", ProcessingConfig.audio_format),
            audio_bitrate=proc_raw.get("audio_bitrate", ProcessingConfig.audio_bitrate),
            keep_audio=proc_raw.get("keep_audio", ProcessingConfig.keep_audio),
        ),
        transcription=TranscriptionConfig(
            model_size=trans_raw.get("model_size", TranscriptionConfig.model_size),
            device=device,
            compute_type=trans_raw.get("compute_type", TranscriptionConfig.compute_type),
            language=trans_raw.get("language", TranscriptionConfig.language),
            output_format=trans_raw.get("output_format", TranscriptionConfig.output_format),
            word_timestamps=trans_raw.get("word_timestamps", TranscriptionConfig.word_timestamps),
        ),
        telegram=TelegramConfig(
            bot_token=bot_token,
            chat_id=chat_id,
        ),
    )

    Path(cfg.watch.folder).mkdir(parents=True, exist_ok=True)
    Path(cfg.processing.output_folder).mkdir(parents=True, exist_ok=True)

    return cfg
