import os
import sys
from pathlib import Path

import yaml

from .autostart import install_autostart, uninstall_autostart
from .config import AppConfig, ProcessingConfig, TelegramConfig, TranscriptionConfig, WatchConfig
from .hardware import MODEL_SPECS, HardwareInfo, detect_hardware, print_hardware_report

CONFIG_MARKER = ".setup_done"


def _prompt(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"  {prompt}{suffix}: ").strip()
        if val:
            return val
        if default:
            return default
        print("    Please enter a value.")


def _confirm(prompt: str, default: bool = True) -> bool:
    yes_no = "Y/n" if default else "y/N"
    val = input(f"  {prompt} [{yes_no}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes", "да", "д")


def _choose(prompt: str, options: list[str], default: int = 0) -> int:
    print(f"  {prompt}:")
    for i, opt in enumerate(options):
        marker = ">" if i == default else " "
        print(f"    {marker} {i + 1}. {opt}")
    while True:
        val = input(f"  Choice [{default + 1}]: ").strip()
        if not val:
            return default
        try:
            idx = int(val) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print("    Invalid choice.")


def _default_paths() -> tuple[str, str]:
    home = Path.home()
    videos = home / "Videos"
    if not videos.exists():
        videos = home / "videos"
        videos.mkdir(exist_ok=True)
    watch = str(videos / "Incoming")
    output = str(videos / "Processed")
    return watch, output


def run_setup_wizard(config_path: Path | None = None) -> AppConfig:
    print("\n" + "=" * 55)
    print("  Video Transcriber — First Run Setup Wizard")
    print("=" * 55)
    print()

    hw = detect_hardware()
    print_hardware_report(hw)

    default_watch, default_output = _default_paths()

    # --- Step 1: Folders ---
    print("Step 1: Folder Setup")
    print(f"  Detected OS: {hw.os_name}")
    print()
    watch_folder = _prompt("Folder to watch for new videos", default_watch)
    output_folder = _prompt("Folder for processed files", default_output)
    print()

    # --- Step 2: Model ---
    print("Step 2: Transcription Model")
    model_names = list(MODEL_SPECS.keys())
    recommended_idx = model_names.index(hw.recommended_model) if hw.recommended_model in model_names else 1
    spec = MODEL_SPECS[hw.recommended_model]
    print(f"  Recommended for your hardware: {hw.recommended_model}")
    print(f"    Quality: {spec['quality']} | Speed: {spec['speed']} | RAM: {spec['ram']}")
    print()

    model_labels = [f"{m} — quality: {MODEL_SPECS[m]['quality']}, speed: {MODEL_SPECS[m]['speed']}" for m in model_names]
    chosen_idx = _choose("Select model", model_labels, recommended_idx)
    chosen_model = model_names[chosen_idx]
    print()

    # --- Step 3: Language ---
    print("Step 3: Language")
    lang_options = ["ru — Russian", "en — English", "uk — Ukrainian", "de — German", "auto — Auto-detect"]
    lang_values = ["ru", "en", "uk", "de", "auto"]
    default_lang_idx = lang_values.index("ru")
    lang_idx = _choose("Primary language for transcription", lang_options, default_lang_idx)
    chosen_lang = lang_values[lang_idx]
    print()

    # --- Step 4: Output format ---
    print("Step 4: Transcript Format")
    fmt_options = ["txt — plain text with timestamps", "srt — SubRip subtitles", "vtt — WebVTT subtitles"]
    fmt_values = ["txt", "srt", "vtt"]
    fmt_idx = _choose("Output format", fmt_options, 0)
    chosen_fmt = fmt_values[fmt_idx]
    print()

    # --- Step 5: Telegram ---
    print("Step 5: Telegram Notifications")
    print("  Create a bot via @BotFather and get your chat_id via @userinfobot")
    print()
    has_tg = _confirm("Set up Telegram notifications?", default=True)
    bot_token = ""
    chat_id = ""
    if has_tg:
        bot_token = _prompt("Bot token (from @BotFather)")
        chat_id = _prompt("Chat ID (from @userinfobot)")
    print()

    # --- Step 6: Autostart ---
    print("Step 6: Autostart")
    print(f"  OS detected: {hw.os_name}")
    autostart = _confirm(
        f"Install Video Transcriber as autostart service on {hw.os_name}?",
        default=True,
    )
    print()

    # --- Build config ---
    cfg = AppConfig(
        watch=WatchConfig(folder=watch_folder),
        processing=ProcessingConfig(output_folder=output_folder),
        transcription=TranscriptionConfig(
            model_size=chosen_model,
            device=hw.recommended_device,
            compute_type=hw.recommended_compute,
            language=chosen_lang,
            output_format=chosen_fmt,
        ),
        telegram=TelegramConfig(bot_token=bot_token, chat_id=chat_id),
    )

    # --- Save config ---
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"

    config_data = {
        "watch": {"folder": cfg.watch.folder, "extensions": cfg.watch.extensions, "delay_seconds": cfg.watch.delay_seconds},
        "processing": {
            "output_folder": cfg.processing.output_folder,
            "audio_format": cfg.processing.audio_format,
            "audio_bitrate": cfg.processing.audio_bitrate,
            "keep_audio": cfg.processing.keep_audio,
        },
        "transcription": {
            "model_size": cfg.transcription.model_size,
            "device": cfg.transcription.device,
            "compute_type": cfg.transcription.compute_type,
            "language": cfg.transcription.language,
            "output_format": cfg.transcription.output_format,
            "word_timestamps": cfg.transcription.word_timestamps,
        },
        "telegram": {"bot_token": bot_token, "chat_id": chat_id},
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Save .env
    env_path = config_path.parent / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        if bot_token:
            f.write(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
        if chat_id:
            f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")

    # Mark setup done
    marker_path = config_path.parent / CONFIG_MARKER
    marker_path.write_text("done\n")

    # Install autostart
    if autostart:
        print("Installing autostart service...")
        success = install_autostart(config_path=config_path)
        if success:
            print("  Autostart installed successfully!")
        else:
            print("  Autostart installation failed. You can try again later with --install-autostart")
    print()

    print("=" * 55)
    print("  Setup complete!")
    print(f"  Config saved to: {config_path}")
    print(f"  Watch folder:    {cfg.watch.folder}")
    print(f"  Output folder:   {cfg.processing.output_folder}")
    print(f"  Model:           {chosen_model} ({hw.recommended_device})")
    if has_tg:
        print(f"  Telegram:        configured")
    if autostart:
        print(f"  Autostart:       installed")
    print("=" * 55)
    print()
    print("  Run: start.bat (Windows) or ./start.sh (macOS/Linux)")
    print()

    return cfg


def is_setup_done(config_path: Path | None = None) -> bool:
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent
    marker = config_path / CONFIG_MARKER if config_path.is_dir() else config_path.parent / CONFIG_MARKER
    return marker.exists()
