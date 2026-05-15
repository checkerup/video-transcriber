# Video Transcriber

Автоматическая расшифровка видео: следит за папкой или запуском программ, записывает экран, транскрибирует локально (бесплатно!), шлет уведомление в Telegram.

**Whisper — полностью бесплатная модель (MIT лицензия).** Всё работает локально, ничего не уходит в облако.

## Возможности

- **Автозапись экрана** — при запуске программы (Zoom, OBS и т.д.) автоматически начинается запись экрана, при закрытии — стоп + транскрипция
- **Автодетект железа** — скрипт проверяет CPU/RAM/GPU и подбирает оптимальную модель
- **First-run визард** — при первом запуске интерактивная настройка (6 шагов)
- **Слежка за папкой** — watchdog автоматически ловит новые видеофайлы
- **Экстракция аудио** — FFmpeg вытягивает MP3 без перекодирования
- **Транскрибация** — faster-whisper (локально, бесплатно, приватно) с таймкодами
- **Уведомления** — Telegram-бот сообщает когда готово
- **Автозапуск** — установка в автозапуск одной командой (Windows/macOS/Linux)
- **Интерактивное меню** — `menu.bat` / `menu.sh` со всеми режимами
- **Кроссплатформенный** — Windows, macOS, Linux

## Быстрый старт

### Windows

```bat
git clone https://github.com/YOU/video-transcriber.git
cd video-transcriber
install.bat
menu.bat
```

### macOS / Linux

```bash
git clone https://github.com/YOU/video-transcriber.git
cd video-transcriber
chmod +x install.sh menu.sh start.sh stop.sh
./install.sh
./menu.sh
```

При **первом запуске** автоматически запустится визард:
1. Проверка железа → рекомендация модели
2. Настройка путей (watch folder, output folder)
3. Выбор языка и формата транскрипта (txt/srt/vtt)
4. Настройка Telegram (bot token + chat ID)
5. Настройка Process Watcher (автозапись при запуске программы)
6. Предложение установить в автозапуск

## Интерактивное меню

Запустите `menu.bat` (Windows) или `./menu.sh` (macOS/Linux):

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

## Режимы работы

### 1. Демон — слежка за папкой

Следит за папкой, новые видео обрабатываются автоматически. Если в конфиге указаны `program_names`, параллельно работает Process Watcher.

```bash
python -m video_transcriber.main
```

### 2. Process Watcher — автозапись при запуске программы

Когда программа (например Zoom) запустилась — автоматически начинается запись экрана. Когда закрылась — запись останавливается и запускается транскрипция.

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

Можно мониторить несколько программ через запятую:
```bash
python -m video_transcriber.main --watch-process "Zoom.exe,Teams.exe"
```

### 3. Ручная запись экрана

Начать запись → Ctrl+C → стоп → транскрипция:

```bash
python -m video_transcriber.main --record
```

### 4. Один файл

Обработать конкретное видео без демона:

```bash
python -m video_transcriber.main --file "video.mp4"
```

## Полный пайплайн

```
Видео появилось в папке (или запись экрана завершена)
  → FFmpeg извлекает аудиодорожку в MP3
  → faster-whisper транскрибирует (с таймкодами)
  → Текст сохраняется (txt/srt/vtt)
  → Telegram-бот отправляет уведомление с путями к файлам
```

## CLI (все флаги)

```bash
python -m video_transcriber.main                        # демон (папка + process watcher)
python -m video_transcriber.main --file "vid.mp4"       # один файл
python -m video_transcriber.main --record               # ручная запись экрана
python -m video_transcriber.main --watch-process "Zoom" # автозапись при запуске программы
python -m video_transcriber.main --setup                 # перенастроить (визард)
python -m video_transcriber.main --check-hardware       # проверить железо
python -m video_transcriber.main --install-autostart    # установить автозапуск
python -m video_transcriber.main --uninstall-autostart  # убрать автозапуск
python -m video_transcriber.main --config my.yaml       # использовать свой конфиг
python -m video_transcriber.main --verbose              # debug логирование
```

## Конфигурация

`config.yaml` (создается визардом автоматически, или вручную из `config.example.yaml`):

