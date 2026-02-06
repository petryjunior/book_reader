from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from reader_app.image_catalog import ImageCatalog, ImageCatalogEntry


@dataclass
class MatchResult:
    entry: ImageCatalogEntry
    fallback_candidates: List[ImageCatalogEntry]


class ContextMatcher:
    def __init__(self, catalog: ImageCatalog) -> None:
        self.catalog = catalog
        self._listeners: List[Callable[[MatchResult], None]] = []
        self._pinned_entry_id: Optional[str] = None

    def add_listener(self, listener: Callable[[MatchResult], None]) -> None:
        self._listeners.append(listener)

    def pin_entry(self, entry_id: str) -> None:
        self._pinned_entry_id = entry_id

    def clear_pin(self) -> None:
        self._pinned_entry_id = None

    def _emit(self, result: MatchResult) -> None:
        for listener in self._listeners:
            listener(result)

    def update_context(self, context: dict) -> None:
        chapter_title = context.get("chapter_title")
        text = context.get("text", "")
        offset = context.get("offset", 0)

        keywords = [word.strip(".,?") for word in text.lower().split()]
        candidates = self.catalog.find_for_context(chapter_title, offset, keywords)

        selected: Optional[ImageCatalogEntry] = None
        if self._pinned_entry_id:
            pinned = next(
                (entry for entry in candidates if entry.id == self._pinned_entry_id), None
            )
            if pinned:
                selected = pinned

        if selected is None and candidates:
            selected = candidates[0]

        if selected:
            fallback = [entry for entry in candidates if entry.id != selected.id]
            self._emit(MatchResult(entry=selected, fallback_candidates=fallback))
