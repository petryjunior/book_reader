from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import yaml


@dataclass
class ImageCatalogEntry:
    id: str
    path: Path
    title: str
    chapter: Optional[str] = None
    priority: int = 50
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    description: Optional[str] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

    def matches_range(self, offset: int) -> bool:
        if self.start_offset is None and self.end_offset is None:
            return True
        start = self.start_offset if self.start_offset is not None else 0
        end = self.end_offset if self.end_offset is not None else offset
        return start <= offset <= end


class ImageCatalog:
    def __init__(self, entries: Sequence[ImageCatalogEntry]) -> None:
        self._entries = list(entries)

    @classmethod
    def load(cls, source: Path) -> "ImageCatalog":
        raw = yaml.safe_load(source.read_text())
        entries: List[ImageCatalogEntry] = []
        for item in raw or []:
            if item is None:
                continue
            entry = ImageCatalogEntry(
                id=item["id"],
                path=Path(item["path"]),
                title=item.get("title", ""),
                chapter=item.get("chapter"),
                priority=int(item.get("priority", 50)),
                tags=list(item.get("tags", [])),
                keywords=list(item.get("keywords", [])),
                description=item.get("description"),
                start_offset=item.get("start_offset"),
                end_offset=item.get("end_offset"),
            )
            entries.append(entry)
        return cls(entries)

    def entries(self) -> List[ImageCatalogEntry]:
        return list(self._entries)

    def find_for_context(
        self,
        chapter: Optional[str],
        offset: int,
        keywords: Sequence[str],
    ) -> List[ImageCatalogEntry]:
        matching = []
        normalized_keywords = {k.lower() for k in keywords}
        for entry in self._entries:
            if entry.chapter and chapter and entry.chapter != chapter:
                continue
            if not entry.matches_range(offset):
                continue
            weight = entry.priority
            weight += len(normalized_keywords & {kw.lower() for kw in entry.keywords})
            tag_hit = len(
                normalized_keywords & {tag.lower() for tag in entry.tags}
            )
            weight += tag_hit * 2
            matching.append((weight, entry))
        matching.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [entry for _, entry in matching]

    def validate(self) -> List[str]:
        errors = []
        for entry in self._entries:
            if not entry.path:
                errors.append(f"{entry.id}: missing path")
            if not entry.tags and not entry.keywords:
                errors.append(f"{entry.id}: missing tags/keywords")
        return errors
