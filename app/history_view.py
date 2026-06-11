"""History table and actions for URLift."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from storage.history_repository import HistoryItem, HistoryRepository


class HistoryView(QWidget):
    """Widget that displays and manages persisted download history."""

    COLUMNS = ("Date", "Platform", "Title", "Format", "Status", "File path")

    def __init__(self, repository: HistoryRepository) -> None:
        super().__init__()
        self.repository = repository
        self.items: list[HistoryItem] = []

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(360)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        self.open_file_button = QPushButton("Open file")
        self.open_folder_button = QPushButton("Open folder")
        self.copy_url_button = QPushButton("Copy original URL")
        self.remove_button = QPushButton("Remove item")
        self.clear_button = QPushButton("Clear all history")
        self.remove_button.setObjectName("DangerButton")
        self.clear_button.setObjectName("DangerButton")

        self.open_file_button.clicked.connect(self.open_selected_file)
        self.open_folder_button.clicked.connect(self.open_selected_folder)
        self.copy_url_button.clicked.connect(self.copy_selected_url)
        self.remove_button.clicked.connect(self.remove_selected_item)
        self.clear_button.clicked.connect(self.clear_history)

        actions = QHBoxLayout()
        actions.addWidget(self.open_file_button)
        actions.addWidget(self.open_folder_button)
        actions.addWidget(self.copy_url_button)
        actions.addStretch(1)
        actions.addWidget(self.remove_button)
        actions.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(self.table)
        layout.addLayout(actions)

        self.refresh()

    def refresh(self) -> None:
        self.items = self.repository.fetch_all()
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            values = (
                _display_date(item.downloaded_at),
                item.platform,
                item.media_title or "(unknown)",
                item.selected_quality,
                item.status,
                item.saved_file_path,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(Qt.UserRole, item.id)
                cell.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if column == 4:
                    color = "#23a559" if item.status == "completed" else "#f23f43"
                    cell.setForeground(QColor(color))
                if item.error_message:
                    cell.setToolTip(item.error_message)
                self.table.setItem(row, column, cell)

    def selected_item(self) -> HistoryItem | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.items):
            return None
        return self.items[row]

    def open_selected_file(self) -> None:
        item = self.selected_item()
        if not item:
            return

        path = Path(item.saved_file_path)
        if not path.is_file():
            QMessageBox.warning(self, "URLift", "The saved file could not be found.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_selected_folder(self) -> None:
        item = self.selected_item()
        if not item:
            return

        if not item.saved_file_path:
            QMessageBox.warning(self, "URLift", "This history item has no saved file path.")
            return

        path = Path(item.saved_file_path)
        folder = path.parent if path.parent.exists() else None
        if not folder:
            QMessageBox.warning(self, "URLift", "The saved folder could not be found.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def copy_selected_url(self) -> None:
        item = self.selected_item()
        if item:
            QApplication.clipboard().setText(item.original_url)

    def remove_selected_item(self) -> None:
        item = self.selected_item()
        if not item:
            return
        self.repository.delete_item(item.id)
        self.refresh()

    def clear_history(self) -> None:
        if not self.items:
            return

        result = QMessageBox.question(
            self,
            "Clear history",
            "Remove all download history entries?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.repository.clear()
            self.refresh()


def _display_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d %H:%M")
