"""Main URLift desktop window."""

from __future__ import annotations

from pathlib import Path

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
from app.theme import APP_STYLESHEET
from app.worker import DownloadRequest, DownloadWorker
from downloader.config import default_download_dir
from downloader.formats import M4A_AUDIO, MP3_AUDIO, VIDEO_1080P, VIDEO_480P, VIDEO_720P, VIDEO_BEST
from downloader.validators import PLATFORMS, validate_output_dir, validate_url
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
        self.worker: DownloadWorker | None = None

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
        self.video_radio.toggled.connect(lambda _checked: self._set_quality_options())

        self.quality_combo = QComboBox()

        download_dir = default_download_dir()
        download_dir.mkdir(parents=True, exist_ok=True)
        self.output_folder_input = QLineEdit(str(download_dir))
        self.output_folder_input.setPlaceholderText("Choose an output folder")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output_folder)
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_input, 1)
        output_folder_layout.addWidget(self.browse_button)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("PrimaryButton")
        self.download_button.clicked.connect(self.start_download)

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

    def start_download(self) -> None:
        platform = self.platform_combo.currentText()
        url = self.url_input.text().strip()
        output_type = self._selected_output_type()
        quality = self.quality_combo.currentText()
        output_dir = self.output_folder_input.text().strip()

        url_valid, url_error = validate_url(url, platform)
        if not url_valid:
            self._record_failed_attempt(platform, url, output_type, quality, url_error)
            self._set_status(url_error)
            return

        folder_valid, folder_error = validate_output_dir(output_dir)
        if not folder_valid:
            self._record_failed_attempt(platform, url, output_type, quality, folder_error)
            self._set_status(folder_error)
            return

        request = DownloadRequest(
            platform=platform,
            url=url,
            output_type=output_type,
            quality=quality,
            output_dir=Path(output_dir),
        )
        self.worker = DownloadWorker(request)
        self.worker.progress.connect(self._on_download_progress)
        self.worker.completed.connect(self._on_download_completed)
        self.worker.failed.connect(self._on_download_failed)
        self.worker.finished.connect(self._on_worker_finished)

        self._set_busy(True)
        self._set_status("Checking URL")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.worker.start()

    def _selected_output_type(self) -> str:
        return "Audio only" if self.audio_radio.isChecked() else "Video"

    def _on_download_progress(self, status: str, percent: float | None, message: str) -> None:
        self._set_status(status if status else message)
        if percent is None:
            self.progress_bar.setRange(0, 0)
            return
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(percent))

    def _on_download_completed(self, payload: dict) -> None:
        self.repository.add_entry(
            platform=payload["platform"],
            original_url=payload["url"],
            media_title=payload["title"],
            output_type=payload["output_type"],
            selected_quality=payload["quality"],
            saved_file_path=payload["file_path"],
            file_extension=payload["extension"],
            status="completed",
        )
        self.history_view.refresh()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self._set_status("Completed")

    def _on_download_failed(self, payload: dict) -> None:
        status = payload.get("status") or "Failed"
        error = payload.get("error") or status
        self.repository.add_entry(
            platform=payload["platform"],
            original_url=payload["url"],
            media_title=payload.get("title") or "(unknown)",
            output_type=payload["output_type"],
            selected_quality=payload["quality"],
            saved_file_path=payload.get("file_path") or "",
            file_extension=payload.get("extension") or "",
            status="failed",
            error_message=error,
        )
        self.history_view.refresh()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._set_status(status)

    def _on_worker_finished(self) -> None:
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self._set_busy(False)

    def _record_failed_attempt(
        self,
        platform: str,
        url: str,
        output_type: str,
        quality: str,
        error: str,
    ) -> None:
        self.repository.add_entry(
            platform=platform,
            original_url=url or "(empty)",
            media_title="(not downloaded)",
            output_type=output_type,
            selected_quality=quality,
            status="failed",
            error_message=error,
        )
        self.history_view.refresh()

    def _set_busy(self, busy: bool) -> None:
        self.platform_combo.setEnabled(not busy)
        self.url_input.setEnabled(not busy)
        self.video_radio.setEnabled(not busy)
        self.audio_radio.setEnabled(not busy)
        self.quality_combo.setEnabled(not busy)
        self.output_folder_input.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.download_button.setEnabled(not busy)
        self.download_button.setText("Downloading" if busy else "Download")

    def _set_status(self, status: str) -> None:
        self.status_label.setText(status)

    def _apply_style(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)
