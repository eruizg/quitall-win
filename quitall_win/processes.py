"""Process enumeration and lifecycle control.

For v1 we only need to:
  - Enumerate user-facing apps (those with visible windows).
  - Quit one gracefully (WM_CLOSE).
  - Force-quit one (TerminateProcess).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

from . import win_api


# Core Windows / shell processes we never touch even if they somehow drift
# into our list. Auto-quit must be defensive — quitting Explorer or DWM
# would ruin the user's session.
_SYSTEM_BLOCKLIST: frozenset[str] = frozenset(
    name.lower()
    for name in (
        "system",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "winlogon.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "dwm.exe",
        "fontdrvhost.exe",
        "explorer.exe",
        "sihost.exe",
        "taskhostw.exe",
        "ctfmon.exe",
        "runtimebroker.exe",
        "searchhost.exe",
        "startmenuexperiencehost.exe",
        "shellexperiencehost.exe",
        "applicationframehost.exe",
        "textinputhost.exe",
        "lockapp.exe",
        "useroobebroker.exe",
        "wmiprvse.exe",
        "audiodg.exe",
        "conhost.exe",
        "spoolsv.exe",
        "memcompression",
    )
)


@dataclass(slots=True, frozen=True)
class AppEntry:
    pid: int
    name: str          # exe filename, e.g. "chrome.exe"
    display_name: str  # user-friendly, e.g. "Chrome"
    exe: Optional[str]


def _is_system(name: str, username: str | None) -> bool:
    if name.lower() in _SYSTEM_BLOCKLIST:
        return True
    if username and username.lower().startswith("nt authority\\"):
        return True
    return False


def _friendly_name(exe: str | None, name: str) -> str:
    if exe:
        stem = Path(exe).stem
        if stem.islower():
            return stem.replace("_", " ").title()
        return stem
    if name:
        return Path(name).stem
    return "Unknown"


def list_visible_apps() -> list[AppEntry]:
    """Return one AppEntry per PID that currently has a visible window."""
    target_pids = win_api.pids_with_visible_windows()
    if not target_pids:
        return []

    self_pid = os.getpid()
    apps: list[AppEntry] = []

    for pid in target_pids:
        if pid == self_pid:
            continue
        try:
            proc = psutil.Process(pid)
            info = proc.as_dict(attrs=("pid", "name", "exe", "username"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        name = info.get("name") or ""
        if _is_system(name, info.get("username")):
            continue

        apps.append(
            AppEntry(
                pid=pid,
                name=name,
                display_name=_friendly_name(info.get("exe"), name),
                exe=info.get("exe"),
            )
        )

    apps.sort(key=lambda a: a.display_name.lower())
    return apps


def quit_app(pid: int) -> bool:
    """Graceful close — gives the app a chance to prompt for unsaved work."""
    return win_api.post_close_to_pid(pid) > 0


def force_quit_app(pid: int, timeout: float = 2.0) -> bool:
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return True
    try:
        proc.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    try:
        proc.wait(timeout=timeout)
        return True
    except psutil.TimeoutExpired:
        return False


def is_alive(pid: int) -> bool:
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
