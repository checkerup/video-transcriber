import os
from pathlib import Path
from video_transcriber.config import load_config, AppConfig, _as_bool, _as_int, _as_list

def test_expand_user_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    
    # Create a test config.yaml with paths containing ~
    config_content = """
    watch:
      folder: "~/IncomingTestDir"
    processing:
      output_folder: "~/ProcessedTestDir"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)
    
    cfg = load_config(cfg_file, load_env_file=False)
    
    # Assert that paths are expanded and don't contain ~
    assert "~" not in cfg.watch.folder
    assert "~" not in cfg.processing.output_folder
    assert Path(cfg.watch.folder).is_absolute()

def test_empty_and_null_sections(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    
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
    cfg = load_config(cfg_file, load_env_file=False)
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

def test_no_filesystem_side_effects(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    
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
    cfg = load_config(cfg_file, load_env_file=False)
    
    # Verify folders were NOT created
    assert not watch_dir.exists()
    assert not output_dir.exists()
    assert Path(cfg.watch.folder) == Path(watch_dir)
    assert Path(cfg.processing.output_folder) == Path(output_dir)


def test_robustness_nested_sections_and_type_casting(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    config_content = """
    watch:
      delay_seconds: "15"
    processing:
      keep_audio: 1
    transcription:
      word_timestamps: 0
    telegram: 42
    recorder:
      fps: "60"
    process_watcher:
      poll_interval: "8"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)

    cfg = load_config(cfg_file, load_env_file=False)
    assert isinstance(cfg, AppConfig)

    assert cfg.watch.delay_seconds == 15
    assert cfg.processing.keep_audio is True
    assert cfg.transcription.word_timestamps is False
    assert cfg.recorder.fps == 60
    assert cfg.process_watcher.poll_interval == 8


def test_non_dict_nested_sections(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    config_content = """
    watch: "invalid_string"
    processing: 123
    transcription: []
    telegram: false
    recorder: 0.5
    process_watcher: "another_invalid"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)

    cfg = load_config(cfg_file, load_env_file=False)
    assert isinstance(cfg, AppConfig)

    # Check that it falls back to defaults for each
    assert cfg.watch.folder is not None
    assert cfg.processing.keep_audio is True
    assert cfg.transcription.word_timestamps is True
    assert cfg.telegram.bot_token == ""
    assert cfg.recorder.fps == 30
    assert cfg.process_watcher.poll_interval == 5


def test_as_bool():
    # True values
    assert _as_bool("true", False) is True
    assert _as_bool("1", False) is True
    assert _as_bool("yes", False) is True
    assert _as_bool("on", False) is True
    assert _as_bool("  TRUE  ", False) is True
    assert _as_bool(True, False) is True
    assert _as_bool(123, False) is True

    # False values
    assert _as_bool("false", True) is False
    assert _as_bool("0", True) is False
    assert _as_bool("no", True) is False
    assert _as_bool("off", True) is False
    assert _as_bool("  FALSE  ", True) is False
    assert _as_bool(False, True) is False
    assert _as_bool(0, True) is False

    # Default values on None
    assert _as_bool(None, True) is True
    assert _as_bool(None, False) is False


def test_as_int():
    # Valid conversions
    assert _as_int("123", 10) == 123
    assert _as_int(45, 10) == 45
    assert _as_int(12.34, 10) == 12

    # Invalid conversions falling back to default
    assert _as_int("abc", 10) == 10
    assert _as_int(None, 10) == 10
    assert _as_int([], 10) == 10
    assert _as_int({}, 10) == 10


def test_as_list():
    # List conversion
    assert _as_list(["a", "b", 123], ["default"]) == ["a", "b", "123"]
    # String conversion
    assert _as_list("a, b, c", ["default"]) == ["a", "b", "c"]
    # String with empty elements
    assert _as_list("a,, b, ,c", ["default"]) == ["a", "b", "c"]
    # None fallback
    assert _as_list(None, ["default"]) == ["default"]
    # Invalid type fallback
    assert _as_list(123, ["default"]) == ["default"]


def test_malformed_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    # Completely malformed YAML that will fail yaml.safe_load
    config_content = """
    watch:
      [invalid yaml
      - {
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)

    # Should not raise exception and return default AppConfig
    cfg = load_config(cfg_file, load_env_file=False)
    assert isinstance(cfg, AppConfig)
    assert cfg.watch.delay_seconds == 10
    assert cfg.processing.keep_audio is True
    assert cfg.transcription.word_timestamps is True
    assert cfg.recorder.fps == 30
    assert cfg.process_watcher.poll_interval == 5


def test_path_string_coercion(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    # Config with non-string paths
    config_content = """
    watch:
      folder: 12345
    processing:
      output_folder: true
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)

    cfg = load_config(cfg_file, load_env_file=False)
    assert cfg.watch.folder == "12345"
    assert cfg.processing.output_folder == "True"


def test_new_config_fields(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    config_content = """
    processing:
      silence_removal: true
    transcription:
      translate_to: "ru"
      clean_paragraphs: true
    summarization:
      enabled: true
      provider: "gemini"
      api_key: "gemini_secret_123"
      model: "gemini-1.5-pro"
      prompt: "My Custom Prompt"
    """
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(config_content)

    cfg = load_config(cfg_file, load_env_file=False)
    assert cfg.processing.silence_removal is True
    assert cfg.transcription.translate_to == "ru"
    assert cfg.transcription.clean_paragraphs is True
    assert cfg.summarization.enabled is True
    assert cfg.summarization.provider == "gemini"
    assert cfg.summarization.api_key == "gemini_secret_123"
    assert cfg.summarization.model == "gemini-1.5-pro"
    assert cfg.summarization.prompt == "My Custom Prompt"


