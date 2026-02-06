from pathlib import Path

from reader_app.config.state import StateStore


def test_state_store_persists(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path=path)
    store.set("last_book", "story.txt")
    store.set("last_catalog", "catalog.yaml")
    reloaded = StateStore(path=path)
    assert reloaded.get("last_book") == "story.txt"
    assert reloaded.get("last_catalog") == "catalog.yaml"
