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


def _as_bool(val, default: bool) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on")
    return bool(val)


def _as_int(val, default: int) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _as_list(val, default: list) -> list:
    if val is None:
        return default
    if isinstance(val, str):
        return [item.strip() for item in val.split(",") if item.strip()]
    if isinstance(val, list):
        return [str(item).strip() for item in val]
    return default


def _get_dict_section(raw: dict, name: str) -> dict:
    section = raw.get(name)
    return section if isinstance(section, dict) else {}


def load_config(config_path: str | Path | None = None, load_env_file: bool = True) -> AppConfig:
    project_root = Path(__file__).resolve().parent.parent.parent
    if load_env_file:
        load_dotenv(project_root / ".env")

    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    raw = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception:
            raw = {}
    if not isinstance(raw, dict):
        raw = {}

    watch_raw = _get_dict_section(raw, "watch")
    proc_raw = _get_dict_section(raw, "processing")
    trans_raw = _get_dict_section(raw, "transcription")
    tg_raw = _get_dict_section(raw, "telegram")
    rec_raw = _get_dict_section(raw, "recorder")
    pw_raw = _get_dict_section(raw, "process_watcher")

    bot_token = tg_raw.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN") or ""
    chat_id = tg_raw.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID") or ""

    device = _resolve_device(trans_raw.get("device") or "auto")

    default_watch = WatchConfig()
    default_proc = ProcessingConfig()
    default_trans = TranscriptionConfig()
    default_rec = RecorderConfig()
    default_pw = ProcessWatcherConfig()

    watch_folder = os.path.expanduser(str(watch_raw.get("folder") or default_watch.folder))
    output_folder = os.path.expanduser(str(proc_raw.get("output_folder") or default_proc.output_folder))

    delay_seconds = _as_int(watch_raw.get("delay_seconds"), default_watch.delay_seconds)
    keep_audio = _as_bool(proc_raw.get("keep_audio"), default_proc.keep_audio)
    word_timestamps = _as_bool(trans_raw.get("word_timestamps"), default_trans.word_timestamps)
    fps = _as_int(rec_raw.get("fps"), default_rec.fps)
    poll_interval = _as_int(pw_raw.get("poll_interval"), default_pw.poll_interval)

    cfg = AppConfig(
        watch=WatchConfig(
            folder=watch_folder,
            extensions=_as_list(watch_raw.get("extensions"), default_watch.extensions),
            delay_seconds=delay_seconds,
        ),
        processing=ProcessingConfig(
            output_folder=output_folder,
            audio_format=proc_raw.get("audio_format") or default_proc.audio_format,
            audio_bitrate=proc_raw.get("audio_bitrate") or default_proc.audio_bitrate,
            keep_audio=keep_audio,
        ),
        transcription=TranscriptionConfig(
            model_size=trans_raw.get("model_size") or default_trans.model_size,
            device=device,
            compute_type=trans_raw.get("compute_type") or default_trans.compute_type,
            language=trans_raw.get("language") or default_trans.language,
            output_format=trans_raw.get("output_format") or default_trans.output_format,
            word_timestamps=word_timestamps,
        ),
        telegram=TelegramConfig(
            bot_token=bot_token,
            chat_id=chat_id,
        ),
        recorder=RecorderConfig(
            fps=fps,
            video_size=rec_raw.get("video_size") if rec_raw.get("video_size") is not None else default_rec.video_size,
        ),
        process_watcher=ProcessWatcherConfig(
            program_names=_as_list(pw_raw.get("program_names"), default_pw.program_names),
            poll_interval=poll_interval,
        ),
    )

    return cfg
