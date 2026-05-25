# Улучшения Video Transcriber: План Реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить автоматическую установку, конвертацию в MP3, автоопределение аудио/видео файлов, удаление тишины, автоперевод, ИИ-суммаризацию через Gemini API, последовательную очередь и исправить критические баги с помощью TDD-подхода.

**Architecture:** Пайплайн обработки расширяется для поддержки как видео, так и аудио файлов. Конфигурация дополняется новыми параметрами с возможностью переопределения через CLI. Сетевые запросы к Gemini и Google Translate выносятся в отдельные изолированные функции. Очередь watcher преобразуется в пул с последовательным консьюмером.

**Tech Stack:** Python 3.10+, faster-whisper, requests, pytest, FFmpeg, winget (на Windows)

---

### Task 1: Исправление багов в config.py (Загрузка .env и раскрытие ~)

**Files:**
- Modify: `src/video_transcriber/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Написать падающий тест**
  Создать файл `tests/test_config.py` и протестировать раскрытие домашней папки `~` и загрузку конфигурации при измененной рабочей директории.
  ```python
  import os
  from pathlib import Path
  from video_transcriber.config import load_config

  def test_expand_user_paths(tmp_path):
      # Создаем тестовый config.yaml с путями, содержащими ~
      config_content = """
      watch:
        folder: "~/IncomingTestDir"
      processing:
        output_folder: "~/ProcessedTestDir"
      """
      cfg_file = tmp_path / "config.yaml"
      cfg_file.write_text(config_content)
      
      cfg = load_config(cfg_file)
      
      # Проверяем, что пути раскрылись и больше не содержат символ ~
      assert "~" not in cfg.watch.folder
      assert "~" not in cfg.processing.output_folder
      assert Path(cfg.watch.folder).is_absolute()
  ```

- [ ] **Step 2: Запустить тест для верификации падения**
  Запуск: `pytest tests/test_config.py -v`
  Ожидается: FAIL (ошибка импорта или падение ассерта из-за присутствия `~` в путях)

- [ ] **Step 3: Написать минимальную реализацию**
  Внести изменения в `src/video_transcriber/config.py` для раскрытия путей:
  ```python
  # Добавить импорт os и изменить загрузку путей:
  watch_folder = os.path.expanduser(watch_raw.get("folder", WatchConfig.folder))
  output_folder = os.path.expanduser(proc_raw.get("output_folder", ProcessingConfig.output_folder))
  
  # А также исправить load_dotenv:
  project_root = Path(__file__).resolve().parent.parent.parent
  load_dotenv(project_root / ".env")
  ```

- [ ] **Step 4: Запустить тест для верификации прохождения**
  Запуск: `pytest tests/test_config.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/config.py tests/test_config.py
  git commit -m "fix: load .env via absolute path and expand user folder paths"
  ```

---

### Task 2: Экранирование HTML для уведомлений в Telegram

**Files:**
- Modify: `src/video_transcriber/notifier.py`
- Test: `tests/test_notifier.py`

- [ ] **Step 1: Написать падающий тест**
  Создать `tests/test_notifier.py` и проверить генерацию безопасного HTML-текста с использованием спецсимволов (`_`, `<`, `>`).
  ```python
  import html
  from video_transcriber.config import AppConfig, TelegramConfig
  from video_transcriber.notifier import send_notification
  from unittest.mock import patch

  @patch("requests.post")
  def test_html_notification_escaping(mock_post):
      config = AppConfig(telegram=TelegramConfig(bot_token="123", chat_id="456"))
      mock_post.return_value.status_code = 200
      
      # Путь содержит нижние подчеркивания и угловые скобки
      video_path = "C:/my_videos/file_<1>_test.mp4"
      
      send_notification(config, video_path, None, None, error="Error occurred <failed>")
      
      # Проверяем, что отправленный текст отформатирован в HTML и экранирован
      args, kwargs = mock_post.call_args
      payload = kwargs["json"]
      assert payload["parse_mode"] == "HTML"
      assert "file_&lt;1&gt;_test.mp4" in payload["text"]
      assert "Error occurred &lt;failed&gt;" in payload["text"]
  ```

- [ ] **Step 2: Запустить тест для проверки падения**
  Запуск: `pytest tests/test_notifier.py -v`
  Ожидается: FAIL (так как сейчас используется Markdown и нет экранирования)

- [ ] **Step 3: Написать минимальную реализацию**
  Модифицировать `src/video_transcriber/notifier.py` для перехода на HTML-разметку и использования `html.escape()`:
  ```python
  import html

  # В функции send_notification:
  if error:
      text = (
          f"❌ <b>Ошибка при обработке видео</b>\n\n"
          f"📁 <b>Файл:</b> <code>{html.escape(video_path)}</code>\n"
          f"⚠️ <b>Ошибка:</b> {html.escape(error)}"
      )
  else:
      lines = ["✅ <b>Расшифровка готова!</b>\n"]
      lines.append(f"📁 <b>Видео:</b> <code>{html.escape(video_path)}</code>")
      if audio_path:
          lines.append(f"🎵 <b>Аудио:</b> <code>{html.escape(audio_path)}</code>")
      if transcript_path:
          lines.append(f"📝 <b>Текст:</b> <code>{html.escape(transcript_path)}</code>")
      text = "\n".join(lines)

  payload = {
      "chat_id": config.telegram.chat_id,
      "text": text,
      "parse_mode": "HTML",
  }
  ```

- [ ] **Step 4: Запустить тест**
  Запуск: `pytest tests/test_notifier.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/notifier.py tests/test_notifier.py
  git commit -m "fix: use HTML parse mode in Telegram and escape special characters"
  ```

---

### Task 3: Последовательная очередь обработки (Queue Worker)

**Files:**
- Modify: `src/video_transcriber/watcher.py`
- Test: `tests/test_watcher.py`

- [ ] **Step 1: Написать падающий тест**
  Проверить, что watcher при обнаружении нескольких стабильных файлов не запускает обработку одновременно, а передает их в очередь.
  ```python
  import time
  import threading
  from video_transcriber.config import AppConfig
  from video_transcriber.watcher import VideoFileHandler

  def test_sequential_processing_queue():
      processed_files = []
      lock = threading.Lock()
      
      def mock_callback(file_path):
          time.sleep(0.1) # Симулируем обработку
          with lock:
              processed_files.append(file_path)

      queue = []
      config = AppConfig()
      handler = VideoFileHandler(config, mock_callback, queue, lock)
      
      # Симулируем обработку нескольких файлов
      handler._process_after_delay("file1.mp4")
      handler._process_after_delay("file2.mp4")
      
      # Ожидается, что они добавлены в очередь
      assert "file1.mp4" in queue
      assert "file2.mp4" in queue
  ```

- [ ] **Step 2: Запустить тест**
  Запуск: `pytest tests/test_watcher.py -v`
  Ожидается: FAIL (так как сейчас обработка запускается сразу в новом потоке через `threading.Thread`)

- [ ] **Step 3: Написать минимальную реализацию**
  Переделать запуск обработки в `watcher.py`. Вместо непосредственного запуска потока в `_process_after_delay`, мы просто помещаем файл в `queue`. 
  Удалить `threading.Thread(target=self.callback, ...).start()` из `watcher.py`.
  Запуск воркера вынести в `run_daemon` в `src/video_transcriber/main.py`:
  ```python
  # В main.py:
  def queue_worker(queue, lock, config, callback):
      while not shutdown_event.is_set():
          file_path = None
          with lock:
              if queue:
                  file_path = queue[0]
          if file_path:
              try:
                  callback(file_path, config)
              except Exception:
                  logger.exception("Error in queue worker")
              finally:
                  with lock:
                      if file_path in queue:
                          queue.remove(file_path)
          time.sleep(1)
  ```

- [ ] **Step 4: Проверить тесты**
  Запуск: `pytest tests/test_watcher.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/watcher.py src/video_transcriber/main.py tests/test_watcher.py
  git commit -m "feat: implement sequential queue worker instead of parallel threads"
  ```

---

### Task 4: Конвертация видео в MP3 и удаление тишины

**Files:**
- Modify: `src/video_transcriber/extractor.py`
- Test: `tests/test_extractor.py`

- [ ] **Step 1: Написать падающий тест**
  Создать `tests/test_extractor.py` для тестирования `convert_video_to_mp3` и проверки интеграции аудиофильтра тишины.
  ```python
  from video_transcriber.config import AppConfig, ProcessingConfig
  from video_transcriber.extractor import convert_video_to_mp3
  from unittest.mock import patch, MagicMock

  @patch("subprocess.run")
  def test_convert_to_mp3_with_silence_removal(mock_run):
      mock_run.return_value.returncode = 0
      config = AppConfig(processing=ProcessingConfig(silence_removal=True))
      
      # Вызываем конвертацию
      with patch("pathlib.Path.exists", return_value=True):
          with patch("pathlib.Path.stat") as mock_stat:
              mock_stat.return_value.st_size = 1024
              convert_video_to_mp3("input.mp4", config)
              
      # Проверяем, что в аргументах ffmpeg есть фильтр тишины
      args, kwargs = mock_run.call_args
      cmd = args[0]
      assert "-af" in cmd
      assert "silenceremove" in cmd
  ```

- [ ] **Step 2: Запустить тест**
  Запуск: `pytest tests/test_extractor.py -v`
  Ожидается: FAIL (так как функция `convert_video_to_mp3` и параметр `silence_removal` не определены)

- [ ] **Step 3: Написать минимальную реализацию**
  Добавить `silence_removal` в класс `ProcessingConfig` в `src/video_transcriber/config.py`.
  В `src/video_transcriber/extractor.py` реализовать:
  ```python
  def convert_video_to_mp3(video_path: str, config: AppConfig) -> str:
      video = Path(video_path)
      output_dir = Path(config.processing.output_folder)
      output_dir.mkdir(parents=True, exist_ok=True)
      audio_path = output_dir / f"{video.stem}.mp3"
      ffmpeg_path = check_ffmpeg()
      
      cmd = [
          ffmpeg_path,
          "-i", str(video),
          "-vn",
          "-acodec", "libmp3lame",
          "-ab", config.processing.audio_bitrate,
      ]
      
      if getattr(config.processing, "silence_removal", False):
          cmd.extend(["-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"])
          
      cmd.extend(["-y", str(audio_path)])
      
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
      if result.returncode != 0:
          raise RuntimeError(f"FFmpeg failed: {result.stderr}")
      return str(audio_path)
  ```
  Также добавить применение фильтра `silenceremove` в базовую функцию `extract_audio` при установленном `config.processing.silence_removal = True`.

- [ ] **Step 4: Проверить тесты**
  Запуск: `pytest tests/test_extractor.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/extractor.py src/video_transcriber/config.py tests/test_extractor.py
  git commit -m "feat: add convert_video_to_mp3 and silence removal filter support"
  ```

---

### Task 5: Модуль автоперевода и форматирования абзацев

**Files:**
- Modify: `src/video_transcriber/transcriber.py`
- Test: `tests/test_transcriber.py`

- [ ] **Step 1: Написать падающий тест**
  Написать тесты для проверки функции перевода сегментов и форматирования сплошного текста (clean paragraphs).
  ```python
  from video_transcriber.transcriber import _format_paragraphs
  from unittest.mock import MagicMock

  def test_format_paragraphs():
      seg1 = MagicMock(text="Привет. ")
      seg2 = MagicMock(text="Как дела? ")
      seg3 = MagicMock(text="Я записываю видео.")
      
      result = _format_paragraphs([seg1, seg2, seg3])
      assert result == "Привет.\n\nКак дела?\n\nЯ записываю видео."
  ```

- [ ] **Step 2: Запустить тест**
  Запуск: `pytest tests/test_transcriber.py -v`
  Ожидается: FAIL (нет `_format_paragraphs`)

- [ ] **Step 3: Написать минимальную реализацию**
  Добавить `translate_to` и `clean_paragraphs` в `config.py`.
  В `src/video_transcriber/transcriber.py` добавить:
  ```python
  import urllib.parse
  import requests

  def google_translate(text: str, target_lang: str) -> str:
      url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
      resp = requests.get(url, timeout=10)
      resp.raise_for_status()
      parts = resp.json()[0]
      return "".join([part[0] for part in parts if part[0]])

  def _format_paragraphs(segments) -> str:
      text_blocks = []
      current_block = []
      for seg in segments:
          text = seg.text.strip()
          current_block.append(text)
          if text and text[-1] in (".", "?", "!"):
              text_blocks.append(" ".join(current_block))
              current_block = []
      if current_block:
          text_blocks.append(" ".join(current_block))
      return "\n\n".join(text_blocks)
  ```
  Внедрить вызов перевода и форматирования абзацев в `transcribe`:
  ```python
  # В transcribe():
  segment_list = list(segments)
  
  if config.transcription.translate_to and config.transcription.translate_to.lower() != "none":
      target = config.transcription.translate_to
      if info.language != target:
          logger.info("Translating transcript from %s to %s...", info.language, target)
          for seg in segment_list:
              try:
                  seg.text = google_translate(seg.text, target)
              except Exception as e:
                  logger.warning("Failed to translate segment: %s", e)

  if getattr(config.transcription, "clean_paragraphs", False):
      text = _format_paragraphs(segment_list)
  else:
      formatter = formatters.get(fmt, _format_txt)
      text = formatter(segment_list)
  ```

- [ ] **Step 4: Проверить тесты**
  Запуск: `pytest tests/test_transcriber.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/transcriber.py tests/test_transcriber.py
  git commit -m "feat: add Google Translate integration and clean paragraphs formatting"
  ```

---

### Task 6: Модуль суммаризации ИИ (Gemini API)

**Files:**
- Create: `src/video_transcriber/summarizer.py`
- Test: `tests/test_summarizer.py`

- [ ] **Step 1: Написать падающий тест**
  Создать тест, проверяющий HTTP запрос к Gemini API и сохранение Markdown-файла резюме.
  ```python
  from video_transcriber.config import AppConfig, TelegramConfig
  from video_transcriber.summarizer import generate_summary
  from unittest.mock import patch

  @patch("requests.post")
  def test_generate_summary_gemini(mock_post):
      mock_post.return_value.status_code = 200
      mock_post.return_value.json.return_value = {
          "candidates": [{"content": {"parts": [{"text": "Это краткое содержание."}]}}]
      }
      
      class SummarizationConfig:
          enabled = True
          provider = "gemini"
          api_key = "test_key"
          
      config = AppConfig()
      config.summarization = SummarizationConfig()
      
      summary = generate_summary("Длинный текст расшифровки встреч...", config)
      assert summary == "Это краткое содержание."
  ```

- [ ] **Step 2: Запустить тест**
  Запуск: `pytest tests/test_summarizer.py -v`
  Ожидается: FAIL (так как файла `summarizer.py` нет)

- [ ] **Step 3: Написать минимальную реализацию**
  Создать `src/video_transcriber/summarizer.py`:
  ```python
  import os
  import requests
  import logging
  from .config import AppConfig

  logger = logging.getLogger(__name__)

  def generate_summary(text: str, config: AppConfig) -> str:
      sum_cfg = getattr(config, "summarization", None)
      if not sum_cfg or not sum_cfg.enabled:
          return ""
          
      api_key = sum_cfg.api_key or os.getenv("GEMINI_API_KEY")
      if not api_key:
          logger.warning("Gemini API key is not configured. Skipping summarization.")
          return ""
          
      url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
      prompt = (
          "Сделай краткое изложение (summary) следующего текста расшифровки видео на русском языке. "
          "Выдели ключевые темы, инсайты и выводы, а также составь оглавление/таймкоды, если это уместно.\n\n"
          f"Текст расшифровки:\n{text}"
      )
      
      payload = {
          "contents": [{
              "parts": [{"text": prompt}]
          }]
      }
      
      try:
          resp = requests.post(url, json=payload, timeout=45)
          resp.raise_for_status()
          result = resp.json()
          summary_text = result['candidates'][0]['content']['parts'][0]['text']
          return summary_text
      except Exception as e:
          logger.error("Gemini summarization failed: %s", e)
          return ""
  ```
  Не забыть добавить новые поля для суммаризации в класс `AppConfig` и `load_config` в `src/video_transcriber/config.py`.

- [ ] **Step 4: Проверить тесты**
  Запуск: `pytest tests/test_summarizer.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/summarizer.py src/video_transcriber/config.py tests/test_summarizer.py
  git commit -m "feat: implement AI summarization using Gemini API"
  ```

---

### Task 7: Обновление пайплайна (процессинг файлов, автоопределение аудио/видео)

**Files:**
- Modify: `src/video_transcriber/pipeline.py`
- Modify: `src/video_transcriber/main.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Написать падающий тест**
  Написать тесты для проверки автоопределения аудио/видео и вызова суммаризации внутри пайплайна.
  ```python
  from video_transcriber.config import AppConfig
  from video_transcriber.pipeline import process_file
  from unittest.mock import patch, MagicMock

  @patch("video_transcriber.pipeline.transcribe")
  @patch("video_transcriber.pipeline.extract_audio")
  @patch("video_transcriber.pipeline.copy_video_to_output")
  @patch("video_transcriber.pipeline.send_notification")
  def test_pipeline_audio_file(mock_notify, mock_copy_vid, mock_extract, mock_transcribe):
      config = AppConfig()
      
      # Запуск пайплайна для аудиофайла
      with patch("pathlib.Path.exists", return_value=True):
          with patch("shutil.copy2") as mock_copy:
              process_file("audio.mp3", config)
              
      # Проверяем, что извлечение аудио (extract_audio) пропущено
      mock_extract.assert_not_called()
      # Проверяем, что транскрибация вызвана
      mock_transcribe.assert_called_once()
  ```

