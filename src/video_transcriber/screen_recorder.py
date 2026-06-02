import logging
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AppConfig

logger = logging.getLogger(__name__)

_current_recording: subprocess.Popen | None = None
_current_output: str | None = None
_recording_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Windows audio helpers
# ---------------------------------------------------------------------------

def _windows_default_mic() -> str | None:
    """Pick the first available dshow audio input device as the default mic."""
    try:
        from .audio_devices import list_dshow_audio_inputs
        devs = list_dshow_audio_inputs()
        return devs[0] if devs else None
    except Exception as e:
        logger.debug("Could not enumerate dshow audio inputs: %s", e)
        return None


def _windows_default_system_loopback() -> str | None:
    """Pick the first Stereo-Mix / loopback-looking device, if any."""
    try:
        from .audio_devices import list_dshow_audio_inputs
        devs = list_dshow_audio_inputs()
        for name in devs:
            low = name.lower()
            if "stereo mix" in low or "loopback" in low or "what u hear" in low or "what you hear" in low:
                return name
        return None
    except Exception as e:
        logger.debug("Could not enumerate dshow audio inputs: %s", e)
        return None


# ---------------------------------------------------------------------------
# FFmpeg command builders
# ---------------------------------------------------------------------------

def _windows_cmd(output_path: str, config: AppConfig) -> list[str]:
    rec = config.recorder
    fps = rec.fps
    mode = rec.audio_mode

    cmd: list[str] = ["ffmpeg"]

    # Video input (screen).
    cmd += ["-f", "gdigrab", "-framerate", str(fps), "-i", "desktop"]

    audio_inputs: list[str] = []
    if mode in ("mic", "both"):
        mic = rec.mic_device or _windows_default_mic()
        if mic:
            cmd += ["-f", "dshow", "-i", f"audio={mic}"]
            audio_inputs.append(mic)
        else:
            logger.warning("audio_mode=%s but no microphone found — video-only fallback", mode)

    if mode in ("system", "both"):
        sys_dev = rec.system_device or _windows_default_system_loopback()
        if sys_dev:
            cmd += ["-f", "dshow", "-i", f"audio={sys_dev}"]
            audio_inputs.append(sys_dev)
        else:
            logger.warning("audio_mode=%s but no system-loopback device found "
                           "(enable 'Stereo Mix' in Sound settings) — video-only fallback", mode)

    # Mix multiple audio inputs into a single AAC track.
    if len(audio_inputs) >= 2:
        cmd += [
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
        ]
    elif len(audio_inputs) == 1:
        cmd += [
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
        ]
    else:
        cmd += [
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
        ]

    cmd += [
        "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
        "-y", output_path,
    ]
    return cmd


def _macos_cmd(output_path: str, config: AppConfig) -> list[str]:
    rec = config.recorder
    fps = rec.fps
    mode = rec.audio_mode

    video_idx = "1"
    audio_idx = rec.mic_device or "0"  # macOS uses indices; default = 0
    if mode == "none":
        spec = f"{video_idx}"
    else:
        spec = f"{video_idx}:{audio_idx}"

    return [
        "ffmpeg",
        "-f", "avfoundation",
        "-framerate", str(fps),
        "-i", spec,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
        *(["-c:a", "aac", "-b:a", "192k"] if mode != "none" else []),
        "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
        "-y", output_path,
    ]


def _linux_cmd(output_path: str, config: AppConfig) -> list[str]:
    rec = config.recorder
    fps = rec.fps
    mode = rec.audio_mode
    display = ":0.0"
    size = rec.video_size or "1920x1080"

    cmd: list[str] = [
        "ffmpeg",
        "-f", "x11grab", "-framerate", str(fps), "-video_size", size, "-i", display,
    ]

    pulse_inputs: list[str] = []
    if mode in ("mic", "both") and rec.mic_device:
        cmd += ["-f", "pulse", "-i", rec.mic_device]
        pulse_inputs.append(rec.mic_device)
    elif mode in ("mic", "both"):
        cmd += ["-f", "pulse", "-i", "default"]
        pulse_inputs.append("default")

    if mode in ("system", "both"):
        sys_dev = rec.system_device or "@DEFAULT_MONITOR@"
        cmd += ["-f", "pulse", "-i", sys_dev]
        pulse_inputs.append(sys_dev)

    if len(pulse_inputs) >= 2:
        cmd += [
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
        ]
    elif len(pulse_inputs) == 1:
        cmd += [
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
        ]
    else:
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p"]

    cmd += ["-movflags", "+frag_keyframe+empty_moov+default_base_moof", "-y", output_path]
    return cmd


