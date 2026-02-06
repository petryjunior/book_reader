from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from reader_app.config.state import StateStore
from reader_app.context_matcher import ContextMatcher, MatchResult
from reader_app.reader import BookLoader


class MainWindow(QMainWindow):
    def __init__(
        self,
        book_loader: BookLoader,
        matcher: ContextMatcher,
        state: StateStore,
        catalog_path: Path,
    ) -> None:
        super().__init__()
        self.book_loader = book_loader
        self.matcher = matcher
        self.state = state
        self.catalog_path = catalog_path

        self.setWindowTitle("StoryGlass Reader")
        self.resize(1200, 650)

        self._setup_ui()
        self._connect_signals()

        self.book_loader.add_listener(self._on_book_context)
        self.matcher.add_listener(self._on_image_match)
        self.book_loader.navigate_to(
            self.state.get("last_chapter", 0), self.state.get("last_paragraph", 0)
        )

    def _setup_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(splitter)

        self.text_viewer = QTextBrowser()
        self.text_viewer.setReadOnly(True)
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.text_viewer)

        nav_bar = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_bar.setLayout(nav_layout)
        left_layout.addWidget(nav_bar)

        left_container.setLayout(left_layout)

        image_panel = QWidget()
        image_layout = QVBoxLayout()
        self.image_label = QLabel("No image yet")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(320)
        self.metadata_label = QLabel("")
        self.fallback_list = QListWidget()
        self.fallback_list.setFixedHeight(140)
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(self.metadata_label)
        image_layout.addWidget(QLabel("Other matches"))
        image_layout.addWidget(self.fallback_list)
        image_panel.setLayout(image_layout)

        splitter.addWidget(left_container)
        splitter.addWidget(image_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        toolbar = self.addToolBar("Navigation")
        toolbar.addAction("Previous", self.book_loader.previous_paragraph)
        toolbar.addAction("Next", self.book_loader.next_paragraph)
        open_catalog_action = toolbar.addAction("Catalog Editor")
        open_catalog_action.triggered.connect(self._launch_catalog_editor)
        session_action = toolbar.addAction("Session Info")
        session_action.triggered.connect(self._show_session_info)

    def _connect_signals(self) -> None:
        self.prev_button.clicked.connect(self.book_loader.previous_paragraph)
        self.next_button.clicked.connect(self.book_loader.next_paragraph)
        self.fallback_list.itemClicked.connect(self._on_fallback_selected)

    def _launch_catalog_editor(self) -> None:
        print("You can re-run `python -m reader_app.cli.catalog_editor ...` to edit catalogs.")

    def _on_book_context(self, context: dict) -> None:
        chapter = context["chapter_title"]
        paragraph = context["text"]
        self.text_viewer.setHtml(
            f"<h2>{chapter}</h2><p>{paragraph}</p>"
        )
        self.metadata_label.setText(
            f"Offsets chapter {context['chapter_index']}, paragraph {context['paragraph_index']}"
        )
        self.matcher.update_context(context)
        self.state.set("last_chapter", context["chapter_index"])
        self.state.set("last_paragraph", context["paragraph_index"])
        self.state.set("last_book", str(self.book_loader.path))
        self.state.set("last_catalog", str(self.catalog_path))

    def _on_image_match(self, match: MatchResult) -> None:
        pixmap = QPixmap(match.entry.path)
        if pixmap.isNull():
            self.image_label.setText(f"Image missing: {match.entry.path}")
        else:
            scaled = pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        self.metadata_label.setText(
            f"{match.entry.title} — tags: {', '.join(match.entry.tags)}"
        )
        self.fallback_list.clear()
        for entry in match.fallback_candidates:
            item = QListWidgetItem(f"{entry.title} ({entry.id})")
            item.setData(Qt.UserRole, entry.id)
            self.fallback_list.addItem(item)

    def _on_fallback_selected(self, item: QListWidgetItem) -> None:
        entry_id = item.data(Qt.UserRole)
        self.matcher.pin_entry(entry_id)
        self.matcher.update_context(self.book_loader.current_context())

    def _show_session_info(self) -> None:
        import json

        payload = json.dumps(self.state.data, indent=2)
        QMessageBox.information(self, "Session State", payload or "No saved session yet.")
