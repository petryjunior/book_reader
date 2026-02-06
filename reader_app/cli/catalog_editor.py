from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from reader_app.image_catalog import ImageCatalog


def describe_entry(entry) -> str:
    return f"{entry.id}: {entry.title} ({entry.path})"


def list_entries(entries: Iterable) -> None:
    for entry in entries:
        print(describe_entry(entry))


def validate_entries(entries: Sequence) -> None:
    catalog = ImageCatalog(entries)
    errors = catalog.validate()
    if errors:
        print("Validation errors:")
        for error in errors:
            print(" -", error)
    else:
        print("Catalog looks healthy.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect or validate an image catalog."
    )
    parser.add_argument("catalog", type=Path, help="YAML catalog path")
    parser.add_argument("--list", action="store_true", help="List catalog entries")
    parser.add_argument("--validate", action="store_true", help="Run catalog validation")
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="List entries whose image files are missing on disk",
    )
    args = parser.parse_args()

    catalog = ImageCatalog.load(args.catalog)
    if args.list:
        list_entries(catalog.entries())
    if args.validate or not args.list:
        validate_entries(catalog.entries())
    if args.show_missing:
        missing = [
            entry for entry in catalog.entries() if not entry.path.exists()
        ]
        if missing:
            print("Missing image files:")
            for entry in missing:
                print(f" - {entry.id}: {entry.path}")
        else:
            print("All referenced image files exist.")


if __name__ == "__main__":
    main()