def _ffmpeg_record_cmd(output_path: str, config: AppConfig) -> list[str]:
    os_name = platform.system()
    if os_name == "Windows":
        return _windows_cmd(output_path, config)
    if os_name == "Darwin":
        return _macos_cmd(output_path, config)
    return _linux_cmd(output_path, config)


# ---------------------------------------------------------------------------
# Public API — start / stop / status
# ---------------------------------------------------------------------------

def start_recording(config: AppConfig) -> str | None:
    global _current_recording, _current_output

    with _recording_lock:
        if _current_recording is not None and _current_recording.poll() is None:
            logger.warning("Recording already in progress: %s", _current_output)
            return _current_output

        output_dir = Path(config.processing.output_folder).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = str(output_dir / f"screen_{timestamp}.mp4")

        cmd = _ffmpeg_record_cmd(output_path, config)
        logger.info("Starting screen recording: %s", output_path)
        logger.debug("FFmpeg cmd: %s", " ".join(cmd))

        try:
            popen_kw: dict[str, Any] = dict(
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if sys.platform == "win32":
                popen_kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

            _current_recording = subprocess.Popen(cmd, **popen_kw)
            _current_output = output_path

            time.sleep(1)
            if _current_recording.poll() is not None:
                stderr = _current_recording.stderr.read().decode(errors="replace")[:500]
                logger.error("FFmpeg exited immediately: %s", stderr)
                _current_recording = None
                _current_output = None
                return None

            logger.info("Recording started: %s (PID %d)", output_path, _current_recording.pid)
            return output_path
        except FileNotFoundError:
            logger.error("FFmpeg not found — cannot record screen")
            return None
        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            _current_recording = None
            _current_output = None
            return None


def stop_recording() -> str | None:
    global _current_recording, _current_output

    with _recording_lock:
        if _current_recording is None:
            logger.warning("No recording in progress")
            return None

        logger.info("Stopping screen recording...")
        proc = _current_recording

        # 1) Windows: CTRL_BREAK_EVENT first (cleanest finalize for fragmented mp4).
        if sys.platform == "win32":
            try:
                import signal as _sig
                proc.send_signal(_sig.CTRL_BREAK_EVENT)
                try:
                    proc.wait(timeout=8)
                    logger.info("FFmpeg stopped via CTRL_BREAK_EVENT")
                except subprocess.TimeoutExpired:
                    pass
            except Exception as e:
                logger.debug("CTRL_BREAK_EVENT failed: %s", e)

        # 2) If still alive: send 'q\n' on stdin and close it.
        if proc.poll() is None:
            try:
                if proc.stdin:
                    proc.stdin.write(b"q\n")
                    proc.stdin.flush()
                    proc.stdin.close()
            except Exception:
                pass
            try:
                proc.wait(timeout=8)
                logger.info("FFmpeg stopped via stdin 'q'")
            except subprocess.TimeoutExpired:
                pass

        # 3) Last resort: kill (output is still recoverable thanks to
        #    fragmented-mp4 movflags above).
        if proc.poll() is None:
            logger.warning("FFmpeg didn't stop gracefully, killing...")
            proc.kill()
            proc.wait(timeout=5)

        output = _current_output
        logger.info("Recording stopped: %s", output)
        _current_recording = None
        _current_output = None
        return output


def is_recording() -> bool:
    with _recording_lock:
        return _current_recording is not None and _current_recording.poll() is None


def get_current_output() -> str | None:
    with _recording_lock:
        return _current_output


# Re-export typing helper used by api.py.
try:
    from typing import Any  # noqa: F401
except Exception:
    pass
