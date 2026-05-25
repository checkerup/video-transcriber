import time
import threading
from video_transcriber.config import AppConfig
from video_transcriber.watcher import VideoFileHandler

def test_sequential_processing_queue():
    processed_files = []
    lock = threading.Lock()
    
    def mock_callback(file_path):
        time.sleep(0.1)
        with lock:
            processed_files.append(file_path)

    queue = []
    config = AppConfig()
    handler = VideoFileHandler(config, mock_callback, queue, lock)
    # Stub _is_file_stable to return True so we don't require the file to exist on disk
    handler._is_file_stable = lambda file_path: True
    
    # Process after delay
    handler._process_after_delay("file1.mp4")
    handler._process_after_delay("file2.mp4")
    
    # Assert they are only appended to the queue, and not executed (mock_callback is not called by VideoFileHandler)
    assert "file1.mp4" in queue
    assert "file2.mp4" in queue
    
    # Wait to ensure any spawned background threads have run
    time.sleep(0.2)
    assert len(processed_files) == 0
