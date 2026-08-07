"""System tray icon — the only persistent UI in v1.

Right-click menu:
  - Auto-quit:  ON / OFF (toggleable, syncs the config)
  - Settings...
  - About
  - Quit QuitAll-Win
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QMenu, QSystemTrayIcon

from .. import APP_NAME, __version__
from ..config import Config
from ..engine import AutoQuitEngine
from .settings_dialog import SettingsDialog


def _make_fallback_icon(enabled: bool) -> QIcon:
    """Generate a simple colored-circle icon at runtime.

    Saves us from shipping an icon file in v1. Yellow when active, gray when
    disabled. Replace with a real .ico in v0.2.
    """
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor("#ffc215") if enabled else QColor("#9aa0a6")
    painter.setBrush(color)
    painter.setPen(QColor(0, 0, 0, 80))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#1a1a1a") if enabled else QColor("#ffffff"))
    font = QFont("Segoe UI", 28, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pix.rect(), 0x84, "Q")  # AlignCenter
    painter.end()
    return QIcon(pix)


class TrayController(QObject):
    """Owns the QSystemTrayIcon and wires it to the engine + settings."""

    def __init__(
        self,
        app: QApplication,
        config: Config,
        engine: AutoQuitEngine,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._app = app
        self._config = config
        self._engine = engine

        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip(self._tooltip_text())
        self._tray.setIcon(_make_fallback_icon(config.enabled))

        # ---- menu ----------------------------------------------------------
        menu = QMenu()

        self._toggle_action = QAction("Auto-quit: ON" if config.enabled else "Auto-quit: OFF")
        self._toggle_action.setCheckable(True)
        self._toggle_action.setChecked(config.enabled)
        self._toggle_action.toggled.connect(self._on_toggled)

        settings_action = QAction("Settings…")
        settings_action.triggered.connect(self._on_settings)

        about_action = QAction("About")
        about_action.triggered.connect(self._on_about)

        quit_action = QAction(f"Quit {APP_NAME}")
        quit_action.triggered.connect(self._on_quit)

        menu.addAction(self._toggle_action)
        menu.addSeparator()
        menu.addAction(settings_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        # Show toast when the engine quits something.
        engine.quit_triggered.connect(self._on_app_quit_by_engine)

    # ------------------------------------------------------------- handlers
    def _on_toggled(self, checked: bool) -> None:
        self._config.enabled = checked
        self._config.save()
        self._toggle_action.setText("Auto-quit: ON" if checked else "Auto-quit: OFF")
        self._tray.setIcon(_make_fallback_icon(checked))
        self._tray.setToolTip(self._tooltip_text())
        self._engine.reload()

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self._config)
        if dlg.exec():
            # User saved — sync UI and engine.
            self._toggle_action.setChecked(self._config.enabled)
            self._toggle_action.setText(
                "Auto-quit: ON" if self._config.enabled else "Auto-quit: OFF"
            )
            self._tray.setIcon(_make_fallback_icon(self._config.enabled))
            self._tray.setToolTip(self._tooltip_text())
            self._engine.reload()

    def _on_about(self) -> None:
        QMessageBox.information(
            None,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{__version__}<br><br>"
            "Auto-quits Windows apps that have been unused for a configurable "
            "amount of time. Inspired by QuitAll for macOS.",
        )

    def _on_quit(self) -> None:
        self._engine.stop()
        self._tray.hide()
        self._app.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        # Left-click opens settings — matches Win11 conventions for tray apps.
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._on_settings()

    def _on_app_quit_by_engine(self, _pid: int, name: str) -> None:
        if not self._config.notify_on_quit:
            return
        # Use Qt's tray balloon — works on Win10/11 without extra deps.
        self._tray.showMessage(
            APP_NAME,
            f"Auto-quit: {name} (was idle for "
            f"{self._config.threshold_seconds // 60} min)",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    # --------------------------------------------------------------- helpers
    def _tooltip_text(self) -> str:
        if not self._config.enabled:
            return f"{APP_NAME} (paused)"
        mins = self._config.threshold_seconds // 60
        return f"{APP_NAME} — quitting apps idle > {mins} min"
