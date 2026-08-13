#!/usr/bin/env python3
"""Audit deployed image assets and verify site image references."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REFERENCE_PATTERN = re.compile(r"(?:image|sourceImage)\s*[\"']?\s*[:=]\s*(?:`|[\"'])([^\"'`]+?\.(?:png|jpe?g|webp))", re.I)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    public = root / "public"
    images = [path for path in public.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
    assert images, "no site images found"
    assert all(path.suffix.lower() == ".webp" for path in images), "legacy PNG/JPEG assets remain"

    total = 0
    for path in images:
        total += path.stat().st_size
        with Image.open(path) as image:
            assert image.format == "WEBP", f"unexpected format: {path}"
            assert image.width > 0 and image.height > 0, f"invalid dimensions: {path}"

    missing = []
    scanned = []
    for path in list((root / "src").rglob("*")) + list((root / "scripts").rglob("*")) + list((root / "physiology").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".js", ".jsx", ".json", ".mjs", ".py", ".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        scanned.extend(REFERENCE_PATTERN.findall(text))
    for reference in scanned:
        if "${" in reference or "{" in reference:
            continue
        normalized = reference.lstrip("/")
        if not (public / normalized).exists():
            missing.append(reference)
    assert not missing, f"missing referenced images: {sorted(set(missing))[:20]}"

    print(json.dumps({
        "images": len(images),
        "bytes": total,
        "mib": round(total / 1048576, 2),
        "format": "webp",
        "references_checked": len(scanned),
        "status": "ok",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
