"""Application stylesheet for URLift."""

from __future__ import annotations


APP_STYLESHEET = """
QWidget {
    background: #313338;
    color: #dbdee1;
    font-size: 13px;
}

QMainWindow,
QTabWidget::pane {
    background: #313338;
    border: 0;
}

QTabBar::tab {
    background: #2b2d31;
    color: #b5bac1;
    padding: 10px 18px;
    border: 0;
    min-width: 92px;
}

QTabBar::tab:selected {
    background: #313338;
    color: #ffffff;
    border-bottom: 3px solid #5865f2;
}

QTabBar::tab:hover:!selected {
    background: #35373c;
    color: #ffffff;
}

QLabel {
    background: transparent;
    color: #dbdee1;
}

QLabel#Title {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#Subtitle {
    color: #b5bac1;
    font-size: 14px;
}

QLabel#StatusLabel {
    background: #1e1f22;
    border: 1px solid #3f4147;
    border-radius: 14px;
    color: #dbdee1;
    font-weight: 700;
    padding: 6px 12px;
}

QLabel#StatusLabel[state="success"],
QLabel#StatusLabel[state="ready"] {
    color: #23a559;
}

QLabel#StatusLabel[state="active"] {
    color: #f0b232;
}

QLabel#StatusLabel[state="error"] {
    color: #f23f43;
}

QLabel#LegalNote {
    background: #3f3420;
    border: 1px solid #8f6a24;
    border-radius: 8px;
    color: #f0d7a1;
    padding: 12px;
}

QFrame#FormFrame {
    background: #2b2d31;
    border: 1px solid #1e1f22;
    border-radius: 8px;
    padding: 18px;
}

QFrame#PreviewFrame {
    background: #1e1f22;
    border: 1px solid #3f4147;
    border-radius: 8px;
}

QLabel#PreviewThumbnail {
    background: #111214;
    border: 1px solid #3f4147;
    border-radius: 6px;
}

QLabel#PreviewTitle {
    color: #ffffff;
    font-weight: 700;
}

QLabel#MutedLabel {
    color: #949ba4;
}

QLabel#SectionTitle {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

QFrame#QueueFrame {
    background: #2b2d31;
    border: 1px solid #1e1f22;
    border-radius: 8px;
}

QLineEdit,
QComboBox {
    background: #1e1f22;
    border: 1px solid #3f4147;
    border-radius: 6px;
    color: #f2f3f5;
    padding: 0 10px;
    selection-background-color: #5865f2;
}

QLineEdit:focus,
QComboBox:focus {
    border: 1px solid #5865f2;
}

QLineEdit:disabled,
QComboBox:disabled {
    background: #2b2d31;
    color: #80848e;
}

QComboBox QAbstractItemView {
    background: #1e1f22;
    border: 1px solid #3f4147;
    color: #f2f3f5;
    selection-background-color: #5865f2;
    selection-color: #ffffff;
    outline: 0;
}

QRadioButton {
    background: transparent;
    color: #dbdee1;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:unchecked {
    border: 2px solid #6d717c;
    border-radius: 8px;
    background: #1e1f22;
}

QRadioButton::indicator:checked {
    border: 4px solid #5865f2;
    border-radius: 8px;
    background: #ffffff;
}

QPushButton {
    background: #4e5058;
    border: 0;
    border-radius: 6px;
    color: #ffffff;
    padding: 0 14px;
}

QPushButton:hover {
    background: #5c5f68;
}

QPushButton:pressed {
    background: #3f4147;
}

QPushButton:disabled {
    background: #3a3c42;
    color: #80848e;
}

QPushButton#PrimaryButton {
    background: #5865f2;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background: #4752c4;
}

QPushButton#DangerButton {
    background: #da373c;
}

QPushButton#DangerButton:hover {
    background: #a12828;
}

QProgressBar {
    background: #1e1f22;
    border: 1px solid #3f4147;
    border-radius: 6px;
    color: #ffffff;
    text-align: center;
}

QProgressBar::chunk {
    background: #23a559;
    border-radius: 5px;
}

QTableWidget {
    background: #2b2d31;
    alternate-background-color: #26282d;
    border: 1px solid #1e1f22;
    border-radius: 8px;
    color: #dbdee1;
    gridline-color: #3f4147;
    selection-background-color: #5865f2;
    selection-color: #ffffff;
}

QHeaderView::section {
    background: #1e1f22;
    border: 0;
    border-right: 1px solid #3f4147;
    color: #b5bac1;
    font-weight: 700;
    padding: 8px;
}

QMessageBox {
    background: #313338;
}
"""
