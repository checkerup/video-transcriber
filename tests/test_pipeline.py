import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from video_transcriber.config import AppConfig, ProcessingConfig, SummarizationConfig
from video_transcriber.pipeline import process_file, process_video

@pytest.fixture
def config():
    return AppConfig(
        processing=ProcessingConfig(
            output_folder="C:/Processed",
            keep_audio=True
        ),
        summarization=SummarizationConfig(
            enabled=True,
            api_key="test_key"
        )
    )

@patch("video_transcriber.pipeline.copy_audio_to_output")
@patch("video_transcriber.pipeline.transcribe")
@patch("video_transcriber.pipeline.generate_summary")
@patch("video_transcriber.pipeline.send_notification")
@patch("video_transcriber.pipeline.copy_video_to_output")
@patch("video_transcriber.pipeline.extract_audio")
def test_process_audio_file(
    mock_extract_audio,
    mock_copy_video,
    mock_send_notification,
    mock_generate_summary,
    mock_transcribe,
    mock_copy_audio,
    config
):
    mock_copy_audio.return_value = "C:/Processed/audio.mp3"
    mock_transcribe.return_value = "C:/Processed/audio.txt"
    mock_generate_summary.return_value = "Mocked Summary content"

    # We mock reading the transcript inside pipeline
    with patch("builtins.open", mock_open(read_data="Mocked transcript text")):
        with patch("pathlib.Path.exists", return_value=True):
            result = process_file("input.mp3", config)

    # Assertions
    mock_copy_audio.assert_called_once_with("input.mp3", config)
    mock_transcribe.assert_called_once_with("C:/Processed/audio.mp3", config, speaker_turns=None)
    mock_generate_summary.assert_called_once_with("Mocked transcript text", config)
    
    # Check that video copying and audio extraction were skipped
    mock_copy_video.assert_not_called()
    mock_extract_audio.assert_not_called()

    # Check result keys
    assert result["video"] is None
    assert result["audio"] == "C:/Processed/audio.mp3"
    assert result["transcript"] == "C:/Processed/audio.txt"
    assert Path(result["summary"]) == Path("C:/Processed/audio_summary.md")
    assert result["error"] is None

    # Check notification call
    mock_send_notification.assert_called_once()
    _, kwargs = mock_send_notification.call_args
    assert kwargs["config"] == config
    assert kwargs["video_path"] is None
    assert kwargs["audio_path"] == "C:/Processed/audio.mp3"
    assert kwargs["transcript_path"] == "C:/Processed/audio.txt"
    assert kwargs["error"] is None
    assert Path(kwargs["summary_path"]) == Path("C:/Processed/audio_summary.md")

@patch("video_transcriber.pipeline.copy_video_to_output")
@patch("video_transcriber.pipeline.extract_audio")
@patch("video_transcriber.pipeline.transcribe")
@patch("video_transcriber.pipeline.generate_summary")
@patch("video_transcriber.pipeline.send_notification")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.unlink")
def test_process_video_file_keep_audio_false(
    mock_unlink,
    mock_exists,
    mock_send_notification,
    mock_generate_summary,
    mock_transcribe,
    mock_extract_audio,
    mock_copy_video,
    config
):
    config.processing.keep_audio = False
    
    mock_copy_video.return_value = "C:/Processed/video.mp4"
    mock_extract_audio.return_value = "C:/Processed/video.mp3"
    mock_transcribe.return_value = "C:/Processed/video.txt"
    mock_generate_summary.return_value = ""

    with patch("builtins.open", mock_open(read_data="Transcription")):
        result = process_file("input.mp4", config)

    # Verify video flow
    mock_copy_video.assert_called_once_with("input.mp4", config)
    mock_extract_audio.assert_called_once_with("C:/Processed/video.mp4", config)
    mock_transcribe.assert_called_once_with("C:/Processed/video.mp3", config, speaker_turns=None)
    
    # Assert temporary audio was unlinked/deleted
    mock_unlink.assert_called_once()
    
    assert result["video"] == "C:/Processed/video.mp4"
    assert result["audio"] == "C:/Processed/video.mp3"
    assert result["transcript"] == "C:/Processed/video.txt"
    assert "summary" not in result or result["summary"] is None

def test_unsupported_file_format(config):
    result = process_file("input.txt", config)
    assert result["error"] is not None
    assert "Unsupported file format" in result["error"]

def test_backward_compatibility_alias(config):
    # process_video should exist and do the same as process_file
    with patch("video_transcriber.pipeline.process_file") as mock_pf:
        process_video("input.mp4", config)
        mock_pf.assert_called_once_with("input.mp4", config)
