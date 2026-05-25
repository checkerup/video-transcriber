import logging
import shutil
import subprocess
from pathlib import Path

from .config import AppConfig

logger = logging.getLogger(__name__)


def check_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Install it: https://ffmpeg.org/download.html "
            "or run: winget install FFmpeg"
        )
    return ffmpeg_path


def extract_audio(video_path: str, config: AppConfig) -> str:
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_dir = Path(config.processing.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_ext = config.processing.audio_format
    audio_path = output_dir / f"{video.stem}.{audio_ext}"

    ffmpeg_path = check_ffmpeg()

    cmd = [
        ffmpeg_path,
        "-i", str(video),
        "-vn",
    ]

    if getattr(config.processing, "silence_removal", False):
        cmd.extend(["-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"])
        if audio_ext == "mp3":
            codec = "libmp3lame"
        elif audio_ext == "wav":
            codec = "pcm_s16le"
        elif audio_ext in ("aac", "m4a"):
            codec = "aac"
        else:
            codec = "libmp3lame"
    else:
        codec = "libmp3lame" if audio_ext == "mp3" else "copy"

    cmd.extend([
        "-acodec", codec,
        "-ab", config.processing.audio_bitrate,
        "-y",
        str(audio_path),
    ])

    logger.info("Extracting audio: %s -> %s", video.name, audio_path.name)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr[:500])
        raise RuntimeError(f"FFmpeg failed (code {result.returncode}): {result.stderr[:200]}")

    logger.info("Audio extracted: %s (%s KB)", audio_path.name, audio_path.stat().st_size // 1024)
    return str(audio_path)


def convert_video_to_mp3(video_path: str, config: AppConfig) -> str:
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_dir = Path(config.processing.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / f"{video.stem}.mp3"
    ffmpeg_path = check_ffmpeg()

    cmd = [
        ffmpeg_path,
        "-i", str(video),
        "-vn",
    ]

    if getattr(config.processing, "silence_removal", False):
        cmd.extend(["-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"])

    cmd.extend([
        "-acodec", "libmp3lame",
        "-ab", config.processing.audio_bitrate,
        "-y",
        str(audio_path),
    ])

    logger.info("Converting video to MP3: %s -> %s", video.name, audio_path.name)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.error("FFmpeg stderr: %s", result.stderr[:500])
        raise RuntimeError(f"FFmpeg failed (code {result.returncode}): {result.stderr[:200]}")

    logger.info("Converted to MP3: %s (%s KB)", audio_path.name, audio_path.stat().st_size // 1024)
    return str(audio_path)


def copy_video_to_output(video_path: str, config: AppConfig) -> str:
    video = Path(video_path)
    output_dir = Path(config.processing.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    dest = output_dir / video.name
    if dest.exists():
        logger.info("Video already in output folder: %s", dest)
        return str(dest)

    logger.info("Copying video to output: %s", dest)
    shutil.copy2(str(video), str(dest))
    return str(dest)


def copy_audio_to_output(audio_path: str, config: AppConfig) -> str:
    audio = Path(audio_path)
    output_dir = Path(config.processing.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    dest = output_dir / audio.name
    if dest.exists():
        logger.info("Audio already in output folder: %s", dest)
        return str(dest)

    logger.info("Copying audio to output: %s", dest)
    shutil.copy2(str(audio), str(dest))
    return str(dest)

