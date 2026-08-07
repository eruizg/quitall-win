"""The auto-quit engine.

Every `check_interval_ms` (default 30 s) we walk the list of user-facing
apps and, for each one that:

  - has been observed in the foreground at least once since we started,
  - is not in the user's whitelist,
  - has been out of foreground for >= the configured threshold,

we issue a graceful quit (or a force quit, if configured). A `Signal` is
emitted for every quit so the tray can show a Windows toast.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from . import processes
from .config import Config
from .tracker import FocusTracker


class AutoQuitEngine(QObject):
    quit_triggered = Signal(int, str)   # (pid, display_name)

    def __init__(
        self,
        config: Config,
        tracker: FocusTracker,
        check_interval_ms: int = 30_000,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._tracker = tracker
        self._timer = QTimer(self)
        self._timer.setInterval(check_interval_ms)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------- lifecycle
    def start(self) -> None:
        if self._config.enabled:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def reload(self) -> None:
        """Call after the user edits the config from the settings dialog."""
        self.stop()
        self.start()

    # --------------------------------------------------------------- queries
    def is_running(self) -> bool:
        return self._timer.isActive()

    # -------------------------------------------------------------- internal
    def _tick(self) -> None:
        cfg = self._config
        if not cfg.enabled:
            return

        threshold = cfg.threshold_seconds
        whitelist = {n.lower() for n in cfg.whitelist}
        force = cfg.force_quit

        for app in processes.list_visible_apps():
            if app.name.lower() in whitelist or app.display_name.lower() in whitelist:
                continue
            if not self._tracker.has_been_seen(app.pid):
                # We've never seen it in foreground since we started — be
                # conservative and skip until we have observed real usage.
                continue
            idle = self._tracker.seconds_since_foreground(app.pid)
            if idle < threshold:
                continue

            ok = processes.force_quit_app(app.pid) if force else processes.quit_app(app.pid)
            if ok:
                self._tracker.forget(app.pid)
                self.quit_triggered.emit(app.pid, app.display_name)
