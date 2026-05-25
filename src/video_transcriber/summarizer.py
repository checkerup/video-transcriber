import logging
import requests
from video_transcriber.config import AppConfig

logger = logging.getLogger(__name__)

def generate_summary(text: str, config: AppConfig) -> str:
    """
    Generates a detailed summary and table of contents with chapters using Gemini API.
    
    Args:
        text (str): The transcription text to summarize.
        config (AppConfig): The application configuration.
        
    Returns:
        str: The generated summary in markdown format, or an empty string on error or if disabled.
    """
    if not config.summarization.enabled:
        logger.debug("Summarization is disabled in config.")
        return ""

    api_key = config.summarization.api_key
    if not api_key:
        logger.warning("Gemini API key is missing. Skipping summarization.")
        return ""

    if not text or not text.strip():
        logger.warning("Empty transcription text provided. Skipping summarization.")
        return ""

    model = config.summarization.model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    custom_prompt = getattr(config.summarization, "prompt", "")
    if custom_prompt:
        if "{text}" in custom_prompt:
            prompt = custom_prompt.format(text=text)
        else:
            prompt = f"{custom_prompt}\n\n{text}"
    else:
        prompt = (
            "Сделай подробное краткое содержание (summary) и оглавление по главам для следующего текста транскрибации. "
            "Ответ должен быть на русском языке и оформлен в формате Markdown. Текст транскрибации:\n\n"
            f"{text}"
        )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Parse the standard response structure from Gemini API
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                summary_text = parts[0].get("text", "")
                if summary_text:
                    logger.info("Successfully generated summary via Gemini API.")
                    return summary_text.strip()
                    
        logger.warning(f"Unexpected response format from Gemini API: {data}")
        return ""
    except Exception as e:
        logger.exception(f"Error calling Gemini API for summarization: {e}")
        return ""
