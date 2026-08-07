"""Entry point: wire config -> tracker -> engine -> tray, then run."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from . import APP_NAME
from .config import Config
from .engine import AutoQuitEngine
from .tracker import FocusTracker
from .ui.tray import TrayController


def _ensure_single_instance(app: QApplication) -> bool:
    """Best-effort guard: refuse to run twice on the same machine.

    Uses a named mutex via ctypes — survives PyInstaller bundling.
    """
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE

    handle = kernel32.CreateMutexW(None, False, "Global\\QuitAllWin.SingleInstance")
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        QMessageBox.information(
            None,
            APP_NAME,
            f"{APP_NAME} is already running. Look for it in the system tray.",
        )
        return False
    # Stash the handle on the app so it lives for the process lifetime.
    app._single_instance_handle = handle  # type: ignore[attr-defined]
    return True


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # we live in the tray

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            APP_NAME,
            "No system tray detected. QuitAll-Win needs a tray to run.",
        )
        return 1

    if not _ensure_single_instance(app):
        return 0

    config = Config.load()
    tracker = FocusTracker(poll_ms=1000)
    engine = AutoQuitEngine(config, tracker, check_interval_ms=30_000)
    tray = TrayController(app, config, engine)  # noqa: F841 — keeps tray alive

    tracker.start()
    engine.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
