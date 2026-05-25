import os
from pathlib import Path
from video_transcriber.config import load_config, AppConfig

def test_expand_user_paths(tmp_path):
    # Create a test config.yaml with paths containing ~
    config_content = """
    watch:
      folder: "~/IncomingTestDir"
    processing:
      output_folder: "~/ProcessedTestDir"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)
    
    cfg = load_config(cfg_file)
    
    # Assert that paths are expanded and don't contain ~
    assert "~" not in cfg.watch.folder
    assert "~" not in cfg.processing.output_folder
    assert Path(cfg.watch.folder).is_absolute()

def test_empty_and_null_sections(tmp_path):
    # Create a config.yaml where sections and keys are explicitly null/empty
    config_content = """
    watch:
    processing: null
    transcription:
      model_size: null
      device: null
      compute_type: null
      language: null
      output_format: null
      word_timestamps: null
    telegram: null
    recorder:
      fps: null
      video_size: null
    process_watcher:
      program_names: null
      poll_interval: null
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)
    
    # Should load successfully without throwing AttributeError or TypeError
    cfg = load_config(cfg_file)
    assert isinstance(cfg, AppConfig)
    
    # Check that defaults are correctly populated
    assert cfg.watch.folder is not None
    assert cfg.processing.output_folder is not None
    assert cfg.transcription.model_size == "base"
    assert cfg.transcription.device in ("cpu", "cuda")
    assert cfg.transcription.compute_type == "int8"
    assert cfg.transcription.language == "ru"
    assert cfg.transcription.output_format == "txt"
    assert cfg.transcription.word_timestamps is True
    assert cfg.telegram.bot_token == ""
    assert cfg.telegram.chat_id == ""
    assert cfg.recorder.fps == 30
    assert cfg.recorder.video_size is None
    assert cfg.process_watcher.program_names == []
    assert cfg.process_watcher.poll_interval == 5

def test_no_filesystem_side_effects(tmp_path):
    # Ensure we point to directories that do not exist
    watch_dir = tmp_path / "non_existent_watch"
    output_dir = tmp_path / "non_existent_output"
    
    assert not watch_dir.exists()
    assert not output_dir.exists()
    
    config_content = f"""
    watch:
      folder: "{watch_dir.as_posix()}"
    processing:
      output_folder: "{output_dir.as_posix()}"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)
    
    # Load config
    cfg = load_config(cfg_file)
    
    # Verify folders were NOT created
    assert not watch_dir.exists()
    assert not output_dir.exists()
    assert Path(cfg.watch.folder) == Path(watch_dir)
    assert Path(cfg.processing.output_folder) == Path(output_dir)
