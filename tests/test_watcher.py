import time
import threading
from video_transcriber.config import AppConfig
from video_transcriber.watcher import VideoFileHandler

def test_sequential_processing_queue():
    lock = threading.Lock()
    
    queue = []
    config = AppConfig()
    handler = VideoFileHandler(config, queue, lock)
    # Stub _is_file_stable to return True so we don't require the file to exist on disk
    handler._is_file_stable = lambda file_path: True
    
    # Process after delay
    handler._process_after_delay("file1.mp4")
    handler._process_after_delay("file2.mp4")
    
    # Assert they are only appended to the queue
    assert "file1.mp4" in queue
    assert "file2.mp4" in queue


def test_queue_worker_pops_immediately():
    from video_transcriber.main import queue_worker, shutdown_event
    import threading
    
    lock = threading.Lock()
    queue = ["file1.mp4", "file2.mp4"]
    processed = []
    
    def mock_callback(file_path, config):
        processed.append(file_path)
        # Set shutdown event inside callback so worker stops immediately after processing
        shutdown_event.set()
        
    shutdown_event.clear()
    
    # We pass None for config as it is just passed to mock_callback
    queue_worker(queue, lock, None, mock_callback)
    
    # Assert queue worker popped immediately before callback
    assert len(processed) == 1
    assert processed[0] == "file1.mp4"
    assert "file1.mp4" not in queue
    assert "file2.mp4" in queue
    
    # Clean up
    shutdown_event.clear()


def test_run_process_watcher_routes_callback(monkeypatch):
    from video_transcriber.process_watcher import run_process_watcher
    from video_transcriber.config import AppConfig
    
    config = AppConfig()
    passed_callback = None
    
    def mock_watch_processes(cfg, on_recording_done=None, *args, **kwargs):
        nonlocal passed_callback
        passed_callback = on_recording_done
        
    monkeypatch.setattr("video_transcriber.process_watcher.watch_processes", mock_watch_processes)
    
    my_callback = lambda video_path: None
    run_process_watcher(config, on_recording_done=my_callback)
    
    assert passed_callback is my_callback


def test_enqueue_file():
    from video_transcriber.main import _enqueue_file, queue, lock
    
    # Ensure queue starts empty
    with lock:
        queue.clear()
        
    _enqueue_file("video_to_process.mp4")
    
    with lock:
        assert "video_to_process.mp4" in queue
        assert len(queue) == 1
        
    # Attempt to enqueue the same file again (should not duplicate)
    _enqueue_file("video_to_process.mp4")
    with lock:
        assert len(queue) == 1
        
    # Clean up
    with lock:
        queue.clear()


def test_video_file_handler_cleanup():
    from video_transcriber.config import AppConfig
    from video_transcriber.watcher import VideoFileHandler
    import threading
    
    lock = threading.Lock()
    queue = []
    config = AppConfig()
    handler = VideoFileHandler(config, queue, lock)
    handler._is_file_stable = lambda file_path: True
    
    # We trigger on_created with a mock event
    class MockEvent:
        is_directory = False
        src_path = "test_video.mp4"
        
    # We need to make sure the extension is valid
    config.watch.extensions = [".mp4"]
    config.watch.delay_seconds = 60.0  # long delay so it doesn't fire immediately
    
    handler.on_created(MockEvent())
    
    # Assert a timer was created and is in self._timers
    assert len(handler._timers) == 1
    timer = list(handler._timers.values())[0]
    assert timer.is_alive()
    
    # Run cleanup
    handler.cleanup()
    
    # Assert timers are cancelled and dict is cleared
    assert len(handler._timers) == 0


def test_watch_processes_graceful_shutdown():
    from video_transcriber.process_watcher import watch_processes
    from video_transcriber.config import AppConfig
    import threading
    import time
    
    config = AppConfig()
    # Mock config.process_watcher
    class MockProcessWatcherConfig:
        program_names = ["test_process.exe"]
        poll_interval = 10
        
    config.process_watcher = MockProcessWatcherConfig()
    
    stop_event = threading.Event()
    stop_event.set()  # set immediately so it exits the loop right away
    
    # This should return immediately because stop_event is set
    start_time = time.time()
    watch_processes(config, stop_event=stop_event)
    duration = time.time() - start_time
    
    # Assert it exited immediately (much less than poll_interval of 10)
    assert duration < 2.0
