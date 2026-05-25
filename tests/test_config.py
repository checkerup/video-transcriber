from pathlib import Path
from video_transcriber.config import load_config

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