- [ ] **Step 2: Запустить тест**
  Запуск: `pytest tests/test_pipeline.py -v`
  Ожидается: FAIL (так как функция `process_file` отсутствует)

- [ ] **Step 3: Написать минимальную реализацию**
  Переименовать `process_video` в `process_file` в `pipeline.py` и реализовать логику автоопределения:
  ```python
  # Добавить импорт copy_audio_to_output и generate_summary
  from .summarizer import generate_summary
  
  def process_file(file_path: str, config: AppConfig) -> dict:
      suffix = Path(file_path).suffix.lower()
      is_audio = suffix in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"]
      is_video = suffix in [".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"]
      
      if not is_audio and not is_video:
          raise ValueError(f"Unsupported file format: {suffix}")
          
      result = {"video": None, "audio": None, "transcript": None, "summary": None, "error": None}
      
      try:
          if is_video:
              output_video = copy_video_to_output(file_path, config)
              result["video"] = output_video
              audio_path = extract_audio(output_video, config)
              result["audio"] = audio_path
          else:
              # Для аудиофайлов копируем его как аудиоисточник
              output_audio = copy_audio_to_output(file_path, config)
              result["audio"] = output_audio
              
          transcript_path = transcribe(result["audio"], config)
          result["transcript"] = transcript_path
          
          # Запуск суммаризации при наличии конфигурации
          sum_cfg = getattr(config, "summarization", None)
          if sum_cfg and sum_cfg.enabled:
              with open(transcript_path, "r", encoding="utf-8") as f:
                  text = f.read()
              summary_text = generate_summary(text, config)
              if summary_text:
                  summary_path = Path(transcript_path).parent / f"{Path(file_path).stem}_summary.md"
                  summary_path.write_text(summary_text, encoding="utf-8")
                  result["summary"] = str(summary_path)
                  
      except Exception as e:
          result["error"] = str(e)
          
      # Отправка уведомлений в Telegram
      send_notification(
          config=config,
          video_path=result["video"],
          audio_path=result["audio"],
          transcript_path=result["transcript"],
          summary_path=result.get("summary"),
          error=result["error"]
      )
      return result
  ```
  Внедрить в `main.py` новые CLI параметры и переопределение полей `AppConfig`, а также обновить вызов `process_file`.

