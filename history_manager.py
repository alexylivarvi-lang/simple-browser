"""
history_manager.py - Selaushistorian hallinta ja graafinen historia-dialogi (%APPDATA%)
"""

from datetime import datetime
import json
import os
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app_paths import get_history_file


class HistoryManager:
    """Hallitsee selaushistorian tallennusta ja hakua."""

    @staticmethod
    def load_history() -> list:
        history_file = get_history_file()
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    @staticmethod
    def save_history(history: list):
        history_file = get_history_file()
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Historian tallennus epäonnistui: {e}")

    @classmethod
    def add_entry(cls, title: str, url: str):
        if not url or url.startswith("about:"):
            return

        history = cls.load_history()
        # Vältetään identtisen peräkkäisen sivun toistaminen
        if history and history[0].get("url") == url:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "title": title or url,
            "url": url,
            "timestamp": timestamp,
        }
        history.insert(0, entry)
        cls.save_history(history[:2000])

    @classmethod
    def clear_history(cls):
        cls.save_history([])


class HistoryDialog(QDialog):
    """Historiaikkuna, josta voi selata, etsiä ja avata menneitä sivuja."""
    open_url_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selaushistoria")
        self.resize(750, 480)
        self._all_history = HistoryManager.load_history()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Yläpalkki: Etsintä ja toiminnot
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Etsi historiasta...")
        self.search_input.textChanged.connect(self._filter_history)
        top_layout.addWidget(self.search_input)

        self.clear_btn = QPushButton("Tyhjennä historia")
        self.clear_btn.clicked.connect(self._clear_history)
        top_layout.addWidget(self.clear_btn)

        layout.addLayout(top_layout)

        # Historiataulukko
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Aika", "Sivun otsikko", "Osoite (URL)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        self._populate_table(self._all_history)

    def _populate_table(self, items: list):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            time_item = QTableWidgetItem(item.get("timestamp", ""))
            title_item = QTableWidgetItem(item.get("title", ""))
            url_item = QTableWidgetItem(item.get("url", ""))

            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, title_item)
            self.table.setItem(row, 2, url_item)

    def _filter_history(self, query: str):
        query = query.lower().strip()
        if not query:
            self._populate_table(self._all_history)
            return

        filtered = [
            item for item in self._all_history
            if query in item.get("title", "").lower() or query in item.get("url", "").lower()
        ]
        self._populate_table(filtered)

    def _on_row_double_clicked(self, index):
        row = index.row()
        url_item = self.table.item(row, 2)
        if url_item:
            url = url_item.text()
            self.open_url_requested.emit(url)
            self.accept()

    def _clear_history(self):
        reply = QMessageBox.question(
            self,
            "Tyhjennä historia",
            "Haluatko varmasti poistaa koko selaushistorian?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            HistoryManager.clear_history()
            self._all_history = []
            self._populate_table([])
