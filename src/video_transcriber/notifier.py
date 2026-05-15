import logging

import requests

from .config import AppConfig

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}"


def send_notification(
    config: AppConfig,
    video_path: str,
    audio_path: str | None,
    transcript_path: str | None,
    error: str | None = None,
) -> bool:
    if not config.telegram.bot_token or not config.telegram.chat_id:
        logger.warning("Telegram not configured — skipping notification")
        return False

    url = _API_BASE.format(token=config.telegram.bot_token) + "/sendMessage"

    if error:
        text = (
            f"❌ Ошибка при обработке видео\n\n"
            f"📁 Файл: `{video_path}`\n"
            f"⚠️ Ошибка: {error}"
        )
    else:
        lines = ["✅ Расшифровка готова!\n"]
        lines.append(f"📁 Видео: `{video_path}`")
        if audio_path:
            lines.append(f"🎵 Аудио: `{audio_path}`")
        if transcript_path:
            lines.append(f"📝 Текст: `{transcript_path}`")
        text = "\n".join(lines)

    payload = {
        "chat_id": config.telegram.chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Telegram notification sent")
        return True
    except requests.RequestException as e:
        logger.error("Telegram notification failed: %s", e)
        return False
