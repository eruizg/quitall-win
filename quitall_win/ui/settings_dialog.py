"""The one and only dialog for v1: edit the auto-quit settings."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, autostart
from ..config import Config


class SettingsDialog(QDialog):
    """A small modal where the user configures auto-quit behavior."""

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Settings")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._config = config

        self._enabled = QCheckBox("Enable auto-quit")
        self._enabled.setChecked(config.enabled)

        self._threshold = QSpinBox()
        self._threshold.setRange(1, 24 * 60)
        self._threshold.setSuffix(" minutes")
        self._threshold.setValue(max(1, config.threshold_seconds // 60))

        self._force = QCheckBox("Force quit (skip 'unsaved work' prompts)")
        self._force.setChecked(config.force_quit)
        self._force.setToolTip(
            "When OFF (recommended), apps get a graceful close — they can prompt "
            "to save work. When ON, they're terminated immediately."
        )

        self._notify = QCheckBox("Show a notification when an app is quit")
        self._notify.setChecked(config.notify_on_quit)

        self._autostart = QCheckBox("Start with Windows")
        self._autostart.setChecked(autostart.is_enabled())
        if not autostart.is_supported():
            self._autostart.setEnabled(False)
            self._autostart.setToolTip(
                "Available only when running the bundled .exe. "
                "Build it with `.\\build.ps1` and reopen this dialog."
            )

        self._whitelist = QPlainTextEdit()
        self._whitelist.setPlaceholderText(
            "One app name per line, e.g.\n"
            "code.exe\n"
            "spotify.exe\n"
            "Slack"
        )
        self._whitelist.setPlainText("\n".join(config.whitelist))
        self._whitelist.setMinimumHeight(140)

        # ---- layout --------------------------------------------------------
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(self._enabled)
        form.addRow("Quit apps unused for:", self._threshold)
        form.addRow(self._force)
        form.addRow(self._notify)
        form.addRow(self._autostart)

        wl_label = QLabel("Whitelist (these apps are never auto-quit)")
        wl_label.setStyleSheet("font-weight: 600; margin-top: 8px;")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(wl_label)
        layout.addWidget(self._whitelist)
        layout.addSpacing(8)
        layout.addWidget(buttons)

    # ----------------------------------------------------------------- save
    def _on_save(self) -> None:
        self._config.enabled = self._enabled.isChecked()
        self._config.threshold_seconds = self._threshold.value() * 60
        self._config.force_quit = self._force.isChecked()
        self._config.notify_on_quit = self._notify.isChecked()
        self._config.whitelist = [
            line.strip()
            for line in self._whitelist.toPlainText().splitlines()
            if line.strip()
        ]
        self._config.save()

        # Apply autostart change after the config is on disk so the new exe,
        # if it's launched at next login, sees the user's intended state.
        if self._autostart.isEnabled():
            wanted = self._autostart.isChecked()
            currently = autostart.is_enabled()
            if wanted and not currently:
                autostart.enable()
            elif not wanted and currently:
                autostart.disable()

        self.accept()
