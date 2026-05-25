import html
from video_transcriber.config import AppConfig, TelegramConfig
from video_transcriber.notifier import send_notification
from unittest.mock import patch

@patch("requests.post")
def test_html_notification_escaping(mock_post):
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.return_value.status_code = 200
    
    # Path containing underscores and angle brackets
    video_path = "C:/my_videos/file_<1>_test.mp4"
    
    send_notification(config, video_path, None, None, error="Error occurred <failed>")
    
    # Assert requests.post is called with parse_mode: HTML and escaped strings
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "file_&lt;1&gt;_test.mp4" in payload["text"]
    assert "Error occurred &lt;failed&gt;" in payload["text"]

@patch("requests.post")
def test_html_notification_success_escaping(mock_post):
    config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
    mock_post.return_value.status_code = 200
    
    video_path = "C:/my_videos/video_<&>.mp4"
    audio_path = "C:/my_videos/audio_<&>.wav"
    transcript_path = "C:/my_videos/transcript_<&>.txt"
    
    send_notification(config, video_path, audio_path, transcript_path)
    
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "video_&lt;&amp;&gt;.mp4" in payload["text"]
    assert "audio_&lt;&amp;&gt;.wav" in payload["text"]
    assert "transcript_&lt;&amp;&gt;.txt" in payload["text"]

