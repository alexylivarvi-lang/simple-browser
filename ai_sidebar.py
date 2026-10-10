"""
ai_sidebar.py - SimpleBrowserin Tekoäly-sivupaneeli (AI Sidebar)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ai_engine import AIWorker


class AISidebar(QWidget):
    """Selaimen oikeaan reunaan kiinnittyvä tekoälypaneeli."""
    close_requested = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.worker = None
        self._current_page_text = ""

        self.setMinimumWidth(280)
        self.setMaximumWidth(600)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. Yläpalkki (Otsikko, tila ja sulkemisnappi)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("✨ Tekoälyavustaja")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.btn_clear = QPushButton("🗑️")
        self.btn_clear.setToolTip("Tyhjennä keskustelu")
        self.btn_clear.setFixedSize(28, 28)
        self.btn_clear.clicked.connect(self.clear_chat)
        header_layout.addWidget(self.btn_clear)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Sulje paneeli (Ctrl+Space)")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(self.btn_close)

        layout.addLayout(header_layout)

        # 2. Pikatoimintonapit (Quick action chips)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        self.btn_summarize = QPushButton("📄 Tiivistä")
        self.btn_summarize.setToolTip("Luo tiivistelmä aktiivisesta sivusta")
        self.btn_summarize.clicked.connect(lambda: self._trigger_action("summarize", "Tiivistä tämä sivu"))

        self.btn_facts = QPushButton("🔑 Faktat")
        self.btn_facts.setToolTip("Etsi tärkeimmät luvut ja faktat")
        self.btn_facts.clicked.connect(lambda: self._trigger_action("key_points", "Etsi tärkeimmät faktat"))

        self.btn_translate = QPushButton("🌐 Käännä")
        self.btn_translate.setToolTip("Käännä pääsisältö suomeksi")
        self.btn_translate.clicked.connect(lambda: self._trigger_action("translate", "Käännä suomeksi"))

        self.btn_explain = QPushButton("💡 Selitä")
        self.btn_explain.setToolTip("Selitä sivu selkokielellä")
        self.btn_explain.clicked.connect(lambda: self._trigger_action("explain", "Selitä selkokielellä"))

        for btn in [self.btn_summarize, self.btn_facts, self.btn_translate, self.btn_explain]:
            btn.setFixedHeight(30)
            actions_layout.addWidget(btn)

        layout.addLayout(actions_layout)

        # 3. Keskustelualue (Chat / Output)
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setFont(QFont("Segoe UI", 9))
        self.chat_display.setPlaceholderText("Valitse yläpuolelta toiminto tai kysy jotain avoimesta sivusta...")
        layout.addWidget(self.chat_display)

        # 4. Tilatieto / Latausindikaattori
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #708bff; font-style: italic;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # 5. Syöttökenttä alareunassa
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Kysy jotain tästä sivusta...")
        self.input_field.setFixedHeight(36)
        self.input_field.returnPressed.connect(self._send_custom_prompt)
        input_layout.addWidget(self.input_field)

        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(36, 36)
        self.btn_send.setToolTip("Lähetä viesti")
        self.btn_send.clicked.connect(self._send_custom_prompt)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

    def _apply_style(self):
        self.setStyleSheet("""
            AISidebar {
                background-color: #1a1b24;
                border-left: 1px solid rgba(255, 255, 255, 0.08);
            }
            QLabel {
                color: #f5f6fa;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #f5f6fa;
                border-radius: 6px;
                font-size: 8pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(67, 97, 238, 0.2);
                border-color: #4361ee;
            }
            QPushButton:pressed {
                background-color: #4361ee;
            }
            QTextBrowser {
                background-color: #12131a;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                color: #e2e8f0;
                padding: 10px;
                line-height: 1.5;
            }
            QLineEdit {
                background-color: #12131a;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: #f5f6fa;
                padding: 0 10px;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border-color: #4361ee;
            }
        """)

    def _trigger_action(self, mode: str, user_prompt: str):
        self._add_chat_bubble("user", user_prompt)
        self._fetch_active_page_and_run(mode, user_prompt)

    def _send_custom_prompt(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._add_chat_bubble("user", text)
        self._fetch_active_page_and_run("chat", text)

    def _fetch_active_page_and_run(self, mode: str, prompt: str):
        self._set_loading(True, "🤖 Luetaan sivun sisältöä...")

        # Pyydetään aktiiviselta välilehdeltä sivun teksti
        current_tab = self.main_window.get_current_tab()
        if not current_tab:
            self._set_loading(False)
            self._add_chat_bubble("ai", "Ei aktiivista välilehteä.")
            return

        def on_text_extracted(page_text: str):
            self._set_loading(True, "🤖 Analysoidaan tekstiä...")
            self._start_worker(mode, prompt, page_text)

        current_tab.extract_page_text(on_text_extracted)

    def _start_worker(self, mode: str, prompt: str, page_text: str):
        self.worker = AIWorker(mode, prompt, page_text)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_finished(self, response: str):
        self._set_loading(False)
        self._add_chat_bubble("ai", response)

    def _on_worker_error(self, err_msg: str):
        self._set_loading(False)
        self._add_chat_bubble("ai", f"❌ {err_msg}")

    def _add_chat_bubble(self, sender: str, text: str):
        current_html = self.chat_display.toHtml()
        
        if sender == "user":
            bubble = f"""
            <div style="margin: 8px 0; text-align: right;">
                <span style="background-color: #4361ee; color: white; padding: 6px 12px; border-radius: 12px; display: inline-block; font-size: 13px;">
                    {text}
                </span>
            </div>
            """
        else:
            # Muutetaan markdown perus HTML-muotoon
            formatted_text = text.replace("\n", "<br>")
            bubble = f"""
            <div style="margin: 8px 0; background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); padding: 10px; border-radius: 10px; color: #f1f5f9; font-size: 13px;">
                {formatted_text}
            </div>
            """

        self.chat_display.append(bubble)

    def _set_loading(self, loading: bool, message: str = ""):
        self.status_label.setVisible(loading)
        self.status_label.setText(message)
        self.btn_send.setEnabled(not loading)
        self.btn_summarize.setEnabled(not loading)
        self.btn_facts.setEnabled(not loading)
        self.btn_translate.setEnabled(not loading)
        self.btn_explain.setEnabled(not loading)

    def clear_chat(self):
        self.chat_display.clear()
        self._set_loading(False)