```yaml
watch:
  folder: "~/Videos/Incoming"       # папка для слежки
  extensions: [.mp4, .mkv, .avi, .mov, .webm]
  delay_seconds: 10                 # ожидание до обработки (файл должен дозаписаться)

processing:
  output_folder: "~/Videos/Processed"  # куда сохранять результаты
  audio_format: "mp3"
  audio_bitrate: "192k"
  keep_audio: true                  # сохранять MP3 после транскрибации

transcription:
  model_size: "base"               # tiny/base/small/medium/large-v2
  device: "auto"                    # auto/cpu/cuda (auto = определит GPU)
  compute_type: "int8"             # int8/int8_float16/float16
  language: "ru"                    # язык или "auto" для автоопределения
  output_format: "txt"             # txt/srt/vtt
  word_timestamps: true             # таймкоды для каждого слова

telegram:
  bot_token: ""                    # от @BotFather (или в .env)
  chat_id: ""                      # ваш chat ID (или в .env)

recorder:
  fps: 30                          # FPS записи экрана
  # video_size: "1920x1080"        # разрешение (только для Linux/x11grab)

process_watcher:
  program_names: ["Zoom.exe"]       # имена процессов для отслеживания
  poll_interval: 5                  # секунд между проверками
```

Секреты через `.env` (альтернатива config.yaml):
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

## Как работает Process Watcher

```
Zoom.exe запустился
  → psutil обнаруживает процесс (каждые 5 сек)
  → FFmpeg начинает запись экрана (gdigrab/avfoundation/x11grab)
Zoom.exe закрылся
  → FFmpeg останавливается (отправляется сигнал 'q')
  → Видео сохраняется в ~/Videos/Processed/screen_2025-01-15_14-30-00.mp4
  → Запускается пайплайн: MP3 → транскрибация → Telegram уведомление
```

## Запись экрана — платформы

| ОС | Метод FFmpeg | Примечание |
|----|-------------|------------|
| Windows | `-f gdigrab -i desktop` | Работает из коробки |
| macOS | `-f avfoundation -i 1` | Требуется разрешение: Системные настройки → Конфиденциальность → Запись экрана |
| Linux | `-f x11grab -i :0.0` | Требует X11. На Wayland: использовать pipewire или переключиться на X11 |

## Модели Whisper (бесплатные, MIT лицензия)

Модель скачивается **один раз** автоматически при первом запуске. Все модели OpenAI Whisper — открытые (MIT), бесплатны навсегда.

| Размер | RAM/VRAM | Скорость | Качество | Автовыбор при |
|--------|----------|----------|----------|---------------|
| tiny   | ~1 GB    | fastest  | basic    | < 4GB RAM, нет GPU |
| base   | ~1 GB    | fast     | good     | 4-8GB RAM или 1.5GB VRAM |
| small  | ~2 GB    | moderate | great    | 8-16GB RAM или 2.5GB VRAM |
| medium | ~5 GB    | slow     | excellent| 16GB+ RAM или 5GB+ VRAM |
| large-v2| ~10 GB  | v.slow   | best     | 10GB+ VRAM |

## Автозапуск (OS-специфичный)

| ОС | Метод | Расположение |
|----|-------|-------------|
| Windows | Task Scheduler | `schtasks /Create /SC ONLOGON` |
| macOS | LaunchAgent | `~/Library/LaunchAgents/com.video-transcriber.plist` |
| Linux | systemd user service | `~/.config/systemd/user/video-transcriber.service` |

## CUDA (GPU ускорение)

Скрипт автоматически обнаружит NVIDIA GPU через `torch.cuda` или `nvidia-smi`. Если CUDA доступна — транскрибация пойдёт на GPU (в 3-10 раз быстрее CPU).

Ручная установка CUDA-зависимостей:
```bash
pip install video-transcriber[cuda]
```

В конфиге: `device: "cuda"` (или `"auto"` — определит автоматически).

## Требования

- **Python 3.10+**
- **FFmpeg** — автоматически установится через `install.bat` (winget) или `install.sh` (brew/apt)
- **NVIDIA GPU** (опционально) — для GPU-ускорения

## Структура проекта

```
video-transcriber/
├── src/video_transcriber/
│   ├── hardware.py          # детект CPU/RAM/GPU, рекомендация модели
│   ├── setup_wizard.py      # интерактивный визард первого запуска
│   ├── autostart.py         # автозапуск (Windows/macOS/Linux)
│   ├── process_watcher.py   # слежка за процессами (psutil)
│   ├── screen_recorder.py   # запись экрана (FFmpeg)
│   ├── config.py            # загрузка конфига (YAML + .env)
│   ├── watcher.py           # слежка за папкой (watchdog)
│   ├── extractor.py         # FFmpeg → MP3
│   ├── transcriber.py       # faster-whisper транскрибация
│   ├── notifier.py          # Telegram уведомления
│   ├── pipeline.py          # оркестрация пайплайна
│   └── main.py              # CLI входная точта
├── menu.bat / menu.sh       # интерактивное меню
├── install.bat / install.sh # авто-установка
├── start.bat / start.sh     # быстрый запуск
├── stop.bat / stop.sh       # остановка
├── config.example.yaml      # пример конфига
├── .env.example             # пример секретов
├── pyproject.toml           # Python-пакет
├── requirements.txt         # зависимости
└── LICENSE                  # MIT
```

## Лицензия

MIT
