from video_transcriber.config import AppConfig, TranscriptionConfig
from video_transcriber.transcriber import _format_paragraphs, google_translate, transcribe
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

def test_format_paragraphs():
    seg1 = MagicMock(text="Привет. ")
    seg2 = MagicMock(text="Как дела? ")
    seg3 = MagicMock(text="Я записываю видео.")
    
    result = _format_paragraphs([seg1, seg2, seg3])
    assert result == "Привет.\n\nКак дела?\n\nЯ записываю видео."

@patch("requests.get")
def test_google_translate(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        [["Hello", "Привет", None, None, 1]],
        None,
        "ru"
    ]
    
    res = google_translate("Привет", "en")
    assert res == "Hello"

@patch("video_transcriber.transcriber._get_model")
@patch("video_transcriber.transcriber.google_translate")
def test_transcribe_with_translation_and_paragraphs(mock_translate, mock_get_model):
    mock_model = MagicMock()
    mock_get_model.return_value = mock_model
    
    mock_segment = MagicMock(text="Привет")
    mock_segment.start = 0.0
    mock_segment.end = 1.5
    
    mock_info = MagicMock()
    mock_info.language = "ru"
    mock_info.language_probability = 0.99
    
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    mock_translate.return_value = "Hello"
    
    config = AppConfig(
        transcription=TranscriptionConfig(
            translate_to="en",
            clean_paragraphs=True
        )
    )
    
    with patch.object(Path, "exists", return_value=True):
        with patch("builtins.open", mock_open()) as mock_file:
            transcribe("dummy_audio.mp3", config)
            
    mock_translate.assert_called_once_with("Привет", "en")
