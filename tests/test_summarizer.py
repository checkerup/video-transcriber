import pytest
from unittest.mock import patch, MagicMock
import requests

from video_transcriber.config import AppConfig, SummarizationConfig
from video_transcriber.summarizer import generate_summary

def test_generate_summary_disabled():
    config = AppConfig(
        summarization=SummarizationConfig(
            enabled=False,
            api_key="test_key"
        )
    )
    result = generate_summary("some transcript text", config)
    assert result == ""

def test_generate_summary_missing_api_key():
    config = AppConfig(
        summarization=SummarizationConfig(
            enabled=True,
            api_key=""
        )
    )
    result = generate_summary("some transcript text", config)
    assert result == ""

@patch("requests.post")
def test_generate_summary_success(mock_post):
    config = AppConfig(
        summarization=SummarizationConfig(
            enabled=True,
            provider="gemini",
            api_key="test_key",
            model="gemini-1.5-flash"
        )
    )
    
    # Mock successful response from Gemini API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "This is the mocked summary from Gemini."
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    transcript_text = "Hello world transcription text"
    result = generate_summary(transcript_text, config)

    assert result == "This is the mocked summary from Gemini."
    
    # Verify mock call details
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    url = args[0]
    assert "gemini-1.5-flash" in url
    assert "test_key" in url
    
    json_data = kwargs["json"]
    assert "contents" in json_data
    prompt_text = json_data["contents"][0]["parts"][0]["text"]
    assert transcript_text in prompt_text

@patch("requests.post")
def test_generate_summary_http_error(mock_post):
    config = AppConfig(
        summarization=SummarizationConfig(
            enabled=True,
            provider="gemini",
            api_key="test_key"
        )
    )
    
    # Mock failing response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
    mock_post.return_value = mock_response

    result = generate_summary("transcript", config)
    assert result == ""
