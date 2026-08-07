"""Tracks the last time each PID had foreground focus.

Runs on a Qt timer in the main thread. We use `time.monotonic()` so we're
immune to wall-clock changes (NTP sync, daylight savings, manual changes).
"""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer

from . import win_api


class FocusTracker(QObject):
    def __init__(self, poll_ms: int = 1000, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_seen: dict[int, float] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self._poll)

    # ------------------------------------------------------------- lifecycle
    def start(self) -> None:
        self._poll()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    # --------------------------------------------------------------- queries
    def seconds_since_foreground(self, pid: int) -> float:
        """How long since `pid` last had focus.

        Returns +inf if we've never observed this PID in the foreground —
        callers should treat that as "don't auto-quit yet, we don't know
        whether the user has used it."
        """
        last = self._last_seen.get(pid)
        if last is None:
            return float("inf")
        return time.monotonic() - last

    def has_been_seen(self, pid: int) -> bool:
        return pid in self._last_seen

    def forget(self, pid: int) -> None:
        self._last_seen.pop(pid, None)

    # -------------------------------------------------------------- internal
    def _poll(self) -> None:
        pid = win_api.get_foreground_pid()
        if pid is not None:
            self._last_seen[pid] = time.monotonic()
