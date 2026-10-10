"""
updater.py - Automaattinen paivitystarkistin ja yhden klikkauksen paivitys
"""

import json
import os
import sys
import tempfile
import urllib.request
from PyQt6.QtCore import QProcess, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox, QProgressDialog

APP_VERSION = "1.0.4"
GITHUB_REPO = "alexylivarvi-lang/simple-browser"


class UpdateCheckThread(QThread):
    """Taustasäie, joka hakee uusimman version GitHub Releases -rajapinnasta."""
    update_found = pyqtSignal(str, str, str, str)  # (latest_version, html_url, body, direct_installer_url)
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

                    # Etsitään suora asennusohjelman latauslinkki
                    direct_installer_url = ""
                    for asset in data.get("assets", []):
                        if asset.get("name") == "SimpleBrowser-Setup.exe":
                            direct_installer_url = asset.get("browser_download_url", "")
                            break

                    if latest_tag and self._is_newer_version(latest_tag, APP_VERSION):
                        self.update_found.emit(latest_tag, html_url, body, direct_installer_url)
                    else:
                        self.no_update_found.emit()
                else:
                    self.no_update_found.emit()
        except Exception as e:
            self.check_failed.emit(str(e))

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Vertaa versionumeroita (esim. 1.0.4 > 1.0.3)."""
        try:
            latest_parts = [int(p) for p in latest.split(".")]
            current_parts = [int(p) for p in current.split(".")]
            return latest_parts > current_parts
        except Exception:
            return latest != current


class DownloadWorker(QThread):
    """Lataa päivitystiedoston taustalla ja raportoi edistymisen."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, destination: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.destination = destination

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "SimpleBrowser-Downloader"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_length = resp.headers.get("Content-Length")
                total_size = int(content_length) if content_length and content_length.isdigit() else 0
                downloaded = 0
                chunk_size = 64 * 1024

                with open(self.destination, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(min(100, percent))

            self.finished.emit(self.destination)
        except Exception as e:
            self.error.emit(str(e))


class UpdateManager:
    """Hallitsee päivitystarkistuksia ja automaattista latausta."""

    def __init__(self, parent=None):
        self.parent = parent
        self._check_thread = None
        self._download_worker = None
        self._progress_dialog = None

    def check_for_updates(self, silent: bool = False):
        """Käynnistää päivitystarkistuksen taustalla."""
        self._check_thread = UpdateCheckThread(self.parent)
        self._check_thread.update_found.connect(self._on_update_found)
        if not silent:
            self._check_thread.no_update_found.connect(self._on_no_update_found)
            self._check_thread.check_failed.connect(self._on_check_failed)
        self._check_thread.start()

    def _on_update_found(self, latest_version: str, html_url: str, body: str, direct_installer_url: str):
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Päivitys saatavilla")
        msg_box.setText(
            f"<h3>✨ Uusi versio saatavilla!</h3>"
            f"<p>Käytössäsi on versio <code>v{APP_VERSION}</code>.<br>"
            f"Uusin versio on <b>v{latest_version}</b>.</p>"
            f"<p>Haluatko päivittää selaimen nyt?</p>"
        )
        
        btn_update = msg_box.addButton("⚡ Päivitä automaattisesti", QMessageBox.ButtonRole.AcceptRole)
        btn_browser = msg_box.addButton("🌐 Avaa lataussivu", QMessageBox.ButtonRole.ActionRole)
        btn_later = msg_box.addButton("Myöhemmin", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_update:
            if direct_installer_url:
                self._start_auto_download(direct_installer_url, latest_version)
            else:
                QDesktopServices.openUrl(QUrl(html_url))
        elif clicked == btn_browser:
            QDesktopServices.openUrl(QUrl(html_url))

    def _start_auto_download(self, url: str, version: str):
        temp_dir = tempfile.gettempdir()
        dest_path = os.path.join(temp_dir, f"SimpleBrowser-Setup-v{version}.exe")

        self._progress_dialog = QProgressDialog("Ladataan päivitystä...", "Peruuta", 0, 100, self.parent)
        self._progress_dialog.setWindowTitle("Päivitetään SimpleBrowseria")
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)

        self._download_worker = DownloadWorker(url, dest_path, self.parent)
        self._download_worker.progress.connect(self._progress_dialog.setValue)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)

        self._progress_dialog.canceled.connect(self._download_worker.terminate)
        self._download_worker.start()

    def _on_download_finished(self, setup_path: str):
        if self._progress_dialog:
            self._progress_dialog.close()

        msg = QMessageBox.question(
            self.parent,
            "Päivitys ladattu",
            "Päivitys on ladattu onnistuneesti!\n\nAsennetaanko päivitys nyt ja käynnistetään selain uudelleen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if msg == QMessageBox.StandardButton.Yes:
            # Käynnistetään asennusohjelma ja suljetaan selain
            QProcess.startDetached(setup_path, [])
            sys.exit(0)

    def _on_download_error(self, err_msg: str):
        if self._progress_dialog:
            self._progress_dialog.close()
        QMessageBox.warning(
            self.parent,
            "Lataus epäonnistui",
            f"Päivityksen automaattinen lataus epäonnistui:\n{err_msg}\n\nVoit ladata sen manuaalisesti lataussivulta.",
        )

    def _on_no_update_found(self):
        QMessageBox.information(
            self.parent,
            "Päivitykset ajan tasalla",
            f"Käytössäsi on jo uusin versio (v{APP_VERSION}).",
        )

    def _on_check_failed(self, error: str):
        QMessageBox.warning(
            self.parent,
            "Päivitystarkistus epäonnistui",
            "Päivityspalvelimeen ei saatu yhteyttä juuri nyt.",
        )
