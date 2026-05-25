import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_APP_NAME = "video-transcriber"
_APP_DESCRIPTION = "Auto video transcription service"


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _get_python_executable() -> str:
    venv = _get_project_root() / "venv"
    if platform.system() == "Windows":
        python = venv / "Scripts" / "python.exe"
    else:
        python = venv / "bin" / "python"
    if python.exists():
        return str(python)
    return sys.executable


def _get_working_dir() -> str:
    return str(_get_project_root())


def _install_windows(config_path: Path | None = None) -> bool:
    task_name = _APP_NAME
    python = _get_python_executable()
    workdir = _get_working_dir()

    cmd = [
        "schtasks", "/Create",
        "/TN", task_name,
        "/TR", f'"{python}" -m video_transcriber.main',
        "/SC", "ONLOGON",
        "/RL", "LIMITED",
        "/F",
    ]

    if config_path:
        cmd.extend(["/TR", f'"{python}" -m video_transcriber.main --config "{config_path}"'])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            logger.info("Windows Task Scheduler: task '%s' created", task_name)
            return True
        logger.error("schtasks failed: %s", result.stderr)
    except FileNotFoundError:
        logger.error("schtasks not found — not a standard Windows install?")
    except Exception as e:
        logger.error("Windows autostart failed: %s", e)
    return False


def _uninstall_windows() -> bool:
    try:
        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", _APP_NAME, "/F"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            logger.info("Windows Task Scheduler: task '%s' deleted", _APP_NAME)
            return True
        logger.error("schtasks delete failed: %s", result.stderr)
    except Exception as e:
        logger.error("Windows autostart remove failed: %s", e)
    return False


def _install_macos(config_path: Path | None = None) -> bool:
    python = _get_python_executable()
    workdir = _get_working_dir()

    config_str = f"        <string>--config</string>\n        <string>{config_path}</string>\n" if config_path else ""

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{_APP_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>video_transcriber.main</string>
{config_str}    </array>
    <key>WorkingDirectory</key>
    <string>{workdir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{workdir}/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>{workdir}/daemon_error.log</string>
</dict>
</plist>
"""

    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / f"com.{_APP_NAME}.plist"

    try:
        plist_path.write_text(plist_content, encoding="utf-8")
        subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True, timeout=10)
        logger.info("macOS LaunchAgent installed: %s", plist_path)
        return True
    except Exception as e:
        logger.error("macOS autostart failed: %s", e)
    return False


def _uninstall_macos() -> bool:
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.{_APP_NAME}.plist"
    try:
        if plist_path.exists():
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True, timeout=10)
            plist_path.unlink()
            logger.info("macOS LaunchAgent removed")
            return True
        logger.info("macOS LaunchAgent not found — nothing to remove")
        return True
    except Exception as e:
        logger.error("macOS autostart remove failed: %s", e)
    return False


def _install_linux(config_path: Path | None = None) -> bool:
    python = _get_python_executable()
    workdir = _get_working_dir()

    config_arg = ""
    if config_path:
        config_arg = f' --config "{config_path}"'

    service_content = f"""[Unit]
Description={_APP_DESCRIPTION}
After=network.target

[Service]
Type=simple
WorkingDirectory={workdir}
ExecStart={python} -m video_transcriber.main{config_arg}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""

    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    service_path = systemd_dir / f"{_APP_NAME}.service"

    try:
        service_path.write_text(service_content, encoding="utf-8")
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, timeout=10)
        subprocess.run(["systemctl", "--user", "enable", f"{_APP_NAME}.service"], capture_output=True, timeout=10)
        logger.info("Linux systemd user service installed: %s", service_path)
        return True
    except Exception as e:
        logger.error("Linux autostart failed: %s", e)
    return False


def _uninstall_linux() -> bool:
    service_name = f"{_APP_NAME}.service"
    try:
        subprocess.run(["systemctl", "--user", "disable", service_name], capture_output=True, timeout=10)
        service_path = Path.home() / ".config" / "systemd" / "user" / service_name
        if service_path.exists():
            service_path.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, timeout=10)
        logger.info("Linux systemd service removed")
        return True
    except Exception as e:
        logger.error("Linux autostart remove failed: %s", e)
    return False


def install_autostart(config_path: Path | None = None) -> bool:
    os_name = platform.system()
    installers = {
        "Windows": _install_windows,
        "Darwin": _install_macos,
        "Linux": _install_linux,
    }
    installer = installers.get(os_name)
    if not installer:
        logger.error("Unsupported OS for autostart: %s", os_name)
        return False

    logger.info("Installing autostart on %s...", os_name)
    return installer(config_path=config_path)


def uninstall_autostart() -> bool:
    os_name = platform.system()
    uninstallers = {
        "Windows": _uninstall_windows,
        "Darwin": _uninstall_macos,
        "Linux": _uninstall_linux,
    }
    uninstaller = uninstallers.get(os_name)
    if not uninstaller:
        logger.error("Unsupported OS: %s", os_name)
        return False

    logger.info("Removing autostart on %s...", os_name)
    return uninstaller()


def is_autostart_installed() -> bool:
    os_name = platform.system()

    if os_name == "Windows":
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", _APP_NAME],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    if os_name == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.{_APP_NAME}.plist"
        return plist_path.exists()

    if os_name == "Linux":
        service_path = Path.home() / ".config" / "systemd" / "user" / f"{_APP_NAME}.service"
        return service_path.exists()

    return False
