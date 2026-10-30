#!/usr/bin/env python3
"""Render the reviewed physiology collection pages, including annotations.

Usage: python scripts/render_physiology_collection_pages.py /path/to/collection.pdf
The checked manifest fixes the mapping from split-lecture pages to the collection.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "physiology/collection-lecture-pages.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != manifest["sourceSha256"]:
        raise SystemExit("Source PDF differs from the reviewed collection; recheck the page mapping.")

    with pdfium.PdfDocument(args.pdf) as document:
        if len(document) != manifest["sourcePageCount"]:
            raise SystemExit("Unexpected collection page count")
        for item in manifest["pages"]:
            target = ROOT / "public" / item["image"]
            target.parent.mkdir(parents=True, exist_ok=True)
            page = document[item["collectionPage"] - 1]
            try:
                bitmap = page.render(scale=manifest["renderDpi"] / 72, draw_annots=True)
                image = bitmap.to_pil().convert("RGB")
                image.save(target, "WEBP", quality=manifest["webpQuality"], method=6)
                image.close()
                bitmap.close()
            finally:
                page.close()
            print(f"{item['collectionPage']}: {target.name}", flush=True)


if __name__ == "__main__":
    main()
