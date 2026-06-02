"""Enumerate audio input devices for the recorder UI / config.

PR1 / commit 7 — adds macOS (AVFoundation) and Linux (PulseAudio) backends
to the Windows-only implementation introduced in commit 3.
"""

from __future__ import annotations

import logging
import platform
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Windows (dshow)
# ---------------------------------------------------------------------------

_DSHOW_AUDIO_RE = re.compile(r'"([^"]+)"\s*\(audio\)', re.IGNORECASE)


def list_dshow_audio_inputs(ffmpeg_path: str = "ffmpeg", timeout: float = 8.0) -> list[str]:
    if platform.system() != "Windows":
        return []

    cmd = [ffmpeg_path, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    output = (proc.stderr or "") + "\n" + (proc.stdout or "")
    names: list[str] = []
    for m in _DSHOW_AUDIO_RE.finditer(output):
        n = m.group(1).strip()
        if n and n not in names:
            names.append(n)
    return names


# ---------------------------------------------------------------------------
# macOS (AVFoundation)
# ---------------------------------------------------------------------------

_AVF_AUDIO_BLOCK_RE = re.compile(
    r"AVFoundation audio devices:.*?(?=AVFoundation\s+\w+\s+devices:|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_AVF_DEVICE_RE = re.compile(r"\[(\d+)\]\s*(.+)$", re.MULTILINE)


def list_avfoundation_audio_inputs(ffmpeg_path: str = "ffmpeg", timeout: float = 8.0) -> list[str]:
    if platform.system() != "Darwin":
        return []
    cmd = [ffmpeg_path, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    output = (proc.stderr or "") + "\n" + (proc.stdout or "")
    m = _AVF_AUDIO_BLOCK_RE.search(output)
    if not m:
        return []
    names: list[str] = []
    for dm in _AVF_DEVICE_RE.finditer(m.group(0)):
        # We return display names; the recorder maps them back to indices via
        # `recorder.mic_device` (which on macOS is the literal index string).
        idx, name = dm.group(1), dm.group(2).strip()
        names.append(f"{idx}: {name}")
    return names


# ---------------------------------------------------------------------------
# Linux (PulseAudio)
# ---------------------------------------------------------------------------

def _pactl_sources(kind: str) -> list[str]:
    """Return Pulse source names. kind = 'input' (mics) or 'monitor' (system loopback)."""
    if not shutil.which("pactl"):
        return []
    try:
        out = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True, text=True, timeout=5, errors="replace",
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    names: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        is_monitor = name.endswith(".monitor")
        if kind == "monitor" and is_monitor:
            names.append(name)
        elif kind == "input" and not is_monitor:
            names.append(name)
    return names


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def list_audio_inputs() -> dict[str, list[str]]:
    os_name = platform.system()
    result: dict[str, list[str]] = {"platform": os_name, "mic": [], "system": []}

    if os_name == "Windows":
        all_inputs = list_dshow_audio_inputs()
        result["mic"] = list(all_inputs)
        result["system"] = [
            n for n in all_inputs
            if any(k in n.lower() for k in ("stereo mix", "loopback", "what u hear", "what you hear"))
        ]
    elif os_name == "Darwin":
        result["mic"] = list_avfoundation_audio_inputs()
        # macOS has no built-in loopback — users typically install BlackHole.
        # Surface anything that mentions blackhole/loopback/aggregate as system candidate.
        result["system"] = [
            n for n in result["mic"]
            if any(k in n.lower() for k in ("blackhole", "loopback", "aggregate", "soundflower"))
        ]
    elif os_name == "Linux":
        result["mic"] = _pactl_sources("input")
        result["system"] = _pactl_sources("monitor")

    return result
