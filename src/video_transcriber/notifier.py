from typing import Any
import html
import logging
from pathlib import Path

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
    summary_path: Any = None,
    timing_summary: Any = None,
) -> bool:
    if not config.telegram.bot_token or not config.telegram.chat_id:
        logger.warning("Telegram not configured — skipping notification")
        return False

    url = _API_BASE.format(token=config.telegram.bot_token) + "/sendMessage"

    video_escaped = html.escape(str(video_path)) if video_path is not None else None
    audio_escaped = html.escape(str(audio_path)) if audio_path is not None else None
    transcript_escaped = html.escape(str(transcript_path)) if transcript_path is not None else None
    error_escaped = html.escape(str(error)) if error is not None else None
    summary_path_escaped = html.escape(str(summary_path)) if summary_path is not None else None

    if error_escaped is not None:
        file_label = "Видео" if video_path is not None else "Аудио"
        file_val = video_escaped if video_path is not None else (audio_escaped if audio_escaped else "Неизвестно")
        text = (
            f"❌ <b>Ошибка при обработке {file_label.lower()}</b>\n\n"
            f"📁 <b>Файл:</b> <code>{file_val}</code>\n"
            f"⚠️ <b>Ошибка:</b> <code>{error_escaped}</code>"
        )
        payload = {
            "chat_id": config.telegram.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Telegram notification failed: %s", e)
            return False

    # Success path
    lines = ["✅ <b>Расшифровка готова!</b>\n"]
    if video_escaped is not None:
        lines.append(f"📁 <b>Видео:</b> <code>{video_escaped}</code>")
        if audio_escaped is not None:
            lines.append(f"🎵 <b>Аудио:</b> <code>{audio_escaped}</code>")
    elif audio_escaped is not None:
        lines.append(f"🎵 <b>Аудио:</b> <code>{audio_escaped}</code>")
    else:
        lines.append("📁 <b>Видео:</b> <code>Неизвестно</code>")
    if transcript_escaped is not None:
        lines.append(f"📝 <b>Текст:</b> <code>{transcript_escaped}</code>")
    if summary_path_escaped is not None:
        lines.append(f"📊 <b>Сводка:</b> <code>{summary_path_escaped}</code>")
    if timing_summary:
        lines.append(f"⏱ <b>Время обработки:</b> <code>{html.escape(str(timing_summary))}</code>")

    base_text = "\n".join(lines)

    # Read summary content if present
    summary_text = ""
    if summary_path and Path(summary_path).exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read().strip()
        except Exception as e:
            logger.warning("Failed to read summary file: %s", e)

    payload = {
        "chat_id": config.telegram.chat_id,
        "parse_mode": "HTML",
    }

    try:
        if summary_text:
            summary_section = f"\n\n📖 <b>Краткое содержание:</b>\n{html.escape(summary_text)}"
            if len(base_text) + len(summary_section) <= 4096:
                payload["text"] = base_text + summary_section
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
            else:
                # Send first message (metadata)
                payload["text"] = base_text
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                
                # Send second message (summary) - potentially chunked
                summary_header = "📖 <b>Краткое содержание:</b>\n"
                _send_message_in_chunks(url, payload, summary_header + html.escape(summary_text))
        else:
            payload["text"] = base_text
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            
        logger.info("Telegram notification sent successfully")
        return True
    except requests.RequestException as e:
        logger.error("Telegram notification failed: %s", e)
        return False


def _send_message_in_chunks(url: str, payload: dict, text_to_send: str) -> None:
    max_len = 4000
    lines = text_to_send.split("\n")
    current_chunk = []
    current_len = 0
    for line in lines:
        if current_len + len(line) + 1 > max_len:
            if current_chunk:
                payload["text"] = "\n".join(current_chunk)
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                current_chunk = [line]
                current_len = len(line)
            else:
                # Line itself is longer than max_len, split it
                payload["text"] = line
                resp = requests.post(url, json=payload, timeout=15)
                resp.raise_for_status()
                current_chunk = []
                current_len = 0
        else:
            current_chunk.append(line)
            current_len += len(line) + 1
    if current_chunk:
        payload["text"] = "\n".join(current_chunk)
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()

