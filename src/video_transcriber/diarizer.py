import logging
from video_transcriber.config import AppConfig

logger = logging.getLogger(__name__)


def diarize_audio(audio_path: str, config: AppConfig) -> list[dict]:
    """
    Runs speaker diarization on an audio file using PyAnnote.audio.
    
    Args:
        audio_path (str): Path to the audio file.
        config (AppConfig): Application configuration.
        
    Returns:
        list[dict]: A list of speaker turns, where each turn is a dictionary:
                   {"start": float, "end": float, "speaker": str}
    """
    if not config.diarization.enabled:
        logger.debug("Speaker diarization is disabled.")
        return []

    token = config.diarization.auth_token
    if not token or not token.strip():
        raise ValueError(
            "Hugging Face API token (auth_token) is required for speaker diarization. "
            "Please configure it in config.yaml under diarization.auth_token, or set HF_TOKEN environment variable."
        )

    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError:
        raise ImportError(
            "The 'pyannote.audio' library is required for diarization. "
            "Please install it using: pip install -e .[diarization]"
        )

    logger.info("Initializing PyAnnote speaker diarization pipeline...")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token.strip()
        )
    except Exception as e:
        logger.error("Failed to load PyAnnote pipeline from Hugging Face: %s", e)
        raise RuntimeError(
            f"Failed to load speaker diarization pipeline. Make sure you accepted the terms for "
            f"'pyannote/speaker-diarization-3.1' and 'pyannote/segmentation-3.0' on Hugging Face, "
            f"and that your API token is correct. Error: {e}"
        )

    # Use CUDA if available and configured
    device = torch.device(
        "cuda" if torch.cuda.is_available() and config.transcription.device == "cuda" else "cpu"
    )
    logger.info("Running diarization on device: %s", device)
    pipeline.to(device)

    logger.info("Running speaker diarization on: %s", audio_path)
    
    min_speakers = config.diarization.min_speakers
    max_speakers = config.diarization.max_speakers
    
    # Run the pipeline
    diarization_result = pipeline(audio_path, min_speakers=min_speakers, max_speakers=max_speakers)
    
    turns = []
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        turns.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })
        
    logger.info("Speaker diarization complete. Found %d speaker turns.", len(turns))
    return turns
