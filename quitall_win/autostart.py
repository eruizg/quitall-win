"""Manage the 'Start with Windows' option via a Startup-folder shortcut.

We use the user-level Startup folder rather than the registry Run key for
two reasons: (a) it shows up in Task Manager's Startup tab where the user
expects to see it, and (b) it's trivial to remove if the app misbehaves —
the user just deletes the .lnk.

In dev mode (``python -m quitall_win``) the feature reports as unsupported
because ``sys.executable`` points at the Python interpreter, not at a
stable launcher. Build the bundled exe first.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from . import APP_NAME

_SHORTCUT_NAME = "QuitAllWin.lnk"


def _startup_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _shortcut_path() -> Path:
    return _startup_dir() / _SHORTCUT_NAME


def is_supported() -> bool:
    """Only meaningful when running from the bundled .exe."""
    return bool(getattr(sys, "frozen", False))


def is_enabled() -> bool:
    return _shortcut_path().exists()


def enable() -> bool:
    """Create (or overwrite) the Startup-folder shortcut. Returns success."""
    if not is_supported():
        return False
    target = sys.executable
    lnk = _shortcut_path()
    lnk.parent.mkdir(parents=True, exist_ok=True)
    try:
        from win32com.client import Dispatch  # provided by pywin32

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(lnk))
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = str(Path(target).parent)
        shortcut.Description = f"{APP_NAME} — auto-quit unused apps"
        shortcut.Save()
        return True
    except Exception:
        return False


def disable() -> bool:
    """Remove the Startup-folder shortcut. Idempotent."""
    lnk = _shortcut_path()
    try:
        if lnk.exists():
            lnk.unlink()
        return True
    except OSError:
        return False
