import logging
from pathlib import Path

from .config import AppConfig
from .extractor import copy_video_to_output, extract_audio
from .notifier import send_notification
from .transcriber import transcribe

logger = logging.getLogger(__name__)


def process_video(video_path: str, config: AppConfig) -> dict:
    logger.info("=" * 60)
    logger.info("Processing: %s", video_path)
    logger.info("=" * 60)

    result: dict = {
        "video": video_path,
        "audio": None,
        "transcript": None,
        "error": None,
    }

    try:
        output_video = copy_video_to_output(video_path, config)
        result["video"] = output_video

        audio_path = extract_audio(output_video, config)
        result["audio"] = audio_path

        transcript_path = transcribe(audio_path, config)
        result["transcript"] = transcript_path

        logger.info("Pipeline complete for: %s", video_path)

    except Exception as e:
        logger.exception("Pipeline failed for: %s", video_path)
        result["error"] = str(e)

    send_notification(
        config=config,
        video_path=result["video"],
        audio_path=result["audio"],
        transcript_path=result["transcript"],
        error=result["error"],
    )

    return result
