import logging
import urllib.parse
from pathlib import Path
import requests

from .config import AppConfig

logger = logging.getLogger(__name__)

_model_cache: dict = {}


def google_translate(text: str, target_lang: str) -> str:
    if not text.strip():
        return text
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        parts = resp.json()[0]
        return "".join([part[0] for part in parts if part[0]])
    except Exception as e:
        logger.warning("Google Translate failed: %s", e)
        return text


def _get_model(config: AppConfig):
    key = f"{config.transcription.model_size}_{config.transcription.device}_{config.transcription.compute_type}"
    if key in _model_cache:
        return _model_cache[key]

    from faster_whisper import WhisperModel

    logger.info(
        "Loading Whisper model: size=%s device=%s compute_type=%s",
        config.transcription.model_size,
        config.transcription.device,
        config.transcription.compute_type,
    )
    model = WhisperModel(
        config.transcription.model_size,
        device=config.transcription.device,
        compute_type=config.transcription.compute_type,
    )
    _model_cache[key] = model
    return model


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _format_srt(segments) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg.start).replace(".", ",")
        end = format_timestamp(seg.end).replace(".", ",")
        lines.append(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n")
    return "\n".join(lines)


def _format_vtt(segments) -> str:
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = format_timestamp(seg.start)
        end = format_timestamp(seg.end)
        lines.append(f"{start} --> {end}\n{seg.text.strip()}\n")
    return "\n".join(lines)


def _format_txt(segments) -> str:
    parts = []
    for seg in segments:
        ts = format_timestamp(seg.start)
        text = seg.text.strip()
        parts.append(f"[{ts}] {text}")
    return "\n".join(parts)


def _format_paragraphs(segments) -> str:
    text_blocks = []
    current_block = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        current_block.append(text)
        if text[-1] in (".", "?", "!"):
            text_blocks.append(" ".join(current_block))
            current_block = []
    if current_block:
        text_blocks.append(" ".join(current_block))
    return "\n\n".join(text_blocks)


def transcribe(audio_path: str, config: AppConfig) -> str:
    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    output_dir = Path(config.processing.output_folder)
    fmt = config.transcription.output_format

    transcript_path = output_dir / f"{audio.stem}.{fmt}"

    model = _get_model(config)

    logger.info("Transcribing: %s (lang=%s)", audio.name, config.transcription.language)

    segments, info = model.transcribe(
        str(audio),
        language=config.transcription.language if config.transcription.language != "auto" else None,
        word_timestamps=config.transcription.word_timestamps,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    segment_list = list(segments)
    logger.info(
        "Transcription complete: %d segments, language=%s (%.1f%% confidence)",
        len(segment_list),
        info.language,
        info.language_probability * 100,
    )

    translate_to = getattr(config.transcription, "translate_to", "none")
    if translate_to and translate_to.lower() != "none":
        detected_lang = info.language
        if detected_lang != translate_to:
            logger.info("Translating transcript from %s to %s...", detected_lang, translate_to)
            for seg in segment_list:
                seg.text = google_translate(seg.text, translate_to)

    if getattr(config.transcription, "clean_paragraphs", False):
        text = _format_paragraphs(segment_list)
    else:
        formatters = {"txt": _format_txt, "srt": _format_srt, "vtt": _format_vtt}
        formatter = formatters.get(fmt, _format_txt)
        text = formatter(segment_list)

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    logger.info("Transcript saved: %s", transcript_path)
    return str(transcript_path)

