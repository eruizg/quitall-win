# QuitAll-Win

> Auto-quits Windows apps that have been unused for a configurable amount of time.
> Inspired by [QuitAll](https://amicoapps.com/app/quitall/) for macOS.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CI](https://github.com/eruizg/quitall-win/actions/workflows/ci.yml/badge.svg)](https://github.com/eruizg/quitall-win/actions/workflows/ci.yml)

QuitAll-Win lives in your system tray, watches which apps you actually use,
and gracefully closes the ones you've stopped using — freeing up RAM
without making you think about it.

## Features (v1)

- ✅ **Auto-quit** apps unused for N minutes (configurable, default 30)
- ✅ **Graceful close** by default (apps prompt to save unsaved work) — force quit available
- ✅ **Whitelist** apps that should never be auto-quit
- ✅ **Toast notifications** when something is quit, so you know what happened
- ✅ **Start with Windows** with one click in the settings dialog
- ✅ **Single .exe installer**, per-user (no admin), with proper Add/Remove Programs entry

## Install

Download the latest `QuitAllWin-Setup-x.y.z.exe` from the
[Releases](https://github.com/eruizg/quitall-win/releases) page and
run it. The installer is per-user (no admin needed) and installs to
`%LOCALAPPDATA%\Programs\QuitAllWin\`.

After install, you'll find a yellow "Q" in your system tray. Right-click
→ **Settings…** to configure.

## Configuration

Stored as TOML at `%APPDATA%\QuitAllWin\config.toml` — feel free to edit
by hand:

```toml
enabled = true
threshold_seconds = 1800
force_quit = false
notify_on_quit = true
whitelist = ["code.exe", "Slack", "spotify.exe"]
```

Whitelist matches against either the **exe filename** (`chrome.exe`) or
the **display name** (`Chrome`), case-insensitive.

## Build from source

Requires Python 3.11+. To run from source:

```powershell
git clone https://github.com/eruizg/quitall-win.git
cd quitall-win
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m quitall_win
```

To build the standalone .exe + installer:

```powershell
winget install --id JRSoftware.InnoSetup   # one-time, for the installer
.\build.ps1
```

Outputs:
- `dist\QuitAllWin.exe` — single-file portable exe (~50 MB)
- `dist\installer\QuitAllWin-Setup-<version>.exe` — distributable installer

## Architecture

```
quitall_win/
├── __main__.py          Entry point — wires components together.
├── autostart.py         Manages the Startup-folder shortcut.
├── config.py            TOML config in %APPDATA%\QuitAllWin.
├── win_api.py           ctypes / pywin32 helpers.
├── processes.py         App listing + quit / force-quit primitives.
├── tracker.py           FocusTracker — Qt timer recording last-foreground time per PID.
├── engine.py            AutoQuitEngine — Qt timer that triggers quits.
└── ui/
    ├── tray.py          System-tray icon, menu, toast notifications.
    └── settings_dialog.py
```

**Two Qt timers** drive everything: a fast one (1 s) updates focus
timestamps; a slow one (30 s) checks whether any app has crossed the
threshold. No background threads, no GIL juggling.

**Safety nets:**
- A blocklist in `processes.py` prevents quitting Explorer, DWM, svchost, and friends.
- Apps that have **never** been observed in the foreground are skipped — protects newly-launched apps.
- A named-mutex single-instance guard prevents two copies fighting.
- Graceful close is the default; force is opt-in.

## Releasing

Tag the commit and push the tag. The `release.yml` GitHub Actions workflow
builds the `.exe`, builds the installer, and publishes a Release with both
artifacts attached.

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## Contributing

PRs welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for the basics. In
short: keep PRs focused, use `git commit -s` for the DCO sign-off, and
run a quick syntax check before pushing.

## License

[GPL-3.0-or-later](./LICENSE). See [NOTICE](./NOTICE) for trademark and
attribution details.

If you fork and redistribute a modified version, please use a different
project name to avoid user confusion.
