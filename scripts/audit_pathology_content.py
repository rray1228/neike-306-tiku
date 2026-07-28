#!/usr/bin/env python3
"""Structural checks for the standalone pathology payload."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/pathology-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["sourcePdfPages"] == 37
    assert payload["meta"]["sourcePages"] == 35
    assert payload["meta"]["lectureCount"] == 26

    ids = [group["id"] for group in payload["groups"]]
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert all(group["page"] >= 3 for group in payload["groups"])
    assert all(group.get("stems") for group in payload["groups"]), "empty question group"

    invalid_answers = []
    duplicate_answers = []
    missing_images = []
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        keys = {option["key"] for option in group.get("options", [])}
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            if len(answer) != len(set(answer)):
                duplicate_answers.append(f"{group['id']}:{index}")
            absent = [key for key in answer if key not in keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{index}={''.join(absent)}")

    assert not missing_images, f"missing source images: {missing_images}"
    assert not duplicate_answers, f"duplicate answer keys: {duplicate_answers}"
    assert not invalid_answers, f"answers missing from option bank: {invalid_answers}"

    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group.get("stems", [])) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
