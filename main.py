"""
main.py - Graafinen työpöytäselain (PyQt6 + WebEngine) v3.0 Pro
"""

import json
import os
import sys
from PyQt6.QtCore import QSize, Qt, QUrl, qInstallMessageHandler, QtMsgType
from PyQt6.QtGui import QAction, QFont, QIcon, QKeySequence, QShortcut
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTabBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from adblocker import AdBlockInterceptor
from app_paths import get_bookmarks_file
from browser_tab import BrowserTab
from find_bar import FindBar
from history_manager import HistoryDialog, HistoryManager
from settings_dialog import SettingsDialog, SettingsManager
from updater import APP_VERSION, UpdateManager


def _qt_message_filter(mode, context, message):
    """Suodatetaan Qt:n sisäiset fonttikokovaroitukset."""
    if "setPointSize: Point size <= 0" in message:
        return
    if mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        sys.stderr.write(f"{message}\n")


qInstallMessageHandler(_qt_message_filter)

# Tyyliteemat (pt-yksiköillä)
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e24;
}

QToolBar {
    background-color: #2b2b36;
    border: none;
    padding: 4px 8px;
    spacing: 6px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 10pt;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #3b3b4a;
    border: 1px solid #4f4f63;
}

QToolButton:pressed {
    background-color: #4a4a5e;
}

QLineEdit {
    background-color: #1a1a22;
    color: #f5f5f5;
    border: 1px solid #444455;
    border-radius: 18px;
    padding: 5px 14px;
    font-size: 10pt;
    selection-background-color: #4361ee;
}

QLineEdit:focus {
    border: 1px solid #4361ee;
    background-color: #16161c;
}

QProgressBar {
    border: none;
    background-color: transparent;
    height: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4361ee;
    border-radius: 1px;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e24;
}

QTabBar::tab {
    background-color: #22222c;
    color: #a0a0b0;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 14px;
    margin-right: 2px;
    min-width: 120px;
    max-width: 220px;
    font-size: 9.5pt;
}

QTabBar::tab:selected {
    background-color: #2f2f3e;
    color: #ffffff;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a36;
    color: #e0e0e0;
}

QStatusBar {
    background-color: #1e1e24;
    color: #888899;
    border-top: 1px solid #2b2b36;
    font-size: 9pt;
    padding: 2px 8px;
}

QMenu {
    background-color: #2b2b36;
    color: #f0f0f0;
    border: 1px solid #3f3f50;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item:selected {
    background-color: #4361ee;
    border-radius: 4px;
}

FindBar {
    background-color: #2b2b36;
    border-top: 1px solid #3f3f50;
}
"""

LIGHT_STYLE = """
QMainWindow {
    background-color: #f4f5f7;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e1e4e8;
    padding: 4px 8px;
    spacing: 6px;
}

QToolButton {
    background-color: transparent;
    color: #333333;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 10pt;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #f0f2f5;
    border: 1px solid #d0d7de;
}

QToolButton:pressed {
    background-color: #e2e5e9;
}

QLineEdit {
    background-color: #f0f2f5;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 18px;
    padding: 5px 14px;
    font-size: 10pt;
    selection-background-color: #0969da;
}

QLineEdit:focus {
    border: 1px solid #0969da;
    background-color: #ffffff;
}

QProgressBar {
    border: none;
    background-color: transparent;
    height: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #0969da;
    border-radius: 1px;
}

QTabWidget::pane {
    border: none;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #eef1f5;
    color: #57606a;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 14px;
    margin-right: 2px;
    min-width: 120px;
    max-width: 220px;
    font-size: 9.5pt;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0969da;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #e4e7ec;
    color: #1f2328;
}

QStatusBar {
    background-color: #ffffff;
    color: #57606a;
    border-top: 1px solid #e1e4e8;
    font-size: 9pt;
    padding: 2px 8px;
}

