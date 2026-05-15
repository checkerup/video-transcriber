# Video Transcriber

Автоматическая расшифровка видео: следит за папкой, извлекает аудио, транскрибирует локально (бесплатно!), шлет уведомление в Telegram.

**Whisper — полностью бесплатная модель (MIT лицензия).** Всё работает локально, ничего не уходит в облако.

## Возможности

- **Автодетект железа** — скрипт проверяет CPU/RAM/GPU и подбирает оптимальную модель
- **First-run визард** — при первом запуске интерактивная настройка (папки, модель, Telegram, автозапуск)
- **Слежка за папкой** — watchdog автоматически ловит новые `.mp4/.mkv/.avi/.mov/.webm`
- **Экстракция аудио** — FFmpeg вытягивает MP3 без перекодирования
- **Транскрибация** — faster-whisper (локально, бесплатно, приватно) с таймкодами
- **Уведомления** — Telegram-бот сообщает когда готово + пути к файлам
- **Автозапуск** — установка в автозапуск одной командой (Windows/macOS/Linux)
- **Одиночный режим** — обработать один файл без демона
- **Кроссплатформенный** — Windows, macOS, Linux

## Быстрый старт

### Windows

```bat
git clone https://github.com/YOU/video-transcriber.git
cd video-transcriber
install.bat
start.bat
```

### macOS / Linux

```bash
git clone https://github.com/YOU/video-transcriber.git
cd video-transcriber
chmod +x install.sh start.sh stop.sh
./install.sh
./start.sh
```

При **первом запуске** автоматически запустится визард:
1. Проверка железа → рекомендация модели
2. Настройка путей (watch/output folders)
3. Выбор языка и формата транскрипта
4. Настройка Telegram
5. Предложение установить в автозапуск

## CLI

```bash
# Демон (следит за папкой)
python -m video_transcriber.main

# Один файл
python -m video_transcriber.main --file "video.mp4"

# Перенастроить (визард)
python -m video_transcriber.main --setup

# Проверить железо
python -m video_transcriber.main --check-hardware

# Установить автозапуск
python -m video_transcriber.main --install-autostart

# Удалить автозапуск
python -m video_transcriber.main --uninstall-autostart

# Свой конфиг
python -m video_transcriber.main --config my_config.yaml

# Debug лог
python -m video_transcriber.main --verbose
```

## Конфигурация

`config.yaml` (создается визардом или вручную из `config.example.yaml`):

```yaml
watch:
  folder: "~/Videos/Incoming"
  extensions: [.mp4, .mkv, .avi, .mov, .webm]
  delay_seconds: 10

processing:
  output_folder: "~/Videos/Processed"
  audio_format: "mp3"
  audio_bitrate: "192k"

transcription:
  model_size: "base"        # tiny/base/small/medium/large-v2
  device: "auto"             # auto/cpu/cuda (auto = detect GPU)
  compute_type: "int8"      # int8/int8_float16/float16
  language: "ru"             # язык или "auto"
  output_format: "txt"       # txt/srt/vtt

telegram:
  bot_token: ""              # от @BotFather (или в .env)
  chat_id: ""                # ваш chat ID (или в .env)
```

Секреты через `.env`:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

## Модели Whisper (бесплатные, MIT)

| Размер | RAM/VRAM | Скорость | Качество | Автовыбор при |
|--------|----------|----------|----------|---------------|
| tiny   | ~1 GB    | fastest  | basic    | < 4GB RAM, нет GPU |
| base   | ~1 GB    | fast     | good     | 4-8GB RAM или 1.5GB VRAM |
| small  | ~2 GB    | moderate | great    | 8-16GB RAM или 2.5GB VRAM |
| medium | ~5 GB    | slow     | excellent| 16GB+ RAM или 5GB+ VRAM |
| large-v2| ~10 GB  | v.slow   | best     | 10GB+ VRAM |

Модель скачивается автоматически при первом запуске. Скрипт сам подберёт оптимальную по вашему железу.

## Автозапуск

Скрипт автоматически определяет ОС и ставит в автозапуск:

| ОС | Метод |
|----|-------|
| Windows | Task Scheduler (`schtasks`) |
| macOS | LaunchAgent (`~/Library/LaunchAgents/`) |
| Linux | systemd user service (`~/.config/systemd/user/`) |

## CUDA (GPU ускорение)

Для NVIDIA GPU скрипт автоматически обнаружит CUDA и использует GPU.
Если `torch` не установлен — работает на CPU.

Ручная установка CUDA:
```bash
pip install video-transcriber[cuda]
```

## Архитектура

```
src/video_transcriber/
├── hardware.py      # детект CPU/RAM/GPU, рекомендация модели
├── setup_wizard.py  # интерактивный визард первого запуска
├── autostart.py     # установка в автозапуск (win/mac/linux)
├── config.py        # загрузка конфига (YAML + .env)
├── watcher.py       # watchdog слежка за папкой
├── extractor.py     # FFmpeg экстракция MP3
├── transcriber.py   # faster-whisper транскрибация
├── notifier.py      # Telegram уведомления
├── pipeline.py      # оркестрация пайплайна
└── main.py          # CLI входная точка
```

## Лицензия

MIT
