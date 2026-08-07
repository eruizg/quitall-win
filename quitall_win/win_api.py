"""Thin wrappers over the few Win32 calls we actually need for v1.

Kept in one module so the rest of the codebase stays idiomatic Python and
the platform-specific code is easy to mock or stub when testing.
"""
from __future__ import annotations

from typing import Optional

import win32con
import win32gui
import win32process


def get_foreground_pid() -> Optional[int]:
    """PID of the process owning the current foreground window, or None."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid or None
    except Exception:
        return None


def pids_with_visible_windows() -> set[int]:
    """Return the set of PIDs that currently own at least one user-facing window.

    "User-facing" means: visible, top-level, has a title, not a tool window,
    not owned by another window. This is the same filter Alt+Tab uses.
    """
    pids: set[int] = set()

    def _cb(hwnd: int, _ctx) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
            return True
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return True
        if not win32gui.GetWindowText(hwnd):
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            return True
        if pid:
            pids.add(pid)
        return True

    win32gui.EnumWindows(_cb, None)
    return pids


def post_close_to_pid(pid: int) -> int:
    """Send WM_CLOSE to every visible top-level window owned by `pid`.

    This is the graceful-quit path: the app gets a chance to prompt for
    unsaved work, just like clicking the X. Returns the count of windows
    we messaged.
    """
    sent = 0

    def _cb(hwnd: int, _ctx) -> bool:
        nonlocal sent
        if not win32gui.IsWindowVisible(hwnd):
            return True
        try:
            _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            return True
        if wpid == pid:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            sent += 1
        return True

    win32gui.EnumWindows(_cb, None)
    return sent
