#!/usr/bin/env python3
"""Convert deployed PNG/JPEG assets to readable, size-efficient WebP files.

The site consists mainly of scanned question sheets and lecture pages. A
conservative quality setting is used so small Chinese text remains legible.
Only images wider than MAX_WIDTH are resized; current assets are already below
that threshold, so the first optimization pass is format-only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg"}
TEXT_SUFFIXES = {".js", ".jsx", ".json", ".mjs", ".py", ".ts", ".tsx", ".md", ".html", ".css"}
SKIP_DIRS = {".git", "dist", "dist-pages", "node_modules", "tmp", ".next", ".wrangler"}


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def convert_image(source: Path, target: Path, *, quality: int, max_width: int) -> tuple[int, int, bool]:
    before = source.stat().st_size
    with Image.open(source) as opened:
        image = opened.copy()
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA" if "transparency" in opened.info else "RGB")
    resized = image.width > max_width
    if resized:
        height = round(image.height * max_width / image.width)
        image = image.resize((max_width, height), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "WEBP", quality=quality, method=6, exact=True)
    return before, target.stat().st_size, resized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", type=int, default=88)
    parser.add_argument("--max-width", type=int, default=1600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    public = root / "public"
    sources = sorted(
        path for path in public.rglob("*")
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES
    )
    if not sources:
        print({"converted": 0, "message": "no PNG/JPEG assets found"})
        return

    mapping: dict[str, str] = {}
    before_total = 0
    after_total = 0
    resized_count = 0
    staged: list[tuple[Path, Path]] = []

    for source in sources:
        target = source.with_suffix(".webp")
        public_old = source.relative_to(public).as_posix()
        public_new = target.relative_to(public).as_posix()
        mapping[public_old] = public_new
        if args.dry_run:
            before_total += source.stat().st_size
            continue
        before, after, resized = convert_image(source, target, quality=args.quality, max_width=args.max_width)
        before_total += before
        after_total += after
        resized_count += int(resized)
        staged.append((source, target))

    if not args.dry_run:
        for path in iter_text_files(root):
            original = path.read_text(encoding="utf-8")
            updated = original
            for old, new in mapping.items():
                updated = updated.replace(old, new)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
        for source, target in staged:
            if not target.exists() or target.stat().st_size == 0:
                raise RuntimeError(f"missing converted asset: {target}")
            source.unlink()

    result = {
        "converted": len(sources),
        "quality": args.quality,
        "max_width": args.max_width,
        "resized": resized_count,
        "before_bytes": before_total,
        "after_bytes": after_total or None,
        "reduction_pct": round((1 - after_total / before_total) * 100, 1) if after_total else None,
        "dry_run": args.dry_run,
    }
    print(result)


if __name__ == "__main__":
    main()
