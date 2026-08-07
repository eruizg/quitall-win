"""Config for the v1 auto-quit-only build.

Persisted as TOML in %APPDATA%\\QuitAllWin\\config.toml so the user can
edit it by hand if they want, and so we survive PyInstaller-rebuilds.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

import tomli_w


def _config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    p = Path(base) / "QuitAllWin"
    p.mkdir(parents=True, exist_ok=True)
    return p


CONFIG_PATH: Path = _config_dir() / "config.toml"


# Apps the user almost certainly does NOT want auto-quitting. Tools they
# leave running on purpose (terminal, editor, comms). The user can edit
# this list freely from the settings dialog.
_DEFAULT_WHITELIST: list[str] = [
    "code.exe",
    "windowsterminal.exe",
    "wt.exe",
    "slack.exe",
    "discord.exe",
    "spotify.exe",
    "obs64.exe",
    "obs32.exe",
]


@dataclass(slots=True)
class Config:
    enabled: bool = False
    threshold_seconds: int = 1800       # 30 minutes
    force_quit: bool = False            # graceful by default
    notify_on_quit: bool = True
    whitelist: list[str] = field(default_factory=lambda: list(_DEFAULT_WHITELIST))

    # ------------------------------------------------------------------ I/O
    @classmethod
    def load(cls) -> "Config":
        if not CONFIG_PATH.exists():
            cfg = cls()
            cfg.save()
            return cfg
        try:
            with CONFIG_PATH.open("rb") as fh:
                data = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError):
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            threshold_seconds=int(data.get("threshold_seconds", 1800)),
            force_quit=bool(data.get("force_quit", False)),
            notify_on_quit=bool(data.get("notify_on_quit", True)),
            whitelist=[str(x) for x in data.get("whitelist", _DEFAULT_WHITELIST)],
        )

    def save(self) -> None:
        with CONFIG_PATH.open("wb") as fh:
            tomli_w.dump(asdict(self), fh)
