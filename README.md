[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![Русский](https://img.shields.io/badge/lang-Русский-red.svg)](README.ru.md) [![中文](https://img.shields.io/badge/lang-中文-green.svg)](README.zh.md)

# Video Transcriber

Automatic video transcription: watches a folder or program launches, records screen, transcribes locally (free!), sends Telegram notifications.

**Whisper is a completely free model (MIT license).** Everything runs locally — nothing leaves your machine.

## Features

- **Auto screen recording** — when a target program (Zoom, OBS, etc.) launches, screen recording starts automatically; when it closes, recording stops and transcription begins
- **Hardware auto-detect** — checks CPU/RAM/GPU and recommends the optimal Whisper model
- **First-run wizard** — interactive 6-step setup on first launch
- **Folder watcher** — watchdog automatically catches new video files
- **Audio extraction** — FFmpeg pulls MP3 without re-encoding
- **Transcription** — faster-whisper (local, free, private) with timestamps
- **Notifications** — Telegram bot reports when done with file paths
- **Autostart** — install as auto-start service with one command (Windows/macOS/Linux)
- **Interactive menu** — `menu.bat` / `menu.sh` with all modes
- **Cross-platform** — Windows, macOS, Linux

## Quick Start

### Windows

```bat
git clone https://github.com/checkerup/video-transcriber.git
cd video-transcriber
install.bat
menu.bat
```

### macOS / Linux

```bash
git clone https://github.com/checkerup/video-transcriber.git
cd video-transcriber
chmod +x install.sh menu.sh start.sh stop.sh
./install.sh
./menu.sh
```

On **first run**, the setup wizard launches automatically:
1. Hardware check → model recommendation
2. Folder setup (watch folder, output folder)
3. Language & transcript format selection (txt/srt/vtt)
4. Telegram setup (bot token + chat ID)
5. Process Watcher setup (auto-record on program launch)
6. Autostart offer

## Interactive Menu

Run `menu.bat` (Windows) or `./menu.sh` (macOS/Linux):

```
  ╔══════════════════════════════════════════════╗
  ║       Video Transcriber — Main Menu          ║
  ╚══════════════════════════════════════════════╝

  [1]  Setup / Install           (first run)
  [2]  Start daemon              (watch folder)
  [3]  Process single file       (one-shot)
  [4]  Screen recording          (manual, Ctrl+C stop)
  [5]  Watch process + record    (auto on program launch)
  [6]  Check hardware            (CPU/RAM/GPU)
  [7]  Re-run setup wizard
  [8]  Install autostart
  [9]  Uninstall autostart
  [10] Push to GitHub
  [0]  Exit
```

## Operating Modes

### 1. Daemon — Folder Watch

Watches a folder, new videos are processed automatically. If `program_names` are configured, Process Watcher runs in parallel.

```bash
python -m video_transcriber.main
```

### 2. Process Watcher — Auto-record on Program Launch

When a target program (e.g. Zoom) launches — screen recording starts automatically. When it closes — recording stops and transcription begins.

In `config.yaml`:
```yaml
process_watcher:
  program_names: ["Zoom.exe", "obs64.exe"]
  poll_interval: 5
```

Or via CLI:
```bash
python -m video_transcriber.main --watch-process "Zoom.exe"
```

Monitor multiple programs:
```bash
python -m video_transcriber.main --watch-process "Zoom.exe,Teams.exe"
```

### 3. Manual Screen Recording

Start recording → Ctrl+C → stop → transcribe:

```bash
python -m video_transcriber.main --record
```

### 4. Single File

Process a specific video without the daemon:

```bash
python -m video_transcriber.main --file "video.mp4"
```

## Full Pipeline

```
Video appears in folder (or screen recording finishes)
  → FFmpeg extracts audio track to MP3
  → faster-whisper transcribes (with timestamps)
  → Text saved (txt/srt/vtt)
  → Telegram bot sends notification with file paths
```

## CLI (all flags)

```bash
python -m video_transcriber.main                        # daemon (folder + process watcher)
python -m video_transcriber.main --file "vid.mp4"       # single file
python -m video_transcriber.main --record               # manual screen recording
python -m video_transcriber.main --watch-process "Zoom" # auto-record on program launch
python -m video_transcriber.main --setup                # re-run setup wizard
python -m video_transcriber.main --check-hardware       # detect hardware
python -m video_transcriber.main --install-autostart    # install autostart
python -m video_transcriber.main --uninstall-autostart  # remove autostart
python -m video_transcriber.main --config my.yaml       # custom config
python -m video_transcriber.main --verbose              # debug logging
```

## Configuration

`config.yaml` (created by wizard automatically, or manually from `config.example.yaml`):

```yaml
watch:
  folder: "~/Videos/Incoming"       # folder to monitor
  extensions: [.mp4, .mkv, .avi, .mov, .webm]
  delay_seconds: 10                 # wait before processing (file must finish writing)

processing:
  output_folder: "~/Videos/Processed"  # where to save results
  audio_format: "mp3"
  audio_bitrate: "192k"
  keep_audio: true                  # keep MP3 after transcription

transcription:
  model_size: "base"               # tiny/base/small/medium/large-v2
  device: "auto"                    # auto/cpu/cuda (auto = detect GPU)
  compute_type: "int8"             # int8/int8_float16/float16
  language: "en"                    # language or "auto" for auto-detect
  output_format: "txt"             # txt/srt/vtt
  word_timestamps: true             # timestamps for each word

telegram:
  bot_token: ""                    # from @BotFather (or in .env)
  chat_id: ""                      # your chat ID (or in .env)

recorder:
  fps: 30                          # screen recording FPS
  # video_size: "1920x1080"        # resolution (Linux/x11grab only)

process_watcher:
  program_names: ["Zoom.exe"]       # process names to watch for
  poll_interval: 5                  # seconds between checks
```

Secrets via `.env` (alternative to config.yaml):
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

## How Process Watcher Works

```
Zoom.exe launches
  → psutil detects process (every 5 sec)
  → FFmpeg starts screen recording (gdigrab/avfoundation/x11grab)
Zoom.exe exits
  → FFmpeg stops (sends 'q' signal)
  → Video saved to ~/Videos/Processed/screen_2025-01-15_14-30-00.mp4
  → Pipeline runs: MP3 → transcription → Telegram notification
```

## Screen Recording — Platforms

| OS | FFmpeg Method | Notes |
|----|---------------|-------|
| Windows | `-f gdigrab -i desktop` | Works out of the box |
| macOS | `-f avfoundation -i 1` | Requires Screen Recording permission in System Settings → Privacy |
| Linux | `-f x11grab -i :0.0` | Requires X11. On Wayland: use pipewire or switch to X11 |

## Whisper Models (free, MIT license)

The model downloads **once** automatically on first run. All OpenAI Whisper models are open-source (MIT), free forever.

| Size | RAM/VRAM | Speed | Quality | Auto-select when |
|------|----------|-------|---------|------------------|
| tiny | ~1 GB | fastest | basic | < 4GB RAM, no GPU |
| base | ~1 GB | fast | good | 4-8GB RAM or 1.5GB VRAM |
| small | ~2 GB | moderate | great | 8-16GB RAM or 2.5GB VRAM |
| medium | ~5 GB | slow | excellent | 16GB+ RAM or 5GB+ VRAM |
| large-v2 | ~10 GB | v.slow | best | 10GB+ VRAM |

## Autostart (OS-specific)

| OS | Method | Location |
|----|--------|----------|
| Windows | Task Scheduler | `schtasks /Create /SC ONLOGON` |
| macOS | LaunchAgent | `~/Library/LaunchAgents/com.video-transcriber.plist` |
| Linux | systemd user service | `~/.config/systemd/user/video-transcriber.service` |

## AI Summarization (Gemini)

You can enable automatic transcription summarization and chapter generation using the Gemini API. The summary will be saved to `{filename}_summary.md` and sent to your Telegram bot.

To enable it, set `summarization.enabled: true` in `config.yaml` and provide your `api_key`.

### Changing the Model
You can change the `summarization.model` parameter in `config.yaml` (e.g. to `gemini-1.5-pro` or `gemini-2.0-flash-exp`) or override it via CLI:
```bash
python -m video_transcriber.main --summarize --summarization-model "gemini-1.5-pro"
```

### Changing the Prompt
You can customize the prompt sent to Gemini by editing the `summarization.prompt` option in `config.yaml` or using the `--summarization-prompt` CLI option.

Use the `{text}` placeholder within your prompt to specify where the transcription text should be injected. For example:
```yaml
summarization:
  enabled: true
  api_key: "your_api_key"
  model: "gemini-1.5-flash"
  prompt: "Read the following transcription and summarize the main decisions in English: {text}"
```

If the prompt does not contain the `{text}` placeholder, the transcription text will automatically be appended to the end of the prompt.

## CUDA (GPU Acceleration)

The script auto-detects NVIDIA GPU via `torch.cuda` or `nvidia-smi`. If CUDA is available — transcription runs on GPU (3-10x faster than CPU).

Manual CUDA dependency install:
```bash
pip install video-transcriber[cuda]
```

In config: `device: "cuda"` (or `"auto"` — detects automatically).

## Requirements

- **Python 3.10+**
- **FFmpeg** — auto-installed via `install.bat` (winget) or `install.sh` (brew/apt)
- **NVIDIA GPU** (optional) — for GPU acceleration

## Project Structure

```
video-transcriber/
├── src/video_transcriber/
│   ├── hardware.py          # CPU/RAM/GPU detect, model recommendation
│   ├── setup_wizard.py      # interactive first-run wizard
│   ├── autostart.py         # autostart (Windows/macOS/Linux)
│   ├── process_watcher.py   # process monitoring (psutil)
│   ├── screen_recorder.py   # screen recording (FFmpeg)
│   ├── config.py            # config loader (YAML + .env)
│   ├── watcher.py           # folder watching (watchdog)
│   ├── extractor.py         # FFmpeg → MP3
│   ├── transcriber.py       # faster-whisper transcription
│   ├── notifier.py          # Telegram notifications
│   ├── pipeline.py          # pipeline orchestration
│   └── main.py              # CLI entry point
├── menu.bat / menu.sh       # interactive menu
├── install.bat / install.sh # auto-installer
├── start.bat / start.sh     # quick start
├── stop.bat / stop.sh       # stop service
├── config.example.yaml      # config example
├── .env.example             # secrets example
├── pyproject.toml           # Python package
├── requirements.txt         # dependencies
└── LICENSE                  # MIT
```

## License

MIT
