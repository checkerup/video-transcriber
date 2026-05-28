"""PyWebView entry point — opens the desktop GUI."""

from __future__ import annotations

import logging
from pathlib import Path

from ..config import AppConfig
from .api import JsApi


logger = logging.getLogger(__name__)


def launch(config: AppConfig, config_path: Path, project_root: Path,
           *, debug: bool = False, port: int | None = None) -> None:
    """Open the desktop window. Blocks until the user closes it.

    If ``port`` is given, the same UI is also served over HTTP on that port
    (so the user can open it in any browser on the same machine). Otherwise
    runs purely as a desktop window.
    """
    import webview

    static_dir = Path(__file__).parent / "static"
    index_html = static_dir / "index.html"
    if not index_html.exists():
        raise FileNotFoundError(f"GUI not built: missing {index_html}")

    api = JsApi(config=config, config_path=config_path, project_root=project_root)
    title = "Video Transcriber"

    window = webview.create_window(
        title=title,
        url=str(index_html),
        js_api=api,
        width=1180,
        height=780,
        min_size=(960, 600),
        text_select=True,
        confirm_close=False,
    )
    api.attach_window(window)

    def _on_loaded() -> None:
        logger.info("GUI window loaded — JS api is reachable")

    window.events.loaded += _on_loaded

    # http_server lets the same page be reachable in a browser too;
    # PyWebView serves on a random port unless given one.
    webview.start(debug=debug, http_server=True, http_port=port)
