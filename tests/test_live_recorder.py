"""Tests for the live recorder.

These do not exercise the actual mic/screen capture (that needs a
real audio device + display). They verify the public API and the audio-mix
helpers using ffmpeg + synthetic wavs.
"""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from video_transcriber.config import AppConfig, ProcessingConfig, RecorderConfig
from video_transcriber.live_recorder import LiveRecorder, run_live_recording


def _write_sine_wav(path: Path, freq_hz: float, duration_s: float, sr: int = 16000):
    import math
    import struct

    n = int(duration_s * sr)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for i in range(n):
            v = int(0.5 * 32767 * math.sin(2 * math.pi * freq_hz * i / sr))
            w.writeframes(struct.pack("<h", v))


def test_invalid_mode_raises(tmp_path):
    cfg = AppConfig(processing=ProcessingConfig(output_folder=str(tmp_path)))
    with pytest.raises(ValueError):
        LiveRecorder(cfg, mode="banana")


def test_session_dir_is_created(tmp_path):
    cfg = AppConfig(processing=ProcessingConfig(output_folder=str(tmp_path)))
    rec = LiveRecorder(cfg, mode="voice")
    assert rec.session_dir.exists()
    assert rec.session_dir.is_dir()
    # Session dir should be under output_folder
    assert str(rec.session_dir).startswith(str(tmp_path))


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_ffmpeg_mix_audio_two_inputs(tmp_path):
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    out = tmp_path / "mixed.wav"
    _write_sine_wav(a, 440.0, 0.5)
    _write_sine_wav(b, 220.0, 0.5)

    LiveRecorder._ffmpeg_mix_audio(a, b, out)
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_ffmpeg_mix_falls_back_when_one_missing(tmp_path):
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    out = tmp_path / "mixed.wav"
    _write_sine_wav(a, 440.0, 0.5)
    # b not written

    LiveRecorder._ffmpeg_mix_audio(a, b, out)
    assert out.exists() and out.stat().st_size > 0


def test_invalid_mode_in_run_helper(tmp_path):
    cfg = AppConfig(processing=ProcessingConfig(output_folder=str(tmp_path)))
    with pytest.raises(ValueError):
        run_live_recording(cfg, mode="not-a-real-mode")
