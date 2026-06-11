"""Background download worker for the PySide6 UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from downloader.core import FFmpegMissingError, URLiftDownloadError, download_audio, download_video


@dataclass(frozen=True)
class DownloadRequest:
    platform: str
    url: str
    output_type: str
    quality: str
    output_dir: Path


class DownloadWorker(QThread):
    progress = Signal(str, object, str)
    completed = Signal(dict)
    failed = Signal(dict)

    def __init__(self, request: DownloadRequest) -> None:
        super().__init__()
        self.request = request

    def run(self) -> None:
        try:
            result = self._run_download()
            self.completed.emit(
                {
                    "platform": self.request.platform,
                    "url": self.request.url,
                    "title": result.title,
                    "output_type": self.request.output_type,
                    "quality": self.request.quality,
                    "file_path": str(result.file_path),
                    "extension": result.extension,
                }
            )
        except FFmpegMissingError as exc:
            self.failed.emit(self._failure_payload("FFmpeg missing", str(exc)))
        except URLiftDownloadError as exc:
            status = "Unsupported URL" if "unsupported" in str(exc).lower() else "Failed"
            self.failed.emit(self._failure_payload(status, str(exc)))
        except Exception as exc:
            self.failed.emit(self._failure_payload("Failed", str(exc) or "Failed"))

    def _run_download(self):
        if self.request.output_type == "Audio only":
            return download_audio(
                self.request.url,
                self.request.quality,
                self.request.output_dir,
                self._progress_callback,
            )

        return download_video(
            self.request.url,
            self.request.quality,
            self.request.output_dir,
            self._progress_callback,
        )

    def _progress_callback(self, status: str, percent: float | None, message: str) -> None:
        self.progress.emit(status, percent, message)

    def _failure_payload(self, status: str, error: str) -> dict:
        return {
            "platform": self.request.platform,
            "url": self.request.url,
            "title": "",
            "output_type": self.request.output_type,
            "quality": self.request.quality,
            "file_path": "",
            "extension": "",
            "status": status,
            "error": error,
        }
