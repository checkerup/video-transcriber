import logging
from pathlib import Path
from typing import Dict, Any

from .config import AppConfig
from .extractor import copy_video_to_output, extract_audio, copy_audio_to_output
from .notifier import send_notification
from .transcriber import transcribe
from .summarizer import generate_summary

logger = logging.getLogger(__name__)


def process_file(file_path: str, config: AppConfig) -> dict:
    logger.info("=" * 60)
    logger.info("Processing: %s", file_path)
    logger.info("=" * 60)

    result: dict = {
        "video": None,
        "audio": None,
        "transcript": None,
        "summary": None,
        "error": None,
    }

    was_video = False
    audio_path = None
    try:
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        audio_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
        video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}
        
        if suffix in audio_extensions:
            # Audio pipeline
            output_audio = copy_audio_to_output(file_path, config)
            result["audio"] = output_audio
            audio_path = output_audio
            
            transcript_path = transcribe(output_audio, config)
            result["transcript"] = transcript_path
            
        elif suffix in video_extensions:
            # Video pipeline
            was_video = True
            output_video = copy_video_to_output(file_path, config)
            result["video"] = output_video
            
            extracted_audio = extract_audio(output_video, config)
            result["audio"] = extracted_audio
            audio_path = extracted_audio
            
            transcript_path = transcribe(extracted_audio, config)
            result["transcript"] = transcript_path
            
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        # Summarization
        if result["transcript"]:
            with open(result["transcript"], "r", encoding="utf-8") as f:
                transcript_text = f.read()
                
            summary = generate_summary(transcript_text, config)
            if summary:
                t_path = Path(result["transcript"])
                summary_path = t_path.parent / f"{t_path.stem}_summary.md"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                result["summary"] = str(summary_path)
                logger.info("Summary saved to: %s", summary_path)

        # Temporary audio cleanup if keep_audio is False and it was a video file
        if not config.processing.keep_audio and was_video and audio_path:
            try:
                p_audio = Path(audio_path)
                if p_audio.exists():
                    p_audio.unlink()
                    logger.info("Deleted temporary audio file: %s", audio_path)
            except Exception as e:
                logger.warning("Failed to delete temporary audio file: %s", e)

        logger.info("Pipeline complete for: %s", file_path)

    except Exception as e:
        logger.exception("Pipeline failed for: %s", file_path)
        result["error"] = str(e)

    send_notification(
        config=config,
        video_path=result["video"],
        audio_path=result["audio"],
        transcript_path=result["transcript"],
        error=result["error"],
        summary_path=result["summary"],
    )

    return result


def process_video(video_path: str, config: AppConfig) -> dict:
    """Compatibility alias for process_file."""
    logger.warning("process_video is deprecated, use process_file instead")
    return process_file(video_path, config)
