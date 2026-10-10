"""
updater.py - Automaattinen päivitystarkistin ja versionhallinta
"""

import json
import urllib.request
from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox

APP_VERSION = "1.0.4"
# Käyttäjän oma GitHub-repositorio
GITHUB_REPO = "alexylivarvi-lang/simple-browser"


class UpdateCheckThread(QThread):
    """Taustasäie, joka hakee uusimman version GitHub Releases -rajapinnasta."""
    update_found = pyqtSignal(str, str, str)  # (latest_version, download_url, release_notes)
    no_update_found = pyqtSignal()
    check_failed = pyqtSignal(str)

    def run(self):
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        headers = {"User-Agent": "SimpleBrowser-UpdateChecker"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    latest_tag = data.get("tag_name", "").lstrip("v").strip()
                    html_url = data.get("html_url", "")
                    body = data.get("body", "")

                    if latest_tag and self._is_newer_version(latest_tag, APP_VERSION):
                        self.update_found.emit(latest_tag, html_url, body)
                    else:
                        self.no_update_found.emit()
                else:
                    self.no_update_found.emit()
        except Exception as e:
            self.check_failed.emit(str(e))

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Vertaa versionumeroita (esim. 1.1.0 > 1.0.0)."""
        try:
            latest_parts = [int(p) for p in latest.split(".")]
            current_parts = [int(p) for p in current.split(".")]
            return latest_parts > current_parts
        except Exception:
            return latest != current


class UpdateManager:
    """Hallitsee päivitystarkistuksia ja näyttää ilmoitukset käyttäjälle."""

    def __init__(self, parent=None):
        self.parent = parent
        self._thread = None

    def check_for_updates(self, silent: bool = False):
        """Käynnistää päivitystarkistuksen taustalla."""
        self._thread = UpdateCheckThread(self.parent)
        self._thread.update_found.connect(self._on_update_found)
        if not silent:
            self._thread.no_update_found.connect(self._on_no_update_found)
            self._thread.check_failed.connect(self._on_check_failed)
        self._thread.start()

    def _on_update_found(self, latest_version: str, download_url: str, release_notes: str):
        msg = (
            f"<b>Uusi versio saatavilla!</b><br><br>"
            f"Nykyinen versio: <code>v{APP_VERSION}</code><br>"
            f"Uusin versio: <b>v{latest_version}</b><br><br>"
            f"Haluatko avata lataussivun ja ladata päivityksen?"
        )
        reply = QMessageBox.information(
            self.parent,
            "Päivitys saatavilla",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and download_url:
            QDesktopServices.openUrl(QUrl(download_url))

    def _on_no_update_found(self):
        QMessageBox.information(
            self.parent,
            "Päivitykset ajan tasalla",
            f"Käytössäsi on uusin versio (v{APP_VERSION}).",
        )

    def _on_check_failed(self, error: str):
        QMessageBox.warning(
            self.parent,
            "Päivitystarkistus epäonnistui",
            "Päivityspalvelimeen ei saatu yhteyttä juuri nyt.",
        )
