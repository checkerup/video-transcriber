from pathlib import Path
from unittest.mock import patch
import requests
from video_transcriber.config import AppConfig, TelegramConfig
from video_transcriber.notifier import send_notification

@patch("requests.post")
def test_html_notification_escaping(mock_post):
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.return_value.status_code = 200
    
    # Path containing underscores and angle brackets
    video_path = "C:/my_videos/file_<1>_test.mp4"
    
    result = send_notification(config, video_path, None, None, error="Error occurred <failed>")
    assert result is True
    
    # Assert requests.post is called with parse_mode: HTML and escaped strings
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "file_&lt;1&gt;_test.mp4" in payload["text"]
    assert "Error occurred &lt;failed&gt;" in payload["text"]
    
    # Verify bold tags in the error payload
    assert "<b>Ошибка при обработке видео</b>" in payload["text"]
    assert "<b>Файл:</b>" in payload["text"]
    assert "<b>Ошибка:</b>" in payload["text"]

@patch("requests.post")
def test_html_notification_success_escaping(mock_post):
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.return_value.status_code = 200
    
    video_path = "C:/my_videos/video_<&>.mp4"
    audio_path = "C:/my_videos/audio_<&>.wav"
    transcript_path = "C:/my_videos/transcript_<&>.txt"
    
    result = send_notification(config, video_path, audio_path, transcript_path)
    assert result is True
    
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "video_&lt;&amp;&gt;.mp4" in payload["text"]
    assert "audio_&lt;&amp;&gt;.wav" in payload["text"]
    assert "transcript_&lt;&amp;&gt;.txt" in payload["text"]
    
    # Verify bold tags in the success payload
    assert "<b>Расшифровка готова!</b>" in payload["text"]
    assert "<b>Видео:</b>" in payload["text"]
    assert "<b>Аудио:</b>" in payload["text"]
    assert "<b>Текст:</b>" in payload["text"]

@patch("requests.post")
def test_send_notification_failures(mock_post):
    # Case 1: missing config (bot_token empty)
    config_no_token = AppConfig(telegram=TelegramConfig(bot_token="", chat_id="456"))
    result = send_notification(config_no_token, "video.mp4", None, None)
    assert result is False
    mock_post.assert_not_called()

    # Case 2: missing config (chat_id empty)
    config_no_chat = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id=""))
    result = send_notification(config_no_chat, "video.mp4", None, None)
    assert result is False
    mock_post.assert_not_called()

    # Case 3: request raises requests.RequestException
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.side_effect = requests.RequestException("Network error")
    result = send_notification(config, "video.mp4", None, None)
    assert result is False

@patch("requests.post")
def test_send_notification_robust_types(mock_post):
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.return_value.status_code = 200

    # Pass Path objects and None values
    video_path = Path("C:/my_videos/file.mp4")
    audio_path = Path("C:/my_videos/audio.wav")
    transcript_path = None
    
    result = send_notification(config, video_path, audio_path, transcript_path)
    assert result is True
    
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert "file.mp4" in payload["text"]
    assert "audio.wav" in payload["text"]
    assert "Текст" not in payload["text"]  # transcript_path is None, so it shouldn't be included

    # Test when video_path is None
    send_notification(config, None, None, None)
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert "Неизвестно" in payload["text"]