- [ ] **Step 4: Проверить тесты**
  Запуск: `pytest tests/test_pipeline.py -v`
  Ожидается: PASS

- [ ] **Step 5: Сделать коммит**
  ```bash
  git add src/video_transcriber/pipeline.py src/video_transcriber/main.py tests/test_pipeline.py
  git commit -m "feat: complete pipeline update with auto-format detection and summarization integration"
  ```

---

### Task 8: Автоматическая установка зависимостей в Windows-батниках

**Files:**
- Modify: `install.bat`
- Modify: `menu.bat`
- Modify: `start.bat`

- [ ] **Step 1: Обновить install.bat**
  Внедрить в `install.bat` автоматический поиск Python в системных папках, установку через `winget` при его отсутствии, локальное обновление `PATH`, установку FFmpeg через `winget` при его отсутствии, детекцию CUDA и автоматический выбор `pip install -e .[cuda]`.
  ```batch
  :: Проверка рабочего Python
  python -c "import sys" >nul 2>&1
  if %ERRORLEVEL% neq 0 (
      echo Python not found. Scanning local paths...
      for /d %%d in ("%LocalAppData%\Programs\Python\Python3*") do (
          if exist "%%d\python.exe" (
              set "PATH=%PATH%;%%d;%%d\Scripts"
              goto :python_ready
          )
      )
      for /d %%d in ("%ProgramFiles%\Python3*") do (
          if exist "%%d\python.exe" (
              set "PATH=%PATH%;%%d;%%d\Scripts"
              goto :python_ready
          )
      )
      
      echo Installing Python via winget...
      winget install --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements --silent
      if %ERRORLEVEL% neq 0 (
          echo [ERROR] Failed to install Python. Please install it manually.
          pause
          exit /b 1
      )
      
      :: Снова ищем свежеустановленный Python
      for /d %%d in ("%LocalAppData%\Programs\Python\Python3*") do (
          if exist "%%d\python.exe" (
              set "PATH=%PATH%;%%d;%%d\Scripts"
              goto :python_ready
          )
      )
  )
  :python_ready
  
  :: Проверка FFmpeg
  where ffmpeg >nul 2>&1
  if %ERRORLEVEL% neq 0 (
      if exist "C:\Program Files\FFmpeg\bin\ffmpeg.exe" (
          set "PATH=%PATH%;C:\Program Files\FFmpeg\bin"
      ) else (
          echo Installing FFmpeg via winget...
          winget install --id FFmpeg.FFmpeg --accept-package-agreements --accept-source-agreements --silent
          set "PATH=%PATH%;C:\Program Files\FFmpeg\bin"
      )
  )
  
  :: Проверка CUDA
  nvidia-smi >nul 2>&1
  if %ERRORLEVEL% eq 0 (
      echo Nvidia GPU detected. Installing with CUDA support...
      pip install -e .[cuda]
  ) else (
      pip install -e .
  )
  ```

