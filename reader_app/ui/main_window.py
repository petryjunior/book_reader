from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSizePolicy,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QGraphicsOpacityEffect,
    QMainWindow,
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
        self._current_pixmap: Optional[QPixmap] = None

        self.setWindowTitle("StoryGlass Reader")
        self.resize(1200, 650)

        self._setup_ui()
        self._connect_signals()

        self.matcher.add_listener(self._on_image_match)
        self._set_book_loader(self.book_loader)

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
        self.font_label = QLabel()
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(14, 36)
        self.font_slider.setTickInterval(2)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setSingleStep(1)
        default_font_size = 20
        self.font_slider.setValue(default_font_size)
        self._apply_font_size(default_font_size)
        nav_layout.addWidget(self.font_label)
        nav_layout.addWidget(self.font_slider)
        nav_bar.setLayout(nav_layout)
        left_layout.addWidget(nav_bar)

        left_container.setLayout(left_layout)

        image_panel = QWidget()
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel("No image yet")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._image_effect = QGraphicsOpacityEffect(self.image_label)
        self.image_label.setGraphicsEffect(self._image_effect)
        self._image_animation = QPropertyAnimation(self._image_effect, b"opacity", self)
        self._image_animation.setDuration(400)
        self._image_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._image_animation.setStartValue(0.0)
        self._image_animation.setEndValue(1.0)
        image_layout.addWidget(self.image_label)
        image_panel.setLayout(image_layout)
        self.image_panel = image_panel

        splitter.addWidget(left_container)
        splitter.addWidget(image_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        toolbar = self.addToolBar("Navigation")
        toolbar.addAction("Previous", self._navigate_previous)
        toolbar.addAction("Next", self._navigate_next)
        toolbar.addAction("Open Book", self._prompt_book_path)
        open_catalog_action = toolbar.addAction("Catalog Editor")
        open_catalog_action.triggered.connect(self._launch_catalog_editor)
        session_action = toolbar.addAction("Session Info")
        session_action.triggered.connect(self._show_session_info)

    def _connect_signals(self) -> None:
        self.prev_button.clicked.connect(self._navigate_previous)
        self.next_button.clicked.connect(self._navigate_next)
        self.font_slider.valueChanged.connect(self._on_font_size_changed)

    def _navigate_previous(self) -> None:
        if self.book_loader:
            self.book_loader.previous_paragraph()

    def _navigate_next(self) -> None:
        if self.book_loader:
            self.book_loader.next_paragraph()

    def _prompt_book_path(self) -> None:
        last_book = self.state.get("last_book")
        start_dir = (
            Path(last_book).parent
            if last_book and Path(last_book).parent.exists()
            else Path.home()
        )
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open book",
            str(start_dir),
            "Text & Markdown (*.txt *.md)",
        )
        if not path:
            return
        self._load_book(Path(path))

    def _load_book(self, path: Path) -> None:
        try:
            loader = BookLoader(path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Open book",
                f"Unable to load {path.name}:\n{exc}",
            )
            return
        self._set_book_loader(loader, chapter=0, paragraph=0)

    def _set_book_loader(
        self,
        loader: BookLoader,
        *,
        chapter: Optional[int] = None,
        paragraph: Optional[int] = None,
    ) -> None:
        self.book_loader = loader
        self.book_loader.add_listener(self._on_book_context)
        start_chapter = (
            chapter
            if chapter is not None
            else self.state.get("last_chapter", 0)
        )
        start_paragraph = (
            paragraph
            if paragraph is not None
            else self.state.get("last_paragraph", 0)
        )
        self.book_loader.navigate_to(start_chapter, start_paragraph)
        self.state.set("last_book", str(self.book_loader.path))

    def _launch_catalog_editor(self) -> None:
        print("You can re-run `python -m reader_app.cli.catalog_editor ...` to edit catalogs.")

    def _on_book_context(self, context: dict) -> None:
        chapter = context["chapter_title"]
        paragraph = context["text"]
        self.text_viewer.setHtml(
            f"<h2>{chapter}</h2><p>{paragraph}</p>"
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
            self._current_pixmap = None
            return
        self._current_pixmap = pixmap
        self._update_image_display()

    def _update_image_display(self) -> None:
        if not self._current_pixmap:
            return
        scaled = self._current_pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self._image_effect.setOpacity(0.0)
        self._image_animation.stop()
        self._image_animation.start()

    def _apply_font_size(self, value: int) -> None:
        font = self.text_viewer.font()
        font.setPointSize(value)
        self.text_viewer.setFont(font)
        self.font_label.setText(f"Font size: {value}")

    def _on_font_size_changed(self, value: int) -> None:
        self._apply_font_size(value)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        half_width = max(240, self.width() // 2)
        self.image_panel.setMaximumWidth(half_width)
        self._update_image_display()

    def _show_session_info(self) -> None:
        import json

        payload = json.dumps(self.state.data, indent=2)
        QMessageBox.information(self, "Session State", payload or "No saved session yet.")
