from reader_app.context_matcher import ContextMatcher, MatchResult
from reader_app.image_catalog import ImageCatalog, ImageCatalogEntry


class DummyListener:
    def __init__(self):
        self.last: MatchResult | None = None

    def __call__(self, result: MatchResult) -> None:
        self.last = result


def test_context_matcher_prioritizes_keywords(tmp_path):
    entries = [
        ImageCatalogEntry(
            id="a",
            path=tmp_path / "a.jpg",
            title="A",
            chapter="Chapter 1 — Dawn Ride",
            priority=30,
            keywords=["wind", "carriage"],
        ),
        ImageCatalogEntry(
            id="b",
            path=tmp_path / "b.jpg",
            title="B",
            chapter="Chapter 1 — Dawn Ride",
            priority=50,
            keywords=["sunrise"],
        ),
    ]
    catalog = ImageCatalog(entries)
    matcher = ContextMatcher(catalog)
    listener = DummyListener()
    matcher.add_listener(listener)

    matcher.update_context(
        {
            "chapter_title": "Chapter 1 — Dawn Ride",
            "text": "The wind rattled the carriage.",
            "offset": 0,
        }
    )
    assert listener.last is not None
    assert listener.last.entry.id == "a"


def test_context_matcher_pin_selects_entry(tmp_path):
    entries = [
        ImageCatalogEntry(
            id="a",
            path=tmp_path / "a.jpg",
            title="A",
            chapter="Chapter 1 — Dawn Ride",
        ),
        ImageCatalogEntry(
            id="b",
            path=tmp_path / "b.jpg",
            title="B",
            chapter="Chapter 1 — Dawn Ride",
        ),
    ]
    catalog = ImageCatalog(entries)
    matcher = ContextMatcher(catalog)
    listener = DummyListener()
    matcher.add_listener(listener)
    matcher.pin_entry("b")
    matcher.update_context(
        {"chapter_title": "Chapter 1 — Dawn Ride", "text": "Text", "offset": 0}
    )
    assert listener.last is not None
    assert listener.last.entry.id == "b"
