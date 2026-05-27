# 🚀 Quickstart Scripts / Скрипты быстрого запуска

This directory contains standalone helper scripts to execute specific features of **Video Transcriber** directly, bypassing the main menu console.

Эта папка содержит отдельные скрипты быстрого запуска для вызова конкретных функций **Video Transcriber** напрямую, без необходимости заходить в главное текстовое меню.

---

## 📋 Available Scripts / Доступные скрипты

### 🛠️ Setup & Installation / Установка и настройка
* **`setup.bat`** / **`setup.sh`**
  * Standard environment installation and repair.
  * Стандартная установка зависимостей и настройка виртуального окружения.
* **`setup_diarization.bat`** / **`setup_diarization.sh`**
  * Installs the extra dependencies required for Speaker Diarization (`pyannote.audio`).
  * Устанавливает дополнительные библиотеки для разделения на спикеров (`pyannote.audio`).

---

### 🎙️ Processing Files / Обработка файлов
* **`transcribe_file.bat`** / **`transcribe_file.sh`**
  * Transcribes a single audio or video file.
  * **Windows Tip:** You can drag and drop your file directly onto `transcribe_file.bat` to launch transcription immediately!
  * Транскрибирует один аудио- или видеофайл.
  * **Совет для Windows:** Вы можете просто перетащить файл (drag-and-drop) мышкой прямо на `transcribe_file.bat`, чтобы мгновенно запустить обработку!
* **`convert_to_mp3.bat`** / **`convert_to_mp3.sh`**
  * Quickly extracts audio tracks from video files and saves them as MP3. Supports drag-and-drop for multiple files.
  * Быстро извлекает аудиодорожки из видеофайлов и сохраняет их в формате MP3. Поддерживает перетаскивание нескольких файлов сразу.

---

### 🔍 Daemon & Recording / Фоновый мониторинг и запись
* **`start_daemon.bat`** / **`start_daemon.sh`**
  * Starts the automatic background folder watcher (detects new files and transcribes them sequentially).
  * Запускает фоновый демон (отслеживает новые файлы в папке импорта и обрабатывает их последовательно).
* **`record_screen.bat`** / **`record_screen.sh`**
  * Launches manual screen recording. Stop recording by pressing `Ctrl+C`.
  * Запускает запись экрана вручную. Для остановки нажмите `Ctrl+C`.
* **`watch_process.bat`** / **`watch_process.sh`**
  * Monitors processes (like `Zoom.exe` or `Teams.exe`) and automatically starts recording them on launch.
  * Отслеживает запуск программы (например, `Zoom.exe` или `Telegram.exe`) и автоматически записывает экран при ее активности.

---

### ⚙️ Utilities & Diagnostics / Утилиты и диагностика
* **`check_hardware.bat`** / **`check_hardware.sh`**
  * Verifies system CPU, RAM, and GPU (CUDA) details for Whisper model loading.
  * Проверяет характеристики системы (процессор, ОЗУ, видеокарту) для оптимальной загрузки моделей Whisper.
* **`run_wizard.bat`** / **`run_wizard.sh`**
  * Opens the interactive setup wizard to configure folder paths, translation options, and Telegram alerts.
  * Запускает интерактивный мастер настройки для папок, перевода и уведомлений в Telegram.

---

## 👥 Speaker Diarization Setup / Настройка разделения на спикеров

To run transcription with speaker roles (`SPEAKER_00: Hello`, `SPEAKER_01: Hi`), configure the Hugging Face API:

Для того чтобы транскрибировать текст с разделением по ролям (`SPEAKER_00: Привет`, `SPEAKER_01: Как дела?`), выполните следующие шаги:

1. Run **`setup_diarization.bat`** (or `.sh` on Linux/macOS) to install the necessary libraries.
2. Sign up on [Hugging Face](https://huggingface.co/).
3. Accept the user terms for these models (under your HF account):
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
4. Generate a Read token in Hugging Face settings under **Access Tokens**.
5. Set `enabled: true` and paste your token under `auth_token` in `config.yaml`:
   ```yaml
   diarization:
     enabled: true
     auth_token: "hf_your_token_here"
   ```

1. Запустите **`setup_diarization.bat`** (или `.sh` на Linux/macOS) для установки необходимых библиотек.
2. Зарегистрируйтесь на сайте [Hugging Face](https://huggingface.co/).
3. Подтвердите лицензионное соглашение для моделей (под своей учетной записью HF):
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
4. Сгенерируйте API-токен с правами Read в настройках Hugging Face (раздел **Access Tokens**).
5. Включите функцию и укажите токен в файле `config.yaml`:
   ```yaml
   diarization:
     enabled: true
     auth_token: "hf_your_token_here"
   ```
