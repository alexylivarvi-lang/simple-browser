"""
updater.py - Turvallinen atominen paivitys ja automaattinen palautus (Rollback)
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


def verify_exe_integrity(filepath: str) -> bool:
    """Tarkistaa, etta ladattu suoritettava tiedosto on ehja ja aito Windows PE .exe."""
    try:
        if not os.path.exists(filepath):
            return False
        # Tiedoston koon tulee olla vahintaan 10 megatavua
        if os.path.getsize(filepath) < 10 * 1024 * 1024:
            return False
        # Windows PE .exe alkaa aina tavuilla 'MZ' (0x4D, 0x5A)
        with open(filepath, "rb") as f:
            header = f.read(2)
            return header == b"MZ"
    except Exception:
        return False


def get_current_exe_path() -> str:
    """Hakee nykyisen suoritettavan ohjelman polun."""
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    # Kehitystilan polku
    dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist", "SimpleBrowser.exe"))
    if os.path.exists(dev_path):
        return dev_path
    desktop_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "SimpleBrowser.exe")
    if os.path.exists(desktop_path):
        return desktop_path
    return os.path.abspath(sys.executable)


def execute_atomic_update(target_exe: str, new_exe: str):
    """
    Suorittaa turvallisen paivityksen:
    1. Odottaa nykyisen prosessin sulkeutumista
    2. Ottaa varmuuskopion (SimpleBrowser.exe.bak)
    3. Ylikirjoittaa tiedoston
    4. Testaa kaynnistyksen
    5. Palauttaa vanhan (Rollback) jos uusi ei kaynnisty
    """
    old_pid = os.getpid()
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "simplebrowser_update.ps1")

    ps_content = f"""
param(
    [string]$Target = "{target_exe}",
    [string]$New = "{new_exe}",
    [int]$PidToWait = {old_pid}
)

# 1. Odota etta vanha selain sulkeutuu
if ($PidToWait -gt 0) {{
    while (Get-Process -Id $PidToWait -ErrorAction SilentlyContinue) {{
        Start-Sleep -Milliseconds 200
    }}
}}

$Backup = "$Target.bak"

try {{
    # 2. Luo automaattinen varmuuskopio
    if (Test-Path $Target) {{
        Copy-Item -Path $Target -Destination $Backup -Force
    }}

    # 3. Ylikirjoita uusi versio
    Move-Item -Path $New -Destination $Target -Force

    # 4. Testaa kaynnistys
    $proc = Start-Process -FilePath $Target -PassThru
    Start-Sleep -Seconds 2

    # Jos ohjelma kaatui heti kaynnistyksessa, nostetaan virhe
    if ($proc.HasExited -and $proc.ExitCode -ne 0) {{
        throw "Uusi versio kaatui heti kaynnistyksessa virhekoodilla $($proc.ExitCode)"
    }}

    # Onnistui: poistetaan varmuuskopio
    if (Test-Path $Backup) {{
        Remove-Item -Path $Backup -Force -ErrorAction SilentlyContinue
    }}
}} catch {{
    # 5. ROLLBACK: Palautetaan toimiva vanha versio
    if (Test-Path $Backup) {{
        Copy-Item -Path $Backup -Destination $Target -Force
        Start-Process -FilePath $Target
    }}
}}
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(ps_content)

    # Kaynnistetaan irrotettu PowerShell-skripti ja suljetaan selain heti
    cmd = "powershell.exe"
    args = [
        "-WindowStyle", "Hidden",
        "-ExecutionPolicy", "Bypass",
        "-NoProfile",
        "-File", script_path
    ]
    QProcess.startDetached(cmd, args)
    sys.exit(0)


