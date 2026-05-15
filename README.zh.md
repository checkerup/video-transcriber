[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![Русский](https://img.shields.io/badge/lang-Русский-red.svg)](README.ru.md) [![中文](https://img.shields.io/badge/lang-中文-green.svg)](README.zh.md)

# Video Transcriber

自动视频转录：监控文件夹或程序启动，录制屏幕，本地转录（免费！），发送 Telegram 通知。

**Whisper 是完全免费的模型（MIT 许可证）。** 所有内容在本地运行，不会上传到云端。

## 功能特点

- **自动屏幕录制** — 当目标程序（Zoom、OBS 等）启动时，自动开始屏幕录制；关闭时停止录制并开始转录
- **硬件自动检测** — 检查 CPU/RAM/GPU 并推荐最优 Whisper 模型
- **首次运行向导** — 首次启动时自动运行 6 步交互式设置
- **文件夹监控** — watchdog 自动捕获新视频文件
- **音频提取** — FFmpeg 无需重编码即可提取 MP3
- **转录** — faster-whisper（本地、免费、隐私）带时间戳
- **通知** — Telegram 机器人完成后发送文件路径通知
- **自动启动** — 一键安装为自启动服务（Windows/macOS/Linux）
- **交互式菜单** — `menu.bat` / `menu.sh` 包含所有模式
- **跨平台** — Windows、macOS、Linux

## 快速开始

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

**首次运行**时，设置向导会自动启动：
1. 硬件检测 → 模型推荐
2. 文件夹设置（监控文件夹、输出文件夹）
3. 语言和转录格式选择（txt/srt/vtt）
4. Telegram 设置（机器人令牌 + 聊天 ID）
5. 进程监控器设置（程序启动时自动录制）
6. 自启动安装提示

## 交互式菜单

运行 `menu.bat`（Windows）或 `./menu.sh`（macOS/Linux）：

```
  ╔══════════════════════════════════════════════╗
  ║       Video Transcriber — Main Menu          ║
  ╚══════════════════════════════════════════════╝

  [1]  Setup / Install           (首次运行)
  [2]  Start daemon              (监控文件夹)
  [3]  Process single file       (单文件处理)
  [4]  Screen recording          (手动录制，Ctrl+C 停止)
  [5]  Watch process + record    (程序启动时自动录制)
  [6]  Check hardware            (CPU/RAM/GPU)
  [7]  Re-run setup wizard       (重新运行设置向导)
  [8]  Install autostart         (安装自启动)
  [9]  Uninstall autostart       (卸载自启动)
  [10] Push to GitHub
  [0]  Exit
```

## 运行模式

### 1. 守护进程 — 文件夹监控

监控文件夹，新视频自动处理。如果配置了 `program_names`，进程监控器会并行运行。

```bash
python -m video_transcriber.main
```

### 2. 进程监控器 — 程序启动时自动录制

当目标程序（如 Zoom）启动时，自动开始屏幕录制。关闭时停止录制并开始转录。

在 `config.yaml` 中：
```yaml
process_watcher:
  program_names: ["Zoom.exe", "obs64.exe"]
  poll_interval: 5
```

或通过命令行：
```bash
python -m video_transcriber.main --watch-process "Zoom.exe"
```

监控多个程序：
```bash
python -m video_transcriber.main --watch-process "Zoom.exe,Teams.exe"
```

### 3. 手动屏幕录制

开始录制 → Ctrl+C → 停止 → 转录：

```bash
python -m video_transcriber.main --record
```

### 4. 单文件处理

处理特定视频，无需守护进程：

```bash
python -m video_transcriber.main --file "video.mp4"
```

## 完整流程

```
视频出现在文件夹中（或屏幕录制完成）
  → FFmpeg 提取音轨为 MP3
  → faster-whisper 转录（带时间戳）
  → 文本保存（txt/srt/vtt）
  → Telegram 机器人发送通知及文件路径
```

## 命令行（所有参数）

```bash
python -m video_transcriber.main                        # 守护进程（文件夹 + 进程监控）
python -m video_transcriber.main --file "vid.mp4"       # 单文件
python -m video_transcriber.main --record               # 手动屏幕录制
python -m video_transcriber.main --watch-process "Zoom" # 程序启动时自动录制
python -m video_transcriber.main --setup                # 重新运行设置向导
python -m video_transcriber.main --check-hardware       # 检测硬件
python -m video_transcriber.main --install-autostart    # 安装自启动
python -m video_transcriber.main --uninstall-autostart  # 卸载自启动
python -m video_transcriber.main --config my.yaml       # 自定义配置
python -m video_transcriber.main --verbose              # 调试日志
```

## 配置

`config.yaml`（由向导自动创建，或从 `config.example.yaml` 手动创建）：

```yaml
watch:
  folder: "~/Videos/Incoming"       # 监控的文件夹
  extensions: [.mp4, .mkv, .avi, .mov, .webm]
  delay_seconds: 10                 # 处理前等待时间（文件必须写入完成）

processing:
  output_folder: "~/Videos/Processed"  # 结果保存位置
  audio_format: "mp3"
  audio_bitrate: "192k"
  keep_audio: true                  # 转录后保留 MP3

transcription:
  model_size: "base"               # tiny/base/small/medium/large-v2
  device: "auto"                    # auto/cpu/cuda（auto = 自动检测 GPU）
  compute_type: "int8"             # int8/int8_float16/float16
  language: "zh"                    # 语言或 "auto" 自动检测
  output_format: "txt"             # txt/srt/vtt
  word_timestamps: true             # 每个词的时间戳

telegram:
  bot_token: ""                    # 来自 @BotFather（或在 .env 中）
  chat_id: ""                      # 你的聊天 ID（或在 .env 中）

recorder:
  fps: 30                          # 屏幕录制帧率
  # video_size: "1920x1080"        # 分辨率（仅 Linux/x11grab）

process_watcher:
  program_names: ["Zoom.exe"]       # 要监控的进程名称
  poll_interval: 5                  # 检查间隔（秒）
```

通过 `.env` 设置密钥（config.yaml 的替代方案）：
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

## 进程监控器工作原理

```
Zoom.exe 启动
  → psutil 检测到进程（每 5 秒）
  → FFmpeg 开始屏幕录制（gdigrab/avfoundation/x11grab）
Zoom.exe 退出
  → FFmpeg 停止（发送 'q' 信号）
  → 视频保存到 ~/Videos/Processed/screen_2025-01-15_14-30-00.mp4
  → 运行流程：MP3 → 转录 → Telegram 通知
```

## 屏幕录制 — 平台支持

| 操作系统 | FFmpeg 方法 | 备注 |
|---------|------------|------|
| Windows | `-f gdigrab -i desktop` | 开箱即用 |
| macOS | `-f avfoundation -i 1` | 需要在系统设置 → 隐私 → 屏幕录制中授权 |
| Linux | `-f x11grab -i :0.0` | 需要 X11。Wayland 下：使用 pipewire 或切换到 X11 |

## Whisper 模型（免费，MIT 许可证）

模型在首次运行时**自动下载一次**。所有 OpenAI Whisper 模型都是开源的（MIT），永久免费。

| 大小 | RAM/VRAM | 速度 | 质量 | 自动选择条件 |
|------|----------|------|------|------------|
| tiny | ~1 GB | 最快 | 基础 | < 4GB RAM，无 GPU |
| base | ~1 GB | 快 | 良好 | 4-8GB RAM 或 1.5GB VRAM |
| small | ~2 GB | 中等 | 很好 | 8-16GB RAM 或 2.5GB VRAM |
| medium | ~5 GB | 慢 | 优秀 | 16GB+ RAM 或 5GB+ VRAM |
| large-v2 | ~10 GB | 很慢 | 最佳 | 10GB+ VRAM |

## 自启动（操作系统特定）

| 操作系统 | 方法 | 位置 |
|---------|------|------|
| Windows | 任务计划程序 | `schtasks /Create /SC ONLOGON` |
| macOS | LaunchAgent | `~/Library/LaunchAgents/com.video-transcriber.plist` |
| Linux | systemd 用户服务 | `~/.config/systemd/user/video-transcriber.service` |

## CUDA（GPU 加速）

脚本通过 `torch.cuda` 或 `nvidia-smi` 自动检测 NVIDIA GPU。如果 CUDA 可用，转录将在 GPU 上运行（比 CPU 快 3-10 倍）。

手动安装 CUDA 依赖：
```bash
pip install video-transcriber[cuda]
```

在配置中：`device: "cuda"`（或 `"auto"` — 自动检测）。

## 系统要求

- **Python 3.10+**
- **FFmpeg** — 通过 `install.bat`（winget）或 `install.sh`（brew/apt）自动安装
- **NVIDIA GPU**（可选）— 用于 GPU 加速

## 项目结构

```
video-transcriber/
├── src/video_transcriber/
│   ├── hardware.py          # CPU/RAM/GPU 检测，模型推荐
│   ├── setup_wizard.py      # 首次运行交互式向导
│   ├── autostart.py         # 自启动（Windows/macOS/Linux）
│   ├── process_watcher.py   # 进程监控（psutil）
│   ├── screen_recorder.py   # 屏幕录制（FFmpeg）
│   ├── config.py            # 配置加载（YAML + .env）
│   ├── watcher.py           # 文件夹监控（watchdog）
│   ├── extractor.py         # FFmpeg → MP3
│   ├── transcriber.py       # faster-whisper 转录
│   ├── notifier.py          # Telegram 通知
│   ├── pipeline.py          # 流程编排
│   └── main.py              # 命令行入口
├── menu.bat / menu.sh       # 交互式菜单
├── install.bat / install.sh # 自动安装
├── start.bat / start.sh     # 快速启动
├── stop.bat / stop.sh       # 停止服务
├── config.example.yaml      # 配置示例
├── .env.example             # 密钥示例
├── pyproject.toml           # Python 包
├── requirements.txt         # 依赖
└── LICENSE                  # MIT
```

## 许可证

MIT
