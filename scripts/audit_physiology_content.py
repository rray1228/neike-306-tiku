#!/usr/bin/env python3
"""Validate the reconciled physiology payload and source-page assets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


EXPECTED_CORRECTIONS = {
    "phys-002", "phys-006", "phys-070", "phys-085", "phys-087", "phys-089",
    "phys-090", "phys-093", "phys-111", "phys-112", "phys-118", "phys-136",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/physiology-data.json").read_text(encoding="utf-8"))
    reconciliation = json.loads((root / "physiology/lecture-reconciliation.json").read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["lectureLinked"] is True
    assert payload["meta"]["sourcePages"] == 126
    assert payload["meta"]["lectureCount"] == 41
    assert len(payload["groups"]) == 160
    assert sum(len(group["stems"]) for group in payload["groups"]) == 505

    group_ids = [group["id"] for group in payload["groups"]]
    assert len(group_ids) == len(set(group_ids)), "duplicate group ids"

    corrected_ids = {record["id"] for record in reconciliation["corrections"]}
    assert corrected_ids == EXPECTED_CORRECTIONS, (corrected_ids, EXPECTED_CORRECTIONS)
    assert reconciliation["statusSummary"] == {"与今年讲义一致": 148, "已校正": 12}

    missing_images = []
    duplicate_option_keys = []
    invalid_answers = []
    empty_answers = []
    missing_lectures = []
    lecture_ids = {lecture["id"] for lecture in payload["lectures"]}
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        option_keys = [option["key"] for option in group["options"]]
        if len(option_keys) != len(set(option_keys)):
            duplicate_option_keys.append(group["id"])
        for stem_index, stem in enumerate(group["stems"]):
            if not stem.get("answer"):
                empty_answers.append(f"{group['id']}:{stem_index}")
            absent = [key for key in stem.get("answer", []) if key not in option_keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{stem_index}={absent}")
        if not group.get("lectureIds") or any(item not in lecture_ids for item in group["lectureIds"]):
            missing_lectures.append(group["id"])
        evidence = group.get("lectureEvidence", {})
        assert evidence.get("lectureId") in lecture_ids, f"missing evidence for {group['id']}"
        assert evidence.get("page", 0) > 0, f"missing lecture page for {group['id']}"

    assert not missing_images, f"missing source images: {missing_images[:5]}"
    assert not duplicate_option_keys, f"duplicate option keys: {duplicate_option_keys}"
    assert not invalid_answers, f"answers outside option bank: {invalid_answers}"
    assert not empty_answers, f"empty answers: {empty_answers}"
    assert not missing_lectures, f"missing lecture links: {missing_lectures}"

    print({
        "pages": len(payload["pages"]),
        "groups": len(payload["groups"]),
        "stems": sum(len(group["stems"]) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "corrections": len(corrected_ids),
        "reviewStates": dict(Counter(group["reviewState"] for group in payload["groups"])),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
