"""Main URLift desktop window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QHeaderView,
    QSizePolicy,
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.history_view import HistoryView
from app.resources import resource_path
from app.theme import APP_STYLESHEET
from app.worker import DownloadRequest, DownloadWorker, PreviewWorker
from downloader.config import default_download_dir
from downloader.formats import M4A_AUDIO, MP3_AUDIO, VIDEO_1080P, VIDEO_480P, VIDEO_720P, VIDEO_BEST
from downloader.validators import PLATFORMS, validate_output_dir, validate_url
from storage.history_repository import HistoryItem
from storage.history_repository import HistoryRepository
from storage.settings_repository import AppSettings, SettingsRepository


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
        self.settings_repository = SettingsRepository()
        self.settings = self.settings_repository.load()
        self.worker: DownloadWorker | None = None
        self.preview_worker: PreviewWorker | None = None
        self.queue: list[DownloadRequest] = []
        self.queue_active = False

        self.setWindowTitle("URLift")
        self.resize(980, 680)

        self.tabs = QTabWidget()
        self.download_tab = self._build_download_tab()
        self.history_view = HistoryView(self.repository)
        self.history_view.retry_requested.connect(self.retry_history_item)
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.history_view, "History")

        self.setCentralWidget(self.tabs)
        self._apply_style()
        self._set_quality_options()
        self._apply_settings()
        self._connect_settings_signals()
        self._set_status("Ready")

    def _build_download_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        header_layout.setAlignment(Qt.AlignLeft)

        logo_label = QLabel()
        logo_label.setFixedSize(58, 58)
        logo_pixmap = QPixmap(str(resource_path("Logo.png")))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    logo_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

        title = QLabel("URLift")
        title.setObjectName("Title")
        subtitle = QLabel("Authorized media downloader")
        subtitle.setObjectName("Subtitle")

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)

        note = QLabel(LEGAL_NOTE)
        note.setObjectName("LegalNote")
        note.setWordWrap(True)

        form_frame = QFrame()
        form_frame.setObjectName("FormFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(16)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(PLATFORMS)
        self.platform_combo.setMinimumWidth(420)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a media URL")
        self.url_input.setMinimumWidth(420)
        self.paste_button = QPushButton("Paste")
        self.paste_button.clicked.connect(self.paste_url)
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_url)
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_input, 1)
        url_layout.addWidget(self.paste_button)
        url_layout.addWidget(self.preview_button)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PreviewFrame")
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(4)
        self.preview_title_label = QLabel("No preview loaded")
        self.preview_title_label.setObjectName("PreviewTitle")
        self.preview_title_label.setWordWrap(True)
        self.preview_detail_label = QLabel("Paste a URL and click Preview.")
        self.preview_detail_label.setObjectName("MutedLabel")
        self.preview_detail_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_title_label)
        preview_layout.addWidget(self.preview_detail_label)

        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio only")
        self.video_radio.setChecked(True)
        output_type_layout = QHBoxLayout()
        output_type_layout.addWidget(self.video_radio)
        output_type_layout.addWidget(self.audio_radio)
        output_type_layout.addStretch(1)
        self.video_radio.toggled.connect(lambda _checked: self._set_quality_options())

        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(420)

        download_dir = Path(self.settings.default_output_folder or str(default_download_dir()))
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
        self.download_button.setMinimumWidth(160)
        self.download_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("DangerButton")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.add_queue_button = QPushButton("Add to queue")
        self.add_queue_button.clicked.connect(self.add_current_to_queue)
        self.start_queue_button = QPushButton("Start queue")
        self.start_queue_button.clicked.connect(self.start_queue)
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.download_button)
        action_layout.addWidget(self.add_queue_button)
        action_layout.addWidget(self.start_queue_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addStretch(1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.open_file_check = QCheckBox("Open file when complete")
        self.open_folder_check = QCheckBox("Open folder when complete")
        after_download_layout = QHBoxLayout()
        after_download_layout.addWidget(self.open_file_check)
        after_download_layout.addWidget(self.open_folder_check)
        after_download_layout.addStretch(1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumWidth(130)

        form_layout.addRow("Platform", self.platform_combo)
        form_layout.addRow("URL", url_layout)
        form_layout.addRow("Preview", self.preview_frame)
        form_layout.addRow("Output type", output_type_layout)
        form_layout.addRow("Quality / format", self.quality_combo)
        form_layout.addRow("Output folder", output_folder_layout)
        form_layout.addRow("After download", after_download_layout)
        form_layout.addRow("", action_layout)
        form_layout.addRow("Progress", self.progress_bar)
        form_layout.addRow("Status", self.status_label)

        form_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        queue_frame = self._build_queue_frame()
        layout.addLayout(header_layout)
        layout.addWidget(note)
        layout.addWidget(form_frame)
        layout.addWidget(queue_frame)
        layout.addStretch(1)
        return tab

    def _build_queue_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("QueueFrame")

        title = QLabel("Queue")
        title.setObjectName("SectionTitle")

        self.queue_table = QTableWidget(0, 4)
        self.queue_table.setHorizontalHeaderLabels(("Platform", "URL", "Format", "Folder"))
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setShowGrid(False)
        self.queue_table.setMinimumHeight(130)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.verticalHeader().setDefaultSectionSize(34)
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.remove_queue_button = QPushButton("Remove")
        self.clear_queue_button = QPushButton("Clear queue")
        self.remove_queue_button.setObjectName("DangerButton")
        self.clear_queue_button.setObjectName("DangerButton")
        self.remove_queue_button.clicked.connect(self.remove_selected_queue_item)
        self.clear_queue_button.clicked.connect(self.clear_queue)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.remove_queue_button)
        actions.addWidget(self.clear_queue_button)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(self.queue_table)
        layout.addLayout(actions)
        self._refresh_queue()
        return frame

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
            self._save_settings()

    def paste_url(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)

    def preview_url(self) -> None:
        if self.preview_worker is not None:
            return

        platform = self.platform_combo.currentText()
        url = self.url_input.text().strip()
        url_valid, url_error = validate_url(url, platform)
        if not url_valid:
            self._set_preview("Preview unavailable", url_error)
            self._set_status(url_error)
            return

        self.preview_worker = PreviewWorker(url)
        self.preview_worker.completed.connect(self._on_preview_completed)
        self.preview_worker.failed.connect(self._on_preview_failed)
        self.preview_worker.finished.connect(self._on_preview_finished)
        self.preview_button.setEnabled(False)
        self._set_preview("Checking URL", "Loading media details...")
        self._set_status("Checking URL")
        self.preview_worker.start()

    def start_download(self) -> None:
        request = self._current_request(record_errors=True)
        if not request:
            return
        self.queue_active = False
        self._start_worker(request)

    def add_current_to_queue(self) -> None:
        request = self._current_request(record_errors=False)
        if not request:
            return
        self.queue.append(request)
        self._refresh_queue()
        self._set_status("Ready")

    def start_queue(self) -> None:
        if self.worker or not self.queue:
            return
        self.queue_active = True
        request = self.queue.pop(0)
        self._refresh_queue()
        self._start_worker(request)

    def remove_selected_queue_item(self) -> None:
        row = self.queue_table.currentRow()
        if row < 0 or row >= len(self.queue):
            return
        del self.queue[row]
        self._refresh_queue()

    def clear_queue(self) -> None:
        self.queue.clear()
        self._refresh_queue()

    def retry_history_item(self, item: HistoryItem) -> None:
        output_dir = default_download_dir()
        if item.saved_file_path:
            saved_parent = Path(item.saved_file_path).parent
            if saved_parent.exists():
                output_dir = saved_parent
        output_dir.mkdir(parents=True, exist_ok=True)

        platform = item.platform if item.platform in PLATFORMS else "Other / Auto-detect"
        self.platform_combo.setCurrentText(platform)
        self.url_input.setText(item.original_url)
        self.audio_radio.setChecked(item.output_type == "Audio only")
        self.video_radio.setChecked(item.output_type != "Audio only")
        self._set_quality_options()
        if item.selected_quality:
            self.quality_combo.setCurrentText(item.selected_quality)
        self.output_folder_input.setText(str(output_dir))
        self.tabs.setCurrentWidget(self.download_tab)
        self._save_settings()

        request = DownloadRequest(
            platform=platform,
            url=item.original_url,
            output_type=item.output_type,
            quality=item.selected_quality,
            output_dir=output_dir,
        )
        if self.worker is not None:
            self.queue.append(request)
            self._refresh_queue()
            self._set_status("Ready")
            return
        self.queue_active = False
        self._start_worker(request)

    def _current_request(self, record_errors: bool) -> DownloadRequest | None:
        platform = self.platform_combo.currentText()
        url = self.url_input.text().strip()
        output_type = self._selected_output_type()
        quality = self.quality_combo.currentText()
        output_dir = self.output_folder_input.text().strip()

        url_valid, url_error = validate_url(url, platform)
        if not url_valid:
            if record_errors:
                self._record_failed_attempt(platform, url, output_type, quality, url_error)
            self._set_status(url_error)
            return None

        folder_valid, folder_error = validate_output_dir(output_dir)
        if not folder_valid:
            if record_errors:
                self._record_failed_attempt(platform, url, output_type, quality, folder_error)
            self._set_status(folder_error)
            return None

        return DownloadRequest(
            platform=platform,
            url=url,
            output_type=output_type,
            quality=quality,
            output_dir=Path(output_dir),
        )

    def _start_worker(self, request: DownloadRequest) -> None:
        if self.worker is not None:
            return
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

    def cancel_download(self) -> None:
        if not self.worker:
            return
        self.queue_active = False
        self.cancel_button.setEnabled(False)
        self.worker.cancel()
        self._set_status("Canceling")

    def _selected_output_type(self) -> str:
        return "Audio only" if self.audio_radio.isChecked() else "Video"

    def _on_preview_completed(self, payload: dict) -> None:
        detail = " | ".join(
            part
            for part in (
                payload.get("uploader"),
                self._format_duration(payload.get("duration")),
                payload.get("extractor"),
            )
            if part
        )
        self._set_preview(payload.get("title") or "(unknown title)", detail or "Preview loaded")
        if self.worker is None:
            self._set_status("Ready")

    def _on_preview_failed(self, error: str) -> None:
        self._set_preview("Preview unavailable", error or "Failed")
        self._set_status("Unsupported URL" if "unsupported" in error.lower() else "Failed")

    def _on_preview_finished(self) -> None:
        worker = self.preview_worker
        self.preview_worker = None
        if worker:
            worker.deleteLater()
        self.preview_button.setEnabled(self.worker is None)

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
        self._open_after_download(Path(payload["file_path"]))

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
        if self.queue_active and self.queue:
            self.start_queue()
        elif self.queue_active:
            self.queue_active = False

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
        self.open_file_check.setEnabled(not busy)
        self.open_folder_check.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.paste_button.setEnabled(not busy)
        self.preview_button.setEnabled(not busy and self.preview_worker is None)
        self.download_button.setEnabled(not busy)
        self.download_button.setText("Downloading" if busy else "Download")
        self.cancel_button.setVisible(busy)
        self.cancel_button.setEnabled(busy)
        self._refresh_queue_actions(busy)

    def _refresh_queue(self) -> None:
        self.queue_table.setRowCount(len(self.queue))
        for row, request in enumerate(self.queue):
            values = (
                request.platform,
                request.url,
                request.quality,
                str(request.output_dir),
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.queue_table.setItem(row, column, cell)
        self._refresh_queue_actions(self.worker is not None)

    def _refresh_queue_actions(self, busy: bool) -> None:
        has_items = bool(self.queue)
        self.add_queue_button.setEnabled(not busy)
        self.start_queue_button.setEnabled(not busy and has_items)
        self.remove_queue_button.setEnabled(not busy and has_items)
        self.clear_queue_button.setEnabled(not busy and has_items)

    def _apply_settings(self) -> None:
        if self.settings.default_platform in PLATFORMS:
            self.platform_combo.setCurrentText(self.settings.default_platform)
        self.audio_radio.setChecked(self.settings.default_output_type == "Audio only")
        self.video_radio.setChecked(self.settings.default_output_type != "Audio only")
        self._set_quality_options()
        preferred_quality = (
            self.settings.default_audio_quality
            if self.audio_radio.isChecked()
            else self.settings.default_video_quality
        )
        if preferred_quality:
            self.quality_combo.setCurrentText(preferred_quality)
        self.output_folder_input.setText(self.settings.default_output_folder)
        self.open_file_check.setChecked(self.settings.open_file_after_download)
        self.open_folder_check.setChecked(self.settings.open_folder_after_download)

    def _connect_settings_signals(self) -> None:
        self.platform_combo.currentTextChanged.connect(lambda _text: self._save_settings())
        self.quality_combo.currentTextChanged.connect(lambda _text: self._save_settings())
        self.video_radio.toggled.connect(lambda _checked: self._save_settings())
        self.audio_radio.toggled.connect(lambda _checked: self._save_settings())
        self.output_folder_input.editingFinished.connect(self._save_settings)
        self.open_file_check.toggled.connect(lambda _checked: self._save_settings())
        self.open_folder_check.toggled.connect(lambda _checked: self._save_settings())

    def _save_settings(self) -> None:
        if not hasattr(self, "quality_combo"):
            return
        video_quality = self.settings.default_video_quality
        audio_quality = self.settings.default_audio_quality
        if self.video_radio.isChecked() and self.quality_combo.currentText():
            video_quality = self.quality_combo.currentText()
        if self.audio_radio.isChecked() and self.quality_combo.currentText():
            audio_quality = self.quality_combo.currentText()

        self.settings = AppSettings(
            default_output_folder=self.output_folder_input.text().strip() or str(default_download_dir()),
            default_platform=self.platform_combo.currentText(),
            default_output_type=self._selected_output_type(),
            default_video_quality=video_quality,
            default_audio_quality=audio_quality,
            open_file_after_download=self.open_file_check.isChecked(),
            open_folder_after_download=self.open_folder_check.isChecked(),
            keep_history=self.settings.keep_history,
            convert_video_for_windows=self.settings.convert_video_for_windows,
        )
        self.settings_repository.save(self.settings)

    def _open_after_download(self, file_path: Path) -> None:
        if self.open_file_check.isChecked() and file_path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
        if self.open_folder_check.isChecked() and file_path.parent.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))

    def _set_preview(self, title: str, detail: str) -> None:
        self.preview_title_label.setText(title)
        self.preview_detail_label.setText(detail)

    def _format_duration(self, seconds: int | None) -> str:
        if seconds is None:
            return ""
        minutes, remainder = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{remainder:02d}"
        return f"{minutes}:{remainder:02d}"

    def _set_status(self, status: str) -> None:
        self.status_label.setText(status)
        if status in {"Ready"}:
            state = "ready"
        elif status in {"Completed"}:
            state = "success"
        elif status in {"Checking URL", "Downloading", "Converting", "Canceling"}:
            state = "active"
        else:
            state = "error"
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _apply_style(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)
