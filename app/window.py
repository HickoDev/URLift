"""Main URLift desktop window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.history_view import HistoryView
from downloader.config import default_download_dir
from downloader.formats import M4A_AUDIO, MP3_AUDIO, VIDEO_1080P, VIDEO_480P, VIDEO_720P, VIDEO_BEST
from downloader.validators import PLATFORMS
from storage.history_repository import HistoryRepository


LEGAL_NOTE = (
    "Use URLift only for your own content, royalty-free content, or public content "
    "you have permission to download. URLift does not bypass DRM, paid access, "
    "private accounts, login walls, or platform restrictions."
)


class URLiftWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.repository = HistoryRepository()

        self.setWindowTitle("URLift")
        self.resize(980, 680)

        self.tabs = QTabWidget()
        self.download_tab = self._build_download_tab()
        self.history_view = HistoryView(self.repository)
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.history_view, "History")

        self.setCentralWidget(self.tabs)
        self._apply_style()
        self._set_quality_options()

    def _build_download_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("URLift")
        title.setObjectName("Title")
        subtitle = QLabel("Download authorized or public media with yt-dlp.")
        subtitle.setObjectName("Subtitle")

        note = QLabel(LEGAL_NOTE)
        note.setObjectName("LegalNote")
        note.setWordWrap(True)

        form_frame = QFrame()
        form_frame.setObjectName("FormFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(12)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(PLATFORMS)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a media URL")

        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio only")
        self.video_radio.setChecked(True)
        output_type_layout = QHBoxLayout()
        output_type_layout.addWidget(self.video_radio)
        output_type_layout.addWidget(self.audio_radio)
        output_type_layout.addStretch(1)
        self.video_radio.toggled.connect(self._set_quality_options)

        self.quality_combo = QComboBox()

        self.output_folder_input = QLineEdit(str(default_download_dir()))
        self.output_folder_input.setPlaceholderText("Choose an output folder")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output_folder)
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_input, 1)
        output_folder_layout.addWidget(self.browse_button)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("PrimaryButton")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")

        form_layout.addRow("Platform", self.platform_combo)
        form_layout.addRow("URL", self.url_input)
        form_layout.addRow("Output type", output_type_layout)
        form_layout.addRow("Quality / format", self.quality_combo)
        form_layout.addRow("Output folder", output_folder_layout)
        form_layout.addRow("", self.download_button)
        form_layout.addRow("Progress", self.progress_bar)
        form_layout.addRow("Status", self.status_label)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(note)
        layout.addWidget(form_frame)
        layout.addStretch(1)
        return tab

    def _set_quality_options(self) -> None:
        current = self.quality_combo.currentText() if hasattr(self, "quality_combo") else ""
        self.quality_combo.clear()
        if self.video_radio.isChecked():
            options = (VIDEO_BEST, VIDEO_1080P, VIDEO_720P, VIDEO_480P)
        else:
            options = (MP3_AUDIO, M4A_AUDIO)
        self.quality_combo.addItems(options)
        if current in options:
            self.quality_combo.setCurrentText(current)

    def browse_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.output_folder_input.text(),
        )
        if folder:
            self.output_folder_input.setText(folder)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f7f9;
            }
            QLabel#Title {
                font-size: 28px;
                font-weight: 700;
                color: #15171a;
            }
            QLabel#Subtitle {
                color: #4c5563;
                font-size: 13px;
            }
            QLabel#LegalNote {
                background: #fff7e6;
                border: 1px solid #f1c36d;
                border-radius: 6px;
                color: #4c3513;
                padding: 10px;
            }
            QFrame#FormFrame {
                background: #ffffff;
                border: 1px solid #d9dee7;
                border-radius: 8px;
                padding: 16px;
            }
            QPushButton#PrimaryButton {
                background: #1665d8;
                color: #ffffff;
                border: 0;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: 600;
            }
            QPushButton#PrimaryButton:disabled {
                background: #94a3b8;
            }
            QLabel#StatusLabel {
                color: #1f2937;
                font-weight: 600;
            }
            """
        )
