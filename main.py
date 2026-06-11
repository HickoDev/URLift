"""URLift application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.window import URLiftWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = URLiftWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
