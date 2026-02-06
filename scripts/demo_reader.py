from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from reader_app.config.state import StateStore
from reader_app.context_matcher import ContextMatcher
from reader_app.image_catalog import ImageCatalog
from reader_app.reader import BookLoader
from reader_app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication([])
    root = Path(__file__).resolve().parent.parent
    book_path = root / "resources" / "sample_book.txt"
    catalog_path = root / "resources" / "sample_catalog.yaml"
    catalog = ImageCatalog.load(catalog_path)
    book_loader = BookLoader(book_path)
    matcher = ContextMatcher(catalog)
    state = StateStore()
    window = MainWindow(book_loader, matcher, state, catalog_path)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
