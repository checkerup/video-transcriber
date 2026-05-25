from video_transcriber.config import AppConfig, ProcessingConfig
from video_transcriber.extractor import convert_video_to_mp3, copy_audio_to_output
from unittest.mock import patch, MagicMock
from pathlib import Path

@patch("subprocess.run")
def test_convert_to_mp3_with_silence_removal(mock_run):
    mock_run.return_value.returncode = 0
    config = AppConfig(processing=ProcessingConfig(silence_removal=True))
    
    with patch.object(Path, "mkdir"):
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                res = convert_video_to_mp3("input.mp4", config)
            
    # Check that ffmpeg command contains silence removal filter
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert "-af" in cmd
    assert any("silenceremove" in item for item in cmd)
    assert any("input.mp4" in item for item in cmd)
    assert res == str(Path(config.processing.output_folder) / "input.mp3")

@patch("shutil.copy2")
def test_copy_audio_to_output(mock_copy):
    config = AppConfig()
    
    # We want to mock exists specifically:
    def exists_side_effect(self_obj):
        # If the path points to the source, return True, else False
        return self_obj.name == "my_audio.mp3" and "Processed" not in str(self_obj)
        
    with patch.object(Path, "mkdir"):
        with patch("pathlib.Path.exists", new=exists_side_effect):
            res = copy_audio_to_output("my_audio.mp3", config)
        
    mock_copy.assert_called_once()
    assert res == str(Path(config.processing.output_folder) / "my_audio.mp3")