QMenu {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item:selected {
    background-color: #0969da;
    color: #ffffff;
    border-radius: 4px;
}

FindBar {
    background-color: #ffffff;
    border-top: 1px solid #d0d7de;
}
"""


class DevToolsWindow(QMainWindow):
    """Erillinen ikkuna kehittäjätyökaluille (F12 / DevTools)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kehittäjätyökalut (DevTools)")
        self.resize(900, 600)
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"PyQt6 Moderni Selain Pro (v{APP_VERSION})")
        self.resize(1240, 820)

        # Asetetaan ikkunan kuvake
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.bookmarks = self._load_bookmarks()
        self.devtools_window = None
        self.update_manager = UpdateManager(self)

        # 1. Mainosten esto (AdBlocker)
        self.adblocker = AdBlockInterceptor(self)
        self.adblocker.on_blocked_callback = self._on_ad_blocked
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.adblocker)

        self._setup_ui()
        self._apply_theme()
        self._setup_shortcuts()
        self._setup_downloads()

        # Avataan aloitussivu (Speed Dial)
        self.add_new_tab(QUrl("about:newtab"), "Uusi välilehti")

        # Tarkistetaan päivitykset hiljaisesti taustalla käynnistyksen jälkeen
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.update_manager.check_for_updates(silent=True))

    def _apply_theme(self):
        settings = SettingsManager.load_settings()
        theme = settings.get("theme", "Dark")
        if theme == "Light":
            self.setStyleSheet(LIGHT_STYLE)
        else:
            self.setStyleSheet(DARK_STYLE)

    def _setup_ui(self):
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # 1. Navigaatiotyökalupalkki
        self.nav_toolbar = QToolBar("Navigointi")
        self.nav_toolbar.setMovable(False)
        self.nav_toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(self.nav_toolbar)

        # Takaisin / Eteenpäin
        self.back_btn = QToolButton()
        self.back_btn.setText("◀")
        self.back_btn.setToolTip("Edellinen sivu (Alt+Vasen)")
        self.back_btn.clicked.connect(self._navigate_back)
        self.nav_toolbar.addWidget(self.back_btn)

        self.forward_btn = QToolButton()
        self.forward_btn.setText("▶")
        self.forward_btn.setToolTip("Seuraava sivu (Alt+Oikea)")
        self.forward_btn.clicked.connect(self._navigate_forward)
        self.nav_toolbar.addWidget(self.forward_btn)

        # Päivitä / Pysäytä
        self.reload_btn = QToolButton()
        self.reload_btn.setText("🔄")
        self.reload_btn.setToolTip("Lataa sivu uudelleen (Ctrl+R)")
        self.reload_btn.clicked.connect(self._reload_or_stop)
        self.nav_toolbar.addWidget(self.reload_btn)

        # Koti / Speed Dial
        self.home_btn = QToolButton()
        self.home_btn.setText("🏠")
        self.home_btn.setToolTip("Aloitussivu (Speed Dial)")
        self.home_btn.clicked.connect(self._navigate_home)
        self.nav_toolbar.addWidget(self.home_btn)

        # Osoiterivi
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Kirjoita verkko-osoite tai hakusana ja paina Enter...")
        self.url_bar.returnPressed.connect(self._navigate_to_url)
        self.nav_toolbar.addWidget(self.url_bar)

        # AdBlocker Shield (🛡️)
        self.shield_btn = QToolButton()
        self.shield_btn.setText("🛡️ 0")
        self.shield_btn.setToolTip("Mainosten esto: Päällä (0 estetty). Klikkaa kytkeäksesi.")
        self.shield_btn.clicked.connect(self._toggle_adblock)
        self.nav_toolbar.addWidget(self.shield_btn)

        # Etsi sivulta (Ctrl+F)
        self.find_btn = QToolButton()
        self.find_btn.setText("🔍")
        self.find_btn.setToolTip("Etsi sivulta (Ctrl+F)")
        self.find_btn.clicked.connect(self._toggle_find_bar)
        self.nav_toolbar.addWidget(self.find_btn)

        # Kirjanmerkki (Tähti)
        self.bookmark_btn = QToolButton()
        self.bookmark_btn.setText("★")
        self.bookmark_btn.setToolTip("Lisää kirjanmerkkeihin (Ctrl+D)")
        self.bookmark_btn.clicked.connect(self._add_current_to_bookmarks)
        self.nav_toolbar.addWidget(self.bookmark_btn)

        # Historia
        self.history_btn = QToolButton()
        self.history_btn.setText("📜")
        self.history_btn.setToolTip("Selaushistoria (Ctrl+H)")
        self.history_btn.clicked.connect(self._open_history_dialog)
        self.nav_toolbar.addWidget(self.history_btn)

        # Asetukset
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙️")
        self.settings_btn.setToolTip("Asetukset (Ctrl+,)")
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        self.nav_toolbar.addWidget(self.settings_btn)

        # Uusi välilehti (+)
        self.new_tab_btn = QToolButton()
        self.new_tab_btn.setText("➕")
        self.new_tab_btn.setToolTip("Avaa uusi välilehti (Ctrl+T)")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.nav_toolbar.addWidget(self.new_tab_btn)

        # 2. Kirjanmerkkipalkki
        self.bookmarks_toolbar = QToolBar("Kirjanmerkit")
        self.bookmarks_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.bookmarks_toolbar)
        self._refresh_bookmarks_toolbar()

        # 3. Latauksen edistymispalkki
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        # 4. Välilehtinäkymä
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabBarDoubleClicked.connect(self._on_tabbar_double_clicked)
        
        # Välilehtien kontekstivalikko
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)
        
        self.main_layout.addWidget(self.tab_widget)

        # 5. Sivun sisäinen haku (FindBar)
        self.find_bar = FindBar(self)
        self.find_bar.search_requested.connect(self._on_find_requested)
        self.find_bar.closed.connect(self._on_find_closed)
        self.main_layout.addWidget(self.find_bar)

        # 6. Tilarivi
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("padding-right: 8px;")
        self.status_bar.addPermanentWidget(self.zoom_label)

    def _setup_downloads(self):
        """Kytkee Chromiumin lataustenhallinnan."""
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self._handle_download_request)

    def _handle_download_request(self, download: QWebEngineDownloadRequest):
        suggested_path = download.downloadFileName()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Tallenna tiedosto",
            suggested_path,
        )
        if save_path:
            download.setDownloadDirectory(os.path.dirname(save_path))
            download.setDownloadFileName(os.path.basename(save_path))
            download.accept()
            
            self.status_bar.showMessage(f"Ladataan: {os.path.basename(save_path)}...", 5000)
            download.isFinishedChanged.connect(lambda: self.status_bar.showMessage(f"Lataus valmis: {os.path.basename(save_path)}", 5000))
        else:
            download.cancel()

    def _setup_shortcuts(self):
        """Määritä pikanäppäimet."""
        # Uusi välilehti
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self.add_new_tab())

        # Uusi yksityinen välilehti (Incognito)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self).activated.connect(lambda: self.add_new_tab(is_incognito=True))

        # Tulosta / Vie PDF
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self._export_page_to_pdf)

        # Sulje välilehti
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))

        # Osoiteriville kohdistus
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._focus_url_bar)
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(self._focus_url_bar)

        # Lataa uudelleen
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._reload_or_stop)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._reload_or_stop)

        # Etsi sivulta
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._toggle_find_bar)

        # Selaushistoria
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._open_history_dialog)

        # Asetukset
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(self._open_settings_dialog)

        # Kehittäjätyökalut (F12)
        QShortcut(QKeySequence("F12"), self).activated.connect(self._toggle_devtools)

        # Kirjanmerkki
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._add_current_to_bookmarks)

        # Zoomaus
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._reset_zoom)

    def current_tab(self) -> BrowserTab:
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl: QUrl = None, title: str = "Uusi välilehti", is_incognito: bool = False) -> int:
        tab = BrowserTab(is_incognito=is_incognito, parent=self)
        
        # Yhdistetään signaalit
        tab.urlChanged.connect(lambda url, t=tab: self._update_url_bar(url, t))
        tab.titleChanged.connect(lambda t_str, t=tab: self._update_tab_title(t_str, t))
        tab.iconChanged.connect(lambda icon, t=tab: self._update_tab_icon(icon, t))
        tab.loadProgress.connect(lambda p, t=tab: self._update_progress(p, t))
        tab.loadFinished.connect(lambda ok, t=tab: self._on_load_finished(ok, t))
        tab.status_message_changed.connect(self._set_status_message)
        tab.open_in_new_tab.connect(self.add_new_tab)
        tab.inspect_element_requested.connect(self._show_devtools)
        tab.audio_state_changed.connect(lambda audible, muted, t=tab: self._update_tab_audio_icon(t, audible, muted))

        prefix = "🕵️ " if is_incognito else ""
        index = self.tab_widget.addTab(tab, f"{prefix}{title}")
        self.tab_widget.setCurrentIndex(index)

        if qurl is None or qurl.toString() in ("about:newtab", "about:home", "about:blank"):
            tab.load_speed_dial()
        else:
            tab.setUrl(qurl)

        return index

    def close_tab(self, index: int):
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            if widget:
                widget.deleteLater()
        else:
            self.current_tab().load_speed_dial()

    def _on_tabbar_double_clicked(self, index: int):
        if index == -1:
            self.add_new_tab()

    def _show_tab_context_menu(self, pos):
        index = self.tab_widget.tabBar().tabAt(pos)
        if index < 0:
            return

        tab = self.tab_widget.widget(index)
        menu = QMenu(self)
        
        new_tab_act = menu.addAction("➕ Uusi välilehti")
        incognito_act = menu.addAction("🕵️ Uusi yksityinen välilehti")
        duplicate_act = menu.addAction("📋 Monista välilehti")
        menu.addSeparator()

        is_muted = tab.page().isAudioMuted()
        mute_act = menu.addAction("🔊 Poista mykistys" if is_muted else "🔇 Mykistä välilehti")
        menu.addSeparator()

        close_act = menu.addAction("✕ Sulje välilehti")
        close_others_act = menu.addAction("Sulje muut välilehdet")

        action = menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))
        if action == new_tab_act:
            self.add_new_tab()
        elif action == incognito_act:
            self.add_new_tab(is_incognito=True)
        elif action == duplicate_act:
            self.add_new_tab(tab.url(), tab.title())
        elif action == mute_act:
            tab.toggle_mute()
        elif action == close_act:
            self.close_tab(index)
        elif action == close_others_act:
            for i in range(self.tab_widget.count() - 1, -1, -1):
                if i != index:
                    self.close_tab(i)

    def _on_tab_changed(self, index: int):
        tab = self.current_tab()
        if tab:
            url_str = tab.url().toString()
            self.url_bar.setText("" if url_str == "about:newtab" else url_str)
            self._update_navigation_buttons(tab)
            self.zoom_label.setText(f"{int(tab.zoomFactor() * 100)}%")
            if self.find_bar.isVisible():
                self.find_bar.find_next()

    def _focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def _navigate_to_url(self):
        text = self.url_bar.text().strip()
        tab = self.current_tab()
        if tab and text:
            tab.load_url(text)

    def _navigate_back(self):
        tab = self.current_tab()
        if tab:
            tab.back()

    def _navigate_forward(self):
        tab = self.current_tab()
        if tab:
            tab.forward()

    def _reload_or_stop(self):
        tab = self.current_tab()
        if tab:
            tab.reload()

    def _navigate_home(self):
        tab = self.current_tab()
        if tab:
            tab.load_speed_dial()

    def _update_url_bar(self, qurl: QUrl, tab: BrowserTab):
        if tab == self.current_tab():
            url_str = qurl.toString()
            self.url_bar.setText("" if url_str == "about:newtab" else url_str)
            self._update_navigation_buttons(tab)

    def _update_tab_title(self, title: str, tab: BrowserTab):
        index = self.tab_widget.indexOf(tab)
        if index != -1:
            prefix = "🕵️ " if tab.is_incognito else ""
            short_title = title if len(title) <= 20 else title[:18] + "..."
            self.tab_widget.setTabText(index, f"{prefix}{short_title or 'Uusi välilehti'}")
            self.tab_widget.setTabToolTip(index, f"{prefix}{title}")
            if tab == self.current_tab():
                self.setWindowTitle(f"{title} - PyQt6 Selain Pro" if title else "PyQt6 Selain Pro")

    def _update_tab_icon(self, icon: QIcon, tab: BrowserTab):
        index = self.tab_widget.indexOf(tab)
        if index != -1 and not tab.is_incognito:
            self.tab_widget.setTabIcon(index, icon)

    def _update_tab_audio_icon(self, tab: BrowserTab, audible: bool, muted: bool):
        index = self.tab_widget.indexOf(tab)
        if index == -1:
            return
        curr_text = self.tab_widget.tabText(index)
        # Poistetaan vanha äänimerkki jos oli
        base_text = curr_text.replace(" 🔊", "").replace(" 🔇", "")
        if muted:
            self.tab_widget.setTabText(index, base_text + " 🔇")
        elif audible:
            self.tab_widget.setTabText(index, base_text + " 🔊")
        else:
            self.tab_widget.setTabText(index, base_text)

    def _update_progress(self, progress: int, tab: BrowserTab):
        if tab == self.current_tab():
            self.progress_bar.show()
            self.progress_bar.setValue(progress)
            self.reload_btn.setText("✕")
            self.reload_btn.setToolTip("Pysäytä lataus")

    def _on_load_finished(self, ok: bool, tab: BrowserTab):
        if tab == self.current_tab():
            self.progress_bar.hide()
            self.reload_btn.setText("🔄")
            self.reload_btn.setToolTip("Lataa sivu uudelleen (Ctrl+R)")
            self._update_navigation_buttons(tab)

    def _update_navigation_buttons(self, tab: BrowserTab):
        if tab:
            self.back_btn.setEnabled(tab.history().canGoBack())
            self.forward_btn.setEnabled(tab.history().canGoForward())

    def _set_status_message(self, msg: str):
        self.status_bar.showMessage(msg, 3000 if msg else 0)

    # --- AdBlocker Hallinta ---
    def _toggle_adblock(self):
        enabled = self.adblocker.toggle()
        if enabled:
            self.shield_btn.setText(f"🛡️ {self.adblocker.blocked_count}")
            self.shield_btn.setToolTip(f"Mainosten esto: Päällä ({self.adblocker.blocked_count} estetty). Klikkaa kytkeäksesi.")
            self.status_bar.showMessage("Mainosten ja seurannan esto kytketty PÄÄLLE", 3000)
        else:
            self.shield_btn.setText("🛡️ Pois")
            self.shield_btn.setToolTip("Mainosten esto: POIS PÄÄLTÄ. Klikkaa kytkeäksesi.")
            self.status_bar.showMessage("Mainosten ja seurannan esto kytketty POIS", 3000)

    def _on_ad_blocked(self, count: int, url: str):
        if self.adblocker.enabled:
            self.shield_btn.setText(f"🛡️ {count}")
            self.shield_btn.setToolTip(f"Mainosten esto: Päällä ({count} estetty). Klikkaa kytkeäksesi.")

    # --- PDF Tulostus / Vienti ---
    def _export_page_to_pdf(self):
        tab = self.current_tab()
        if not tab:
            return

        suggested = f"{tab.title() or 'sivu'}.pdf".replace("/", "_").replace("\\", "_")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Tallenna PDF-tiedostoksi",
            suggested,
            "PDF Tiedostot (*.pdf)",
        )
        if file_path:
            tab.export_to_pdf(file_path, lambda path: self.status_bar.showMessage(f"Sivu tallennettu: {os.path.basename(path)}", 4000))

    # --- Sivun sisäinen haku (FindBar) ---
    def _toggle_find_bar(self):
        if self.find_bar.isVisible():
            self.find_bar.close_bar()
        else:
            self.find_bar.show_bar()

    def _on_find_requested(self, text: str, case_sensitive: bool, backward: bool):
        tab = self.current_tab()
        if tab:
            tab.search_in_page(text, case_sensitive, backward)

    def _on_find_closed(self):
        tab = self.current_tab()
        if tab:
            tab.search_in_page("")

    # --- Selaushistoria & Asetukset ---
    def _open_history_dialog(self):
        dialog = HistoryDialog(self)
        dialog.open_url_requested.connect(lambda url: self.add_new_tab(QUrl(url)))
        dialog.exec()

    def _open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self):
        self._apply_theme()
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, BrowserTab):
                tab.apply_settings()
                if tab.url().toString() == "about:newtab":
                    tab.load_speed_dial()
        self.status_bar.showMessage("Asetukset päivitetty onnistuneesti", 3000)

    # --- Kehittäjätyökalut (DevTools / F12) ---
    def _toggle_devtools(self):
        if self.devtools_window and self.devtools_window.isVisible():
            self.devtools_window.close()
        else:
            self._show_devtools()

    def _show_devtools(self):
        tab = self.current_tab()
        if not tab:
            return

        if not self.devtools_window:
            self.devtools_window = DevToolsWindow(self)

        tab.page().setDevToolsPage(self.devtools_window.view.page())
        self.devtools_window.show()
        self.devtools_window.raise_()

    # --- Zoomaus ---
    def _zoom_in(self):
        tab = self.current_tab()
        if tab:
            val = tab.zoom_in()
            self.zoom_label.setText(f"{val}%")

    def _zoom_out(self):
        tab = self.current_tab()
        if tab:
            val = tab.zoom_out()
            self.zoom_label.setText(f"{val}%")

    def _reset_zoom(self):
        tab = self.current_tab()
        if tab:
            val = tab.reset_zoom()
            self.zoom_label.setText(f"{val}%")

    # --- Kirjanmerkit ---
    def _load_bookmarks(self) -> list:
        bookmarks_file = get_bookmarks_file()
        if os.path.exists(bookmarks_file):
            try:
                with open(bookmarks_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_bookmarks(self):
        bookmarks_file = get_bookmarks_file()
        try:
            with open(bookmarks_file, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Kirjanmerkkien tallennus epäonnistui: {e}")

    def _refresh_bookmarks_toolbar(self):
        self.bookmarks_toolbar.clear()
        bm_title = QLabel(" 🔖 ")
        self.bookmarks_toolbar.addWidget(bm_title)

        for bm in self.bookmarks:
            title = bm.get("title", "Linkki")
            url = bm.get("url", "")
            btn = QToolButton()
            btn.setText(title)
            btn.setToolTip(url)
            btn.clicked.connect(lambda checked, u=url: self._open_bookmark_url(u))
            
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, b=btn, u=url, t=title: self._show_bookmark_menu(pos, b, u, t))

            self.bookmarks_toolbar.addWidget(btn)

    def _open_bookmark_url(self, url: str):
        tab = self.current_tab()
        if tab:
            tab.load_url(url)

    def _show_bookmark_menu(self, pos, btn, url, title):
        menu = QMenu(self)
        open_action = menu.addAction("Avaa uudessa välilehdessä")
        delete_action = menu.addAction("Poista kirjanmerkki")
        
        action = menu.exec(btn.mapToGlobal(pos))
        if action == open_action:
            self.add_new_tab(QUrl(url), title)
        elif action == delete_action:
            self.bookmarks = [b for b in self.bookmarks if not (b.get("url") == url and b.get("title") == title)]
            self._save_bookmarks()
            self._refresh_bookmarks_toolbar()

    def _add_current_to_bookmarks(self):
        tab = self.current_tab()
        if not tab:
            return
        
        current_url = tab.url().toString()
        current_title = tab.title() or current_url

        if not current_url or current_url.startswith("about:"):
            return

        title, ok = QInputDialog.getText(
            self,
            "Lisää kirjanmerkki",
            "Kirjanmerkin nimi:",
            QLineEdit.EchoMode.Normal,
            current_title,
        )
        if ok and title:
            exists = any(b.get("url") == current_url for b in self.bookmarks)
            if not exists:
                self.bookmarks.append({"title": title, "url": current_url})
                self._save_bookmarks()
                self._refresh_bookmarks_toolbar()
                self.status_bar.showMessage(f"Lisätty kirjanmerkki: {title}", 3000)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyQt6 Moderni Selain Pro")
    app.setFont(QFont("Segoe UI", 9))
    
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
