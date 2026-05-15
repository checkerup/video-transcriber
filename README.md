# Video Transcriber

Автоматическая расшифровка видео: следит за папкой или запуском программ, записывает экран, транскрибирует локально (бесплатно!), шлет уведомление в Telegram.

**Whisper — полностью бесплатная модель (MIT лицензия).** Всё работает локально, ничего не уходит в облако.

## Возможности

- **Автозапись экрана** — при запуске программы (Zoom, OBS и т.д.) автоматически начинается запись экрана, при закрытии — стоп + транскрипция
- **Автодетект железа** — скрипт проверяет CPU/RAM/GPU и подбирает оптимальную модель
- **First-run визард** — при первом запуске интерактивная настройка
- **Слежка за папкой** — watchdog автоматически ловит новые видеофайлы
- **Экстракция аудио** — FFmpeg вытягивает MP3 без перекодирования
- **Транскрибация** — faster-whisper (локально, бесплатно, приватно) с таймкодами
- **Уведомления** — Telegram-бот сообщает когда готово
- **Автозапуск** — установка в автозапуск одной командой (Windows/macOS/Linux)
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
2. Настройка путей
3. Выбор языка и формата транскрипта
4. Настройка Telegram
5. Настройка Process Watcher (автозапись при запуске программы)
6. Автозапуск

## Режимы работы

### 1. Демон — слежка за папкой

Следит за папкой, новые видео обрабатываются автоматически.

```bash
python -m video_transcriber.main
```

### 2. Process Watcher — автозапись при запуске программы

Когда программа (например Zoom) запускается — автоматически начинается запись экрана. Когда закрывается — запись останавливается и запускается транскрипция.

В `config.yaml`:
```yaml
process_watcher:
  program_names: ["Zoom.exe", "obs64.exe"]
  poll_interval: 5
```

Или через CLI:
```bash
python -m video_transcriber.main --watch-process "Zoom.exe"
```

### 3. Ручная запись экрана

Начать запись → Ctrl+C → стоп → транскрипция:

```bash
python -m video_transcriber.main --record
```

### 4. Один файл

```bash
python -m video_transcriber.main --file "video.mp4"
```

## CLI

```bash
python -m video_transcriber.main                    # демон (папка + process watcher)
python -m video_transcriber.main --file "vid.mp4"   # один файл
python -m video_transcriber.main --record           # ручная запись экрана
python -m video_transcriber.main --watch-process "Zoom.exe"  # автозапись при запуске
python -m video_transcriber.main --setup            # перенастроить
python -m video_transcriber.main --check-hardware   # проверить железо
python -m video_transcriber.main --install-autostart    # автозапуск
python -m video_transcriber.main --uninstall-autostart  # убрать автозапуск
python -m video_transcriber.main --config my.yaml   # свой конфиг
python -m video_transcriber.main --verbose          # debug лог
```

## Конфигурация

`config.yaml` (создается визардом или из `config.example.yaml`):

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
  device: "auto"             # auto/cpu/cuda
  compute_type: "int8"
  language: "ru"             # или "auto"
  output_format: "txt"       # txt/srt/vtt

telegram:
  bot_token: ""              # от @BotFather (или .env)
  chat_id: ""                # (или .env)

recorder:
  fps: 30
  # video_size: "1920x1080"  # только для Linux

process_watcher:
  program_names: ["Zoom.exe"]  # имена процессов для отслеживания
  poll_interval: 5             # секунд между проверками
```

## Как работает Process Watcher

```
Zoom.exe запустился
  → psutil ловит процесс
  → FFmpeg начинает запись экрана (gdigrab/avfoundation/x11grab)
Zoom.exe закрылся
  → FFmpeg останавливается (отправляется 'q')
  → Видео сохраняется в ~/Videos/Processed/
  → Запускается пайплайн: MP3 → транскрибация → Telegram уведомление
```

Можно мониторить несколько программ: `"Zoom.exe, Teams.exe, chrome.exe"`

## Запись экрана — платформы

| ОС | Метод FFmpeg | Примечание |
|----|-------------|------------|
| Windows | `-f gdigrab -i desktop` | Работает из коробки |
| macOS | `-f avfoundation -i 1` | Может потребоваться разрешение Screen Recording |
| Linux | `-f x11grab -i :0.0` | Требует X11 (Wayland: использовать pipewire) |

## Модели Whisper (бесплатные, MIT)

| Размер | RAM/VRAM | Скорость | Качество | Автовыбор при |
|--------|----------|----------|----------|---------------|
| tiny   | ~1 GB    | fastest  | basic    | < 4GB RAM |
| base   | ~1 GB    | fast     | good     | 4-8GB RAM |
| small  | ~2 GB    | moderate | great    | 8-16GB RAM |
| medium | ~5 GB    | slow     | excellent| 16GB+ RAM или 5GB+ VRAM |
| large-v2| ~10 GB  | v.slow   | best     | 10GB+ VRAM |

## Автозапуск

| ОС | Метод |
|----|-------|
| Windows | Task Scheduler |
| macOS | LaunchAgent |
| Linux | systemd user service |

## Архитектура

```
src/video_transcriber/
├── hardware.py          # детект CPU/RAM/GPU
├── setup_wizard.py      # визард первого запуска
├── autostart.py         # автозапуск (win/mac/linux)
├── process_watcher.py   # слежка за процессами (psutil)
├── screen_recorder.py   # запись экрана (FFmpeg)
├── config.py            # конфиг (YAML + .env)
├── watcher.py           # слежка за папкой (watchdog)
├── extractor.py         # FFmpeg → MP3
├── transcriber.py       # faster-whisper
├── notifier.py          # Telegram
├── pipeline.py          # оркестрация
└── main.py              # CLI
```

## Лицензия

MIT
