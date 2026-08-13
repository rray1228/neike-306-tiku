#!/usr/bin/env python3
"""Render every physiology lecture page referenced by a question group."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "src/data/physiology-data.json"
DEFAULT_OUT = ROOT / "public/physiology/lecture-pages"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pdftoppm", default="pdftoppm")
    parser.add_argument("--dpi", type=int, default=120)
    args = parser.parse_args()

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    lecture_files = {
        lecture["id"]: args.lecture_dir / lecture["file"]
        for lecture in payload["lectures"]
    }
    references = {
        (group["lectureEvidence"]["lectureId"], int(group["lectureEvidence"]["page"]))
        for group in payload["groups"]
    }
    args.out.mkdir(parents=True, exist_ok=True)

    rendered = 0
    for lecture_id, page in sorted(references):
        source = lecture_files[lecture_id]
        output = args.out / f"{lecture_id}-page-{page:02d}"
        subprocess.run([
            args.pdftoppm,
            "-f", str(page),
            "-l", str(page),
            "-singlefile",
            "-png",
            "-r", str(args.dpi),
            str(source),
            str(output),
        ], check=True)
        rendered += 1

    print({"referenced_pages": len(references), "rendered": rendered, "out": str(args.out)})


if __name__ == "__main__":
    main()
