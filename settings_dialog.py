"""
settings_dialog.py - Selaimen asetusten hallinta ja asetusikkuna (%APPDATA%)
"""

import json
import os
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app_paths import get_settings_file
from updater import APP_VERSION, UpdateManager

SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/?q={query}",
    "Google": "https://www.google.com/search?q={query}",
    "Bing": "https://www.bing.com/search?q={query}",
    "Ecosia": "https://www.ecosia.org/search?q={query}",
}

DEFAULT_SETTINGS = {
    "search_engine": "DuckDuckGo",
    "home_url": "about:newtab",
    "theme": "Dark",
    "javascript_enabled": True,
}


class SettingsManager:
    """Lukee ja tallentaa selaimen asetukset AppDataan."""

    @staticmethod
    def load_settings() -> dict:
        settings = dict(DEFAULT_SETTINGS)
        settings_file = get_settings_file()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    settings.update(saved)
            except Exception:
                pass
        return settings

    @staticmethod
    def save_settings(settings: dict):
        settings_file = get_settings_file()
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Asetusten tallennus epäonnistui: {e}")

    @classmethod
    def get_search_url_template(cls) -> str:
        settings = cls.load_settings()
        engine_name = settings.get("search_engine", "DuckDuckGo")
        return SEARCH_ENGINES.get(engine_name, SEARCH_ENGINES["DuckDuckGo"])


class SettingsDialog(QDialog):
    """Asetusikkuna käyttäjän muokkauksille ja päivitystarkistukselle."""
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selaimen asetukset")
        self.resize(500, 320)
        self.settings = SettingsManager.load_settings()
        self.update_manager = UpdateManager(self)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Oletushakukone
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(list(SEARCH_ENGINES.keys()))
        curr_engine = self.settings.get("search_engine", "DuckDuckGo")
        if curr_engine in SEARCH_ENGINES:
            self.engine_combo.setCurrentText(curr_engine)
        form_layout.addRow("Oletushakukone:", self.engine_combo)

        # Kotisivu
        self.home_input = QLineEdit()
        self.home_input.setText(self.settings.get("home_url", DEFAULT_SETTINGS["home_url"]))
        form_layout.addRow("Kotisivun osoite:", self.home_input)

        # Teema
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Dark"))
        form_layout.addRow("Ulkoasuteema:", self.theme_combo)

        # JavaScript
        self.js_checkbox = QCheckBox("Ota JavaScript käyttöön")
        self.js_checkbox.setChecked(self.settings.get("javascript_enabled", True))
        form_layout.addRow("Sivuskriptit:", self.js_checkbox)

        layout.addLayout(form_layout)

        # Tekoälyavustajan asetukset
        ai_group = QGroupBox("✨ Tekoälyavustajan asetukset (AI Sidebar)")
        ai_layout = QFormLayout(ai_group)

        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItem("Sisäänrakennettu (Paikallinen)", "local")
        self.ai_provider_combo.addItem("Ollama (http://localhost:11434)", "ollama")
        self.ai_provider_combo.addItem("Google Gemini API", "gemini")
        self.ai_provider_combo.addItem("OpenAI API", "openai")

        curr_provider = self.settings.get("ai_provider", "local")
        idx = self.ai_provider_combo.findData(curr_provider)
        if idx >= 0:
            self.ai_provider_combo.setCurrentIndex(idx)
        ai_layout.addRow("Tekoälymoottori:", self.ai_provider_combo)

        self.ai_key_input = QLineEdit()
        self.ai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key_input.setPlaceholderText("Valinnainen API-avain (Gemini/OpenAI)...")
        self.ai_key_input.setText(self.settings.get("ai_api_key", ""))
        ai_layout.addRow("API-avain:", self.ai_key_input)

        layout.addWidget(ai_group)

        # Versio & Päivitys -osio
        update_group = QGroupBox("Tietoja ja päivitykset")
        update_layout = QHBoxLayout(update_group)

        version_label = QLabel(f"Versio: <b>v{APP_VERSION}</b>")
        update_layout.addWidget(version_label)

        update_layout.addStretch()

        check_update_btn = QPushButton("Tarkista päivitykset")
        check_update_btn.clicked.connect(lambda: self.update_manager.check_for_updates(silent=False))
        update_layout.addWidget(check_update_btn)

        layout.addWidget(update_group)

        # Painikkeet (Tallenna / Peruuta)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _save_and_close(self):
        self.settings["search_engine"] = self.engine_combo.currentText()
        self.settings["home_url"] = self.home_input.text().strip() or DEFAULT_SETTINGS["home_url"]
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["javascript_enabled"] = self.js_checkbox.isChecked()
        self.settings["ai_provider"] = self.ai_provider_combo.currentData()
        self.settings["ai_api_key"] = self.ai_key_input.text().strip()

        SettingsManager.save_settings(self.settings)
        self.settings_saved.emit()
        self.accept()
