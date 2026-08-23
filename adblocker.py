"""
adblocker.py - Mainosten ja seurannan esto (AdBlock & Tracker Shield)
"""

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor


# Yleisimmät mainos- ja seurantaverkkotunnukset
DEFAULT_BLOCKED_DOMAINS = {
    # Mainosverkot
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "adservice.google.com",
    "adnxs.com",
    "criteo.com",
    "outbrain.com",
    "taboola.com",
    "pubmatic.com",
    "rubiconproject.com",
    "openx.net",
    "amazon-adsystem.com",
    "adroll.com",
    "bidswitch.net",
    "adform.net",
    "smartadserver.com",
    "zemanta.com",
    "revcontent.com",
    "mgid.com",
    
    # Seuranta & telemetria
    "google-analytics.com",
    "analytics.google.com",
    "scorecardresearch.com",
    "hotjar.com",
    "facebook.net",
    "connect.facebook.net",
    "pixel.facebook.com",
    "clarity.ms",
    "segment.io",
    "quantserve.com",
    "newrelic.com",
    "matomo.cloud",
}


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    """Sieppaa ja estää mainos- sekä seurantapyynnöt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked_count = 0
        self.blocked_domains = set(DEFAULT_BLOCKED_DOMAINS)
        self.on_blocked_callback = None

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not self.enabled:
            return

        url = info.requestUrl().toString().lower()
        host = info.requestUrl().host().lower()

        # Tarkistetaan kuuluuko palvelin estolistalle
        is_blocked = False
        for domain in self.blocked_domains:
            if host == domain or host.endswith("." + domain):
                is_blocked = True
                break

        if is_blocked:
            info.block(True)
            self.blocked_count += 1
            if self.on_blocked_callback:
                self.on_blocked_callback(self.blocked_count, url)

    def toggle(self) -> bool:
        """Kytkee mainoseston päälle/pois."""
        self.enabled = not self.enabled
        return self.enabled

    def reset_counter(self):
        self.blocked_count = 0
