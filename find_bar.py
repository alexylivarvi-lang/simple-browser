"""
find_bar.py - Sivun sisäinen haku (Find in Page, Ctrl+F)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QWidget,
)


class FindBar(QWidget):
    """Sivun sisäinen hakupalkki (Ctrl+F)."""
    search_requested = pyqtSignal(str, bool, bool)  # (query, case_sensitive, backward)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        # Hakukenttä
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Etsi sivulta...")
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self.find_next)
        layout.addWidget(self.search_input)

        # Edellinen
        self.prev_btn = QToolButton()
        self.prev_btn.setText("▲")
        self.prev_btn.setToolTip("Edellinen osuma (Shift+Enter)")
        self.prev_btn.clicked.connect(self.find_prev)
        layout.addWidget(self.prev_btn)

        # Seuraava
        self.next_btn = QToolButton()
        self.next_btn.setText("▼")
        self.next_btn.setToolTip("Seuraava osuma (Enter)")
        self.next_btn.clicked.connect(self.find_next)
        layout.addWidget(self.next_btn)

        # Isot ja pienet kirjaimet
        self.case_box = QCheckBox("Aa")
        self.case_box.setToolTip("Huomioi isot ja pienet kirjaimet")
        self.case_box.stateChanged.connect(lambda: self._on_text_changed(self.search_input.text()))
        layout.addWidget(self.case_box)

        # Sulje
        self.close_btn = QToolButton()
        self.close_btn.setText("✕")
        self.close_btn.setToolTip("Sulje haku (Esc)")
        self.close_btn.clicked.connect(self.close_bar)
        layout.addWidget(self.close_btn)

    def show_bar(self):
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()
        if self.search_input.text():
            self.find_next()

    def close_bar(self):
        self.hide()
        self.closed.emit()

    def _on_text_changed(self, text: str):
        case_sensitive = self.case_box.isChecked()
        self.search_requested.emit(text, case_sensitive, False)

    def find_next(self):
        text = self.search_input.text()
        case_sensitive = self.case_box.isChecked()
        self.search_requested.emit(text, case_sensitive, False)

    def find_prev(self):
        text = self.search_input.text()
        case_sensitive = self.case_box.isChecked()
        self.search_requested.emit(text, case_sensitive, True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        else:
            super().keyPressEvent(event)
