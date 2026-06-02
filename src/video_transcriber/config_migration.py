"""Migrate legacy config files in-place when new fields are added.

PR1 introduces `recorder.audio_mode` (+ optional `mic_device` / `system_device`).
If a user's config.yaml predates PR1, we transparently add these fields with
sensible defaults so the loader produces a complete RecorderConfig and so the
user's config file stays in sync with the documented schema.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_AUDIO_FIELDS_DEFAULTS = {
    "audio_mode": "both",
    "mic_device": "",
    "system_device": "",
}


def migrate_recorder_section(raw: dict[str, Any], path: Path) -> dict[str, Any]:
    """Ensure raw['recorder'] has the PR1 audio fields. Write back if changed."""
    recorder = raw.get("recorder")
    if not isinstance(recorder, dict):
        recorder = {}
        raw["recorder"] = recorder

    missing = [k for k in _AUDIO_FIELDS_DEFAULTS if k not in recorder]
    if not missing:
        return raw

    for k in missing:
        recorder[k] = _AUDIO_FIELDS_DEFAULTS[k]

    try:
        backup = path.with_suffix(path.suffix + ".pre-pr1.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
            logger.info("Wrote config backup: %s", backup)

        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(raw, fh, sort_keys=False, allow_unicode=True)
        logger.info("Config migrated: added %s to [recorder]", missing)
    except OSError as e:
        logger.warning("Could not persist migrated config (%s) — using in-memory values", e)

    return raw