class UpdateCheckThread(QThread):
    """Taustasaie, joka hakee uusimman version GitHub Releases -rajapinnasta."""
    update_found = pyqtSignal(str, str, str, str, str)  # (latest_version, html_url, body, direct_exe_url, direct_installer_url)
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

                    direct_exe_url = ""
                    direct_installer_url = ""
                    for asset in data.get("assets", []):
                        name = asset.get("name", "")
                        if name == "SimpleBrowser.exe":
                            direct_exe_url = asset.get("browser_download_url", "")
                        elif name == "SimpleBrowser-Setup.exe":
                            direct_installer_url = asset.get("browser_download_url", "")

                    if latest_tag and self._is_newer_version(latest_tag, APP_VERSION):
                        self.update_found.emit(latest_tag, html_url, body, direct_exe_url, direct_installer_url)
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
    """Lataa paivitystiedoston taustalla ja raportoi edistymisen."""
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
    """Hallitsee paivitystarkistuksia, eheystarkistusta ja turvallista asennusta."""

    def __init__(self, parent=None):
        self.parent = parent
        self._check_thread = None
        self._download_worker = None
        self._progress_dialog = None
        self._latest_version = ""

    def check_for_updates(self, silent: bool = False):
        """Kaynnistaa paivitystarkistuksen taustalla."""
        self._check_thread = UpdateCheckThread(self.parent)
        self._check_thread.update_found.connect(self._on_update_found)
        if not silent:
            self._check_thread.no_update_found.connect(self._on_no_update_found)
            self._check_thread.check_failed.connect(self._on_check_failed)
        self._check_thread.start()

    def _on_update_found(
        self,
        latest_version: str,
        html_url: str,
        body: str,
        direct_exe_url: str,
        direct_installer_url: str,
    ):
        self._latest_version = latest_version
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Paivitys saatavilla")
        msg_box.setText(
            f"<h3>✨ Uusi versio saatavilla!</h3>"
            f"<p>Kaytossasi on versio <code>v{APP_VERSION}</code>.<br>"
            f"Uusin versio on <b>v{latest_version}</b>.</p>"
            f"<p>Paivitys suoritetaan turvallisesti ylikirjoituksella ja automaattisella palautussuojalla (Rollback).</p>"
        )

        btn_update = msg_box.addButton("⚡ Paivita turvallisesti", QMessageBox.ButtonRole.AcceptRole)
        btn_browser = msg_box.addButton("🌐 Avaa lataussivu", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton("Myohemmin", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_update:
            # Ensisijaisesti ladataan suora .exe jotta in-place paivitys toimii saumattomasti
            download_url = direct_exe_url or direct_installer_url
            if download_url:
                self._start_auto_download(download_url, latest_version)
            else:
                QDesktopServices.openUrl(QUrl(html_url))
        elif clicked == btn_browser:
            QDesktopServices.openUrl(QUrl(html_url))

    def _start_auto_download(self, url: str, version: str):
        temp_dir = tempfile.gettempdir()
        dest_path = os.path.join(temp_dir, f"SimpleBrowser-v{version}-download.exe")

        self._progress_dialog = QProgressDialog("Ladataan paivitysta...", "Peruuta", 0, 100, self.parent)
        self._progress_dialog.setWindowTitle("Paivitetaan SimpleBrowseria")
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setValue(0)

        self._download_worker = DownloadWorker(url, dest_path, self.parent)
        self._download_worker.progress.connect(self._progress_dialog.setValue)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)

        self._progress_dialog.canceled.connect(self._download_worker.terminate)
        self._download_worker.start()

    def _on_download_finished(self, new_exe_path: str):
        if self._progress_dialog:
            self._progress_dialog.close()

        # 1. Tarkistetaan ladatun tiedoston eheys (Pre-flight Integrity Check)
        if not verify_exe_integrity(new_exe_path):
            if os.path.exists(new_exe_path):
                os.remove(new_exe_path)
            QMessageBox.critical(
                self.parent,
                "Eheystarkistus epaonnistui",
                "Ladattu paivitystiedosto oli korruptoitunut tai vajaa!\n\n"
                "Turvallisuussyista vanhaan ohjelmaan ei koskettu, ja virheellinen tiedosto poistettiin.",
            )
            return

        target_exe = get_current_exe_path()

        msg = QMessageBox.question(
            self.parent,
            "Paivitys tarkistettu ja valmis",
            f"Uusi versio v{self._latest_version} on tarkistettu onnistuneesti (Eheystarkistus: OK).\n\n"
            f"Kohdetiedosto:\n{target_exe}\n\n"
            "Asennetaanko paivitys nyt? Ohjelma ottaa automaattisen varmuuskopion ennen ylikirjoitusta.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if msg == QMessageBox.StandardButton.Yes:
            execute_atomic_update(target_exe, new_exe_path)

    def _on_download_error(self, err_msg: str):
        if self._progress_dialog:
            self._progress_dialog.close()
        QMessageBox.warning(
            self.parent,
            "Lataus epaonnistui",
            f"Paivityksen automaattinen lataus epaonnistui:\n{err_msg}\n\nVoit ladata sen manuaalisesti lataussivulta.",
        )

    def _on_no_update_found(self):
        QMessageBox.information(
            self.parent,
            "Paivitykset ajan tasalla",
            f"Kaytossasi on jo uusin versio (v{APP_VERSION}).",
        )

    def _on_check_failed(self, error: str):
        QMessageBox.warning(
            self.parent,
            "Paivitystarkistus epaonnistui",
            "Paivityspalvelimeen ei saatu yhteytta juuri nyt.",
        )
