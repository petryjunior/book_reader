from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence


@dataclass
class Paragraph:
    text: str
    offset: int


@dataclass
class Chapter:
    title: str
    paragraphs: List[Paragraph]


class BookLoader:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.chapters = self._parse(path.read_text())
        self.current_chapter = 0
        self.current_paragraph = 0
        self._listeners: List[Callable[[dict], None]] = []

    @staticmethod
    def _parse(raw: str) -> List[Chapter]:
        chapters: List[Chapter] = []
        current_title = "Untitled"
        current_paragraphs: List[Paragraph] = []
        offset = 0

        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("chapter"):
                if current_paragraphs:
                    chapters.append(Chapter(current_title, current_paragraphs))
                current_title = stripped
                current_paragraphs = []
                offset = 0
                continue
            if not stripped:
                continue
            paragraph = Paragraph(stripped, offset)
            current_paragraphs.append(paragraph)
            offset += len(stripped)
        if current_paragraphs:
            chapters.append(Chapter(current_title, current_paragraphs))
        return chapters

    def add_listener(self, callback: Callable[[dict], None]) -> None:
        self._listeners.append(callback)

    def _emit_context(self) -> None:
        self._listeners[:]  # ensure list referenced
        context = self.current_context()
        for listener in self._listeners:
            listener(context)

    def current_context(self) -> dict:
        chapter = self.chapters[self.current_chapter]
        paragraph = chapter.paragraphs[self.current_paragraph]
        return {
            "chapter_title": chapter.title,
            "text": paragraph.text,
            "offset": paragraph.offset,
            "chapter_index": self.current_chapter,
            "paragraph_index": self.current_paragraph,
        }

    def _clamp_indices(self) -> None:
        self.current_chapter = max(0, min(self.current_chapter, len(self.chapters) - 1))
        chapter = self.chapters[self.current_chapter]
        self.current_paragraph = max(
            0, min(self.current_paragraph, len(chapter.paragraphs) - 1)
        )

    def next_paragraph(self) -> None:
        chapter = self.chapters[self.current_chapter]
        if self.current_paragraph + 1 < len(chapter.paragraphs):
            self.current_paragraph += 1
        else:
            if self.current_chapter + 1 < len(self.chapters):
                self.current_chapter += 1
                self.current_paragraph = 0
        self._clamp_indices()
        self._emit_context()

    def previous_paragraph(self) -> None:
        if self.current_paragraph > 0:
            self.current_paragraph -= 1
        elif self.current_chapter > 0:
            self.current_chapter -= 1
            self.current_paragraph = len(self.chapters[self.current_chapter].paragraphs) - 1
        self._clamp_indices()
        self._emit_context()

    def navigate_to(self, chapter_index: int, paragraph_index: int) -> None:
        self.current_chapter = chapter_index
        self.current_paragraph = paragraph_index
        self._clamp_indices()
        self._emit_context()
