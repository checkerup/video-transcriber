"""Enumerate audio input devices for the recorder UI / config.

Windows uses DirectShow (`dshow`). macOS uses AVFoundation. Linux uses PulseAudio.
This module shells out to `ffmpeg` (already required by the rest of the project)
and parses its listing output. PR7 adds the non-Windows backends; PR3 ships
only the Windows path so the Settings tab on Windows can populate its dropdowns.
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess

logger = logging.getLogger(__name__)


_DSHOW_AUDIO_RE = re.compile(
    r'"([^"]+)"\s*\(audio\)',
    re.IGNORECASE,
)


def list_dshow_audio_inputs(ffmpeg_path: str = "ffmpeg", timeout: float = 8.0) -> list[str]:
    """Return DirectShow audio input device names on Windows.

    Returns an empty list on non-Windows hosts or when ffmpeg is missing.
    """
    if platform.system() != "Windows":
        return []

    cmd = [ffmpeg_path, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
    except FileNotFoundError:
        logger.warning("ffmpeg not on PATH — cannot list dshow audio devices")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg dshow listing timed out")
        return []

    # ffmpeg writes the device list to stderr.
    output = (proc.stderr or "") + "\n" + (proc.stdout or "")
    names: list[str] = []
    for match in _DSHOW_AUDIO_RE.finditer(output):
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names


def list_audio_inputs() -> dict[str, list[str]]:
    """Return a structured device listing.

    Shape:
        {
          "platform": "Windows" | "Darwin" | "Linux",
          "mic":      [str, ...],   # candidates for recorder.mic_device
          "system":   [str, ...],   # candidates for recorder.system_device
        }

    PR3 ships only the Windows path. PR7 wires up macOS/Linux.
    """
    os_name = platform.system()
    result: dict[str, list[str]] = {"platform": os_name, "mic": [], "system": []}

    if os_name == "Windows":
        all_inputs = list_dshow_audio_inputs()
        result["mic"] = list(all_inputs)
        result["system"] = [
            n for n in all_inputs
            if any(k in n.lower() for k in ("stereo mix", "loopback", "what u hear", "what you hear"))
        ]
    # macOS + Linux backends land in PR7 — return empty lists for now.

    return result
