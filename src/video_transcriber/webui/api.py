"""JsApi — the Python object exposed to the GUI's JavaScript.

Every method here becomes callable from JS as
``await window.pywebview.api.method_name(...)``.

Keep methods small and JSON-serialisable. Long work goes through JobManager.
"""

from __future__ import annotations

import json
import logging
import platform
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any

import yaml

from ..audio_devices import list_audio_inputs
from ..config import AppConfig, load_config
from ..hardware import detect_hardware
from ..screen_recorder import get_current_output, is_recording, start_recording as _start_recording, stop_recording as _stop_recording
from .jobs import JobManager


logger = logging.getLogger(__name__)


# ---------- helpers ----------

def _dataclass_to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {f.name: _dataclass_to_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_dataclass_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj


def _read_timing_report(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------- API class ----------

class JsApi:
    """Stable surface for the JS frontend. Renaming a method is a breaking change."""

    def __init__(self, config: AppConfig, config_path: Path, project_root: Path):
        self.config = config
        self.config_path = config_path
        self.project_root = project_root
        self.jobs = JobManager(config)
        self._window = None  # set by app.launch after window creation

    def attach_window(self, window: Any) -> None:
        self._window = window

    # ----- meta -----

    def ping(self) -> dict:
        return {
            "ok": True,
            "os": platform.system(),
            "python": platform.python_version(),
        }

    def hardware(self) -> dict:
        try:
            hw = detect_hardware()
            return _dataclass_to_dict(hw)
        except Exception as e:
            return {"error": str(e)}

    # ----- config -----

    def get_config(self) -> dict:
        return _dataclass_to_dict(self.config)

    def get_config_yaml(self) -> str:
        """Return raw config.yaml text so the GUI can show / edit it directly."""
        try:
            return self.config_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def send_telegram_test(self) -> dict:
        """Send a one-shot 'connection works' message to the configured chat."""
        import requests as _r
        tg = self.config.telegram
        if not tg.bot_token or not tg.chat_id:
            return {"ok": False, "error": "Telegram is not configured (bot_token + chat_id)."}
        try:
            resp = _r.post(
                f"https://api.telegram.org/bot{tg.bot_token}/sendMessage",
                json={
                    "chat_id": tg.chat_id,
                    "text": "✅ <b>video-transcriber</b>: connection works.",
                    "parse_mode": "HTML",
                },
                timeout=15,
            )
            resp.raise_for_status()
            return {"ok": True}
        except _r.RequestException as e:
            return {"ok": False, "error": str(e)}

    def test_llm(self) -> dict:
        """Hit the configured LLM provider with a tiny sample to confirm credentials work."""
        from ..summarizer import generate_summary
        provider = (self.config.summarization.provider or "gemini").lower()
        if not self.config.summarization.api_key:
            return {"ok": False, "error": "summarization.api_key is not set"}
        result = generate_summary("Hello, this is a test transcript.", provider=provider)
        if result:
            return {"ok": True, "msg": f"{provider}: works"}
        return {"ok": False, "error": "LLM provider returned empty"}

    def save_config_yaml(self, text: str) -> dict:
        """Validate + write raw yaml text. Returns reloaded config or error."""
        try:
            parsed = yaml.safe_load(text)
            if parsed is not None and not isinstance(parsed, dict):
                raise ValueError("top-level YAML must be a mapping")
            self.config_path.write_text(text, encoding="utf-8")
            self.config = load_config(config_path=self.config_path)
            self.jobs.config = self.config
            return {"ok": True, "config": self.get_config()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def update_config(self, patch: dict) -> dict:
        """Apply a *partial* settings update by dotted-path key.

        Example: {"diarization.enabled": true, "diarization.num_speakers": 5}.
        """
        try:
            raw = {}
            if self.config_path.exists():
                raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw, dict):
                raw = {}
            for dotted, value in patch.items():
                parts = dotted.split(".")
                cur = raw
                for p in parts[:-1]:
                    if p not in cur or not isinstance(cur[p], dict):
                        cur[p] = {}
                    cur = cur[p]
                cur[parts[-1]] = value
            txt = yaml.safe_dump(raw, allow_unicode=True, sort_keys=False)
            self.config_path.write_text(txt, encoding="utf-8")
            self.config = load_config(config_path=self.config_path)
            self.jobs.config = self.config
            return {"ok": True, "config": self.get_config()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ----- file dialogs -----

    def pick_file(self, kinds: str = "video") -> str | None:
        """Open a native file picker. ``kinds`` controls the filter."""
        import webview

        if self._window is None:
            return None
        if kinds == "video":
            file_types = (
                "Video and Audio (*.mp4;*.mkv;*.avi;*.mov;*.webm;*.mp3;*.wav;*.m4a)",
                "All files (*.*)",
            )
        elif kinds == "transcript":
            file_types = ("Transcript (*.txt;*.srt;*.vtt)", "All files (*.*)")
        else:
            file_types = ("All files (*.*)",)
        try:
            _open_kind = webview.FileDialog.OPEN
        except AttributeError:
            _open_kind = webview.OPEN_DIALOG  # type: ignore[attr-defined]
        result = self._window.create_file_dialog(
            _open_kind,
            allow_multiple=False,
            file_types=file_types,
        )
        if not result:
            return None
        return result[0] if isinstance(result, (list, tuple)) else result

    def pick_folder(self) -> str | None:
        import webview
        try:
            _folder_kind = webview.FileDialog.FOLDER
        except AttributeError:
            _folder_kind = webview.FOLDER_DIALOG  # type: ignore[attr-defined]
        result = self._window.create_file_dialog(_folder_kind)
        if not result:
            return None
        return result[0] if isinstance(result, (list, tuple)) else result

    # ----- jobs -----

    def start_process(self, file_path: str, overrides: dict | None = None) -> dict:
        if not file_path:
            return {"ok": False, "error": "no file"}
        if not Path(file_path).exists():
            return {"ok": False, "error": f"file not found: {file_path}"}
        job_id = self.jobs.enqueue_process(file_path, overrides or {})
        return {"ok": True, "job_id": job_id}

    def start_retag(self, transcript_path: str, overrides: dict | None = None) -> dict:
        if not transcript_path:
            return {"ok": False, "error": "no transcript"}
        if not Path(transcript_path).exists():
            return {"ok": False, "error": f"transcript not found: {transcript_path}"}
        job_id = self.jobs.enqueue_retag(transcript_path, overrides or {})
        return {"ok": True, "job_id": job_id}

    def cancel_job(self, job_id: str) -> dict:
        ok = self.jobs.cancel(job_id)
        return {"ok": ok}

    def list_jobs(self) -> list[dict]:
        return self.jobs.snapshot_all()

    def get_job(self, job_id: str) -> dict | None:
        return self.jobs.snapshot_one(job_id)

    # ----- history (past runs from output folder) -----

    def list_history(self) -> list[dict]:
        """Scan output folder for *.timing.json — each = one past run."""
        out = Path(self.config.processing.output_folder).expanduser()
        if not out.exists():
            return []
        items = []
        for tp in sorted(out.glob("*.timing.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            data = _read_timing_report(tp) or {}
            stem = tp.name[:-len(".timing.json")]
            base = out / stem
            transcripts = []
            for ext in (".txt", ".srt", ".vtt"):
                p = out / f"{stem}{ext}"
                if p.exists():
                    transcripts.append(str(p))
            items.append({
                "name": stem,
                "timing_report": str(tp),
                "transcripts": transcripts,
                "total_elapsed_human": data.get("total_elapsed_human"),
                "source_duration_seconds": data.get("source_duration_seconds"),
                "speedup_vs_source": data.get("speedup_vs_source"),
                "stages": data.get("stages", []),
                "modified": tp.stat().st_mtime,
            })
        return items

    def read_transcript(self, path: str, max_chars: int = 200_000) -> dict:
        try:
            p = Path(path)
            if not p.exists():
                return {"ok": False, "error": "not found"}
            txt = p.read_text(encoding="utf-8", errors="replace")
            truncated = False
            if len(txt) > max_chars:
                txt = txt[:max_chars]
                truncated = True
            return {"ok": True, "text": txt, "truncated": truncated, "name": p.name}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ----- live recording -----

    def start_live_recording(self, mode: str) -> dict:
        if mode not in {"voice", "screen", "full"}:
            return {"ok": False, "error": f"invalid mode: {mode}"}
        try:
            from ..live_recorder import LiveRecorder
            self._live = LiveRecorder(self.config, mode=mode)
            output = self._live.start()
            return {"ok": True, "output": str(output), "mode": mode}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def stop_live_recording(self) -> dict:
        try:
            live = getattr(self, "_live", None)
            if live is None:
                return {"ok": False, "error": "no active recording"}
            media = live.stop()
            self._live = None
            if media:
                # auto-enqueue for transcription
                job_id = self.jobs.enqueue_process(str(media), {})
                return {"ok": True, "media": str(media), "job_id": job_id}
            return {"ok": False, "error": "recording produced no file"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ----- logs -----

    def get_log_tail(self, max_lines: int = 200) -> list[str]:
        snap = self.jobs.active_snapshot()
        if snap and snap.get("log_tail"):
            return snap["log_tail"][-max_lines:]
        return []

    # ----- screen recorder (FFmpeg, via screen_recorder.py) -----

    def get_recorder_status(self) -> dict:
        """Return whether the FFmpeg screen recorder is active."""
        return {
            "is_recording": is_recording(),
            "output": get_current_output() or "",
        }

    def start_recording(self) -> dict:
        """Start FFmpeg screen recording."""
        try:
            result = _start_recording(self.config)
            if result is None:
                return {"error": "Failed to start recording"}
            return {"ok": True, "output": result}
        except Exception as e:
            logger.exception("start_recording failed")
            return {"error": str(e)}

    def stop_recording(self) -> dict:
        """Stop the FFmpeg screen recording."""
        try:
            result = _stop_recording()
            if result is None:
                return {"error": "No recording in progress"}
            return {"ok": True, "output": result}
        except Exception as e:
            logger.exception("stop_recording failed")
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # PR1 endpoints — audio devices + config get/set
    # ------------------------------------------------------------------

    def list_audio_devices(self) -> dict:
        """Return available audio inputs and the currently selected ones."""
        try:
            devices = list_audio_inputs()
        except Exception as e:
            logger.exception("list_audio_devices failed")
            return {"error": str(e), "platform": "", "mic": [], "system": []}

        rec = getattr(self.config, "recorder", None)
        if rec is not None:
            devices["selected"] = {
                "audio_mode": getattr(rec, "audio_mode", "both"),
                "mic_device": getattr(rec, "mic_device", ""),
                "system_device": getattr(rec, "system_device", ""),
            }
        return devices

    def get_recorder_config(self) -> dict:
        """Return the current recorder section as a plain dict."""
        rec = getattr(self.config, "recorder", None)
        if rec is None:
            return {}
        try:
            return asdict(rec)
        except TypeError:
            return {k: getattr(rec, k) for k in ("fps", "video_size", "audio_mode", "mic_device", "system_device")}

    def set_recorder_config(self, payload: dict) -> dict:
        """Update recorder.* on the in-memory config AND persist to YAML.

        Accepts any subset of: audio_mode, mic_device, system_device, fps, video_size.
        Returns the new recorder dict on success, or {"error": "..."} on failure.
        """
        allowed = {"audio_mode", "mic_device", "system_device", "fps", "video_size"}
        rec = getattr(self.config, "recorder", None)
        if rec is None:
            return {"error": "no recorder section in config"}

        # Validate audio_mode
        if "audio_mode" in payload:
            mode = payload["audio_mode"]
            if mode not in ("none", "mic", "system", "both"):
                return {"error": f"invalid audio_mode: {mode!r}"}

        for k, v in payload.items():
            if k in allowed:
                setattr(rec, k, v)

        # Persist to YAML.
        try:
            cfg_path = self.config_path
            if cfg_path and cfg_path.exists():
                with cfg_path.open("r", encoding="utf-8") as fh:
                    raw = yaml.safe_load(fh) or {}
                raw.setdefault("recorder", {})
                for k in allowed:
                    if hasattr(rec, k):
                        raw["recorder"][k] = getattr(rec, k)
                with cfg_path.open("w", encoding="utf-8") as fh:
                    yaml.safe_dump(raw, fh, sort_keys=False, allow_unicode=True)
        except Exception as e:
            logger.exception("Failed to persist recorder config")
            return {"error": f"saved in memory but persist failed: {e}"}

        return self.get_recorder_config()