- [ ] **Step 2: Обновить menu.bat и start.bat**
  Сделать автоматический вызов `install.bat` в начале скрипта, если папка `venv` не существует.
  Обновить опции меню в `menu.bat` для вызова новой команды `--convert-mp3 %filepaths%` и автоопределения форматов.

- [ ] **Step 3: Проверить запуск**
  Запустить `menu.bat` на системе и проверить, что при переименовании папки `venv` запускается автоматический процесс переустановки.

- [ ] **Step 4: Сделать коммит**
  ```bash
  git add install.bat menu.bat start.bat
  git commit -m "feat: automate Windows dependencies setup and update Batch scripts"
  ```

---

### Task 9: Автоматическая установка зависимостей в Linux/macOS-скриптах

**Files:**
- Modify: `install.sh`
- Modify: `menu.sh`
- Modify: `start.sh`

- [ ] **Step 1: Обновить install.sh**
  Внедрить автоматическую детекцию CUDA и установку дополнительных библиотек при наличии `nvidia-smi`.
  ```bash
  if command -v nvidia-smi &>/dev/null; then
      echo "Nvidia GPU detected. Installing dependencies with CUDA support..."
      pip install -e .[cuda]
  else
      echo "Installing base dependencies (CPU)..."
      pip install -e .
  fi
  ```

- [ ] **Step 2: Обновить menu.sh и start.sh**
  Добавить автоматический вызов `./install.sh`, если папка `venv` не существует.
  Обновить меню, добавив пункт для конвертации в MP3 и пункт транскрибации с автоопределением.

- [ ] **Step 3: Проверить запуск**
  Запустить `./menu.sh` и убедиться в работоспособности.

- [ ] **Step 4: Сделать коммит**
  ```bash
  git add install.sh menu.sh start.sh
  git commit -m "feat: automate Unix dependencies setup and update shell scripts"
  ```

---

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-25-video-transcriber-enhancements.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
