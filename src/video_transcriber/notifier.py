from typing import Any
import html
import logging

import requests

from .config import AppConfig

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}"


def send_notification(
    config: AppConfig,
    video_path: Any,
    audio_path: Any,
    transcript_path: Any,
    error: Any = None,
) -> bool:
    if not config.telegram.bot_token or not config.telegram.chat_id:
        logger.warning("Telegram not configured — skipping notification")
        return False

    url = _API_BASE.format(token=config.telegram.bot_token) + "/sendMessage"

    video_escaped = html.escape(str(video_path)) if video_path is not None else "Неизвестно"
    audio_escaped = html.escape(str(audio_path)) if audio_path is not None else None
    transcript_escaped = html.escape(str(transcript_path)) if transcript_path is not None else None
    error_escaped = html.escape(str(error)) if error is not None else None

    if error_escaped is not None:
        text = (
            f"❌ <b>Ошибка при обработке видео</b>\n\n"
            f"📁 <b>Файл:</b> <code>{video_escaped}</code>\n"
            f"⚠️ <b>Ошибка:</b> <code>{error_escaped}</code>"
        )
    else:
        lines = ["✅ <b>Расшифровка готова!</b>\n"]
        lines.append(f"📁 <b>Видео:</b> <code>{video_escaped}</code>")
        if audio_escaped is not None:
            lines.append(f"🎵 <b>Аудио:</b> <code>{audio_escaped}</code>")
        if transcript_escaped is not None:
            lines.append(f"📝 <b>Текст:</b> <code>{transcript_escaped}</code>")
        text = "\n".join(lines)

    payload = {
        "chat_id": config.telegram.chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Telegram notification sent")
        return True
    except requests.RequestException as e:
        logger.error("Telegram notification failed: %s", e)
        return False

