"""
browser_tab.py - Yksittäisen selainvälilehden komponentti (v3.0 Pro + Media Optimization)
"""

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import (
    QWebEngineFullScreenRequest,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from history_manager import HistoryManager
from new_tab_page import get_new_tab_html
from settings_dialog import SettingsManager

# Moderni Chrome User-Agent, jotta suoratoistopalvelut (Yle Areena, YouTube, Twitch) toimivat täydellisesti
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


class CustomWebEnginePage(QWebEnginePage):
    """Mukautettu WebEngine-sivu, joka hallitsee oikeudet, välilehdet ja koko ruudun videot."""
    new_tab_requested = pyqtSignal(QUrl)

    def __init__(self, profile=None, parent=None):
        if profile:
            super().__init__(profile, parent)
        else:
            super().__init__(parent)

        # Automaattinen lupa medialle ja toistolle
        self.featurePermissionRequested.connect(self._on_feature_permission_requested)
        self.fullScreenRequested.connect(self._on_fullscreen_requested)

    def createWindow(self, window_type: QWebEnginePage.WebWindowType):
        new_view = BrowserTab()
        self.new_tab_requested.emit(QUrl())
        return new_view.page()

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Sivustojen konsolilokit ohjataan F12 DevToolsiin terminaalin sijaan
        pass

    def _on_feature_permission_requested(self, security_origin: QUrl, feature: QWebEnginePage.Feature):
        # Myönnetään luvat suoratoistolle, kameralle/mikrofonille ja medialle
        self.setFeaturePermission(
            security_origin,
            feature,
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
        )

    def _on_fullscreen_requested(self, request: QWebEngineFullScreenRequest):
        request.accept()


class BrowserTab(QWebEngineView):
    """Yksittäinen selainvälilehti, joka kapseloi QWebEngineView:n ja sen asetukset."""
    
    # Signaalit
    open_in_new_tab = pyqtSignal(QUrl)
    status_message_changed = pyqtSignal(str)
    inspect_element_requested = pyqtSignal()
    audio_state_changed = pyqtSignal(bool, bool)  # (is_audible, is_muted)

    def __init__(self, is_incognito: bool = False, parent=None):
        super().__init__(parent)
        self.is_incognito = is_incognito
        
        # Profiilin alustus
        if self.is_incognito:
            self._profile = QWebEngineProfile(self)
            custom_page = CustomWebEnginePage(self._profile, self)
        else:
            self._profile = QWebEngineProfile.defaultProfile()
            custom_page = CustomWebEnginePage(None, self)

        # Asetetaan standardi Chrome User-Agent videotoiston yhteensopivuudelle
        self._profile.setHttpUserAgent(CHROME_USER_AGENT)

        self.setPage(custom_page)
        
        # Määritetään selainmoottorin ja videotoiston asetukset
        self.apply_settings()

        # Linkin leijunnan tilarivisignaali (hover)
        self.page().linkHovered.connect(self._on_link_hovered)
        
        # Uuden ikkunan pyyntö -> uusi välilehti
        custom_page.new_tab_requested.connect(self._on_new_tab_requested)

        # Äänitilan seuranta
        self.page().recentlyAudibleChanged.connect(self._on_audio_state_changed)
        self.page().audioMutedChanged.connect(self._on_audio_state_changed)

        # Tallennetaan historiaan, kun sivu latautuu onnistuneesti (paitsi incognito-tilassa)
        self.loadFinished.connect(self._on_page_load_finished)

        self._zoom_factor = 1.0

    def apply_settings(self):
        """Päivitä asetukset ja optimoi videotoisto (HTML5, WebGL, Fullscreen)."""
        app_settings = SettingsManager.load_settings()
        js_enabled = app_settings.get("javascript_enabled", True)

        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, js_enabled)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, not self.is_incognito)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        
        # Video & Media -optimoinnit
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)

    def _on_link_hovered(self, url: str):
        self.status_message_changed.emit(url)

    def _on_new_tab_requested(self, url: QUrl):
        self.open_in_new_tab.emit(url)

    def _on_audio_state_changed(self):
        is_audible = self.page().recentlyAudible()
        is_muted = self.page().isAudioMuted()
        self.audio_state_changed.emit(is_audible, is_muted)

    def _on_page_load_finished(self, ok: bool):
        if ok and not self.is_incognito:
            title = self.title()
            url = self.url().toString()
            if not url.startswith("about:"):
                HistoryManager.add_entry(title, url)

    def load_speed_dial(self):
        """Lataa sisäänrakennetun aloitussivun."""
        settings = SettingsManager.load_settings()
        theme = settings.get("theme", "Dark")
        html = get_new_tab_html(theme)
        self.setHtml(html, QUrl("about:newtab"))

    def load_url(self, target: str):
        """Lataa annetun osoitteen tai suorittaa haun valitulla hakukoneella."""
        target = target.strip()
        if not target or target in ("about:newtab", "about:home", "about:blank"):
            self.load_speed_dial()
            return

        if target.startswith(("http://", "https://", "file://", "about:", "chrome://")):
            url = QUrl(target)
        elif "." in target and " " not in target:
            url = QUrl("https://" + target)
        else:
            template = SettingsManager.get_search_url_template()
            query = QUrl.toPercentEncoding(target).data().decode('utf-8')
            url = QUrl(template.replace("{query}", query))

        self.setUrl(url)

    def extract_page_text(self, callback):
        """Poimii sivun tekstisisallon asynkronisesti JavaScriptilla."""
        js = "document.body ? document.body.innerText : '';"
        self.page().runJavaScript(js, callback)

    def search_in_page(self, query: str, case_sensitive: bool = False, backward: bool = False):
        """Etsi tekstiä sivulta."""
        if not query:
            self.findText("")
            return

        flags = QWebEnginePage.FindFlag(0)
        if case_sensitive:
            flags |= QWebEnginePage.FindFlag.FindCaseSensitively
        if backward:
            flags |= QWebEnginePage.FindFlag.FindBackward

        self.findText(query, flags)

    def toggle_mute(self) -> bool:
        """Kytkee välilehden äänet päälle/pois."""
        muted = not self.page().isAudioMuted()
        self.page().setAudioMuted(muted)
        return muted

    def export_to_pdf(self, file_path: str, callback=None):
        """Tallentaa sivun PDF-tiedostoksi."""
        if callback:
            self.page().printToPdf(file_path)
            callback(file_path)
        else:
            self.page().printToPdf(file_path)

    def zoom_in(self) -> int:
        self._zoom_factor = min(3.0, round(self._zoom_factor + 0.1, 2))
        self.setZoomFactor(self._zoom_factor)
        return int(self._zoom_factor * 100)

    def zoom_out(self) -> int:
        self._zoom_factor = max(0.25, round(self._zoom_factor - 0.1, 2))
        self.setZoomFactor(self._zoom_factor)
        return int(self._zoom_factor * 100)

    def reset_zoom(self) -> int:
        self._zoom_factor = 1.0
        self.setZoomFactor(1.0)
        return 100

    def contextMenuEvent(self, event):
        """Oikean hiirennapin mukautettu valikko."""
        menu = self.createStandardContextMenu()
        menu.addSeparator()

        is_muted = self.page().isAudioMuted()
        mute_text = "🔊 Poista mykistys" if is_muted else "🔇 Mykistä välilehti"
        mute_action = menu.addAction(mute_text)
        mute_action.triggered.connect(self.toggle_mute)

        menu.addSeparator()
        inspect_action = menu.addAction("🛠️ Tarkasta elementti (Inspect)")
        inspect_action.triggered.connect(self._inspect_element)

        menu.exec(event.globalPos())

    def _inspect_element(self):
        self.page().triggerAction(QWebEnginePage.WebAction.InspectElement)
        self.inspect_element_requested.emit()
