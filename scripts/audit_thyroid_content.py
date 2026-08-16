#!/usr/bin/env python3
"""Validate all thyroid-disease groups against source pages and lecture 01."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "p01-g1": ["B", "A", "C"],
    "p01-g2": ["A", "B", "B"],
    "p01-g3": ["B", "A"],
    "p01-g4": ["ACEGHJL", "BDFIKM"],
    "p01-g5": ["CD", "DE", "AB"],
    "p02-g1": ["AE", "BG", "CDH", "FIJ"],
    "p02-g2": ["ACDFHK", "BEGIJL"],
    "p02-g3": ["E", "B", "G", "DH", "ACFI"],
    "p03-g1": ["E", "E", "ABCD", "ABD", "E", "ABCD", "BD"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"][:9]

    assert [group["id"] for group in groups] == list(EXPECTED)
    assert sum(len(group["stems"]) for group in groups) == 31
    assert sum(len(group["options"]) for group in groups) == 61

    for group in groups:
        assert group["topic"] == "颈部疾病"
        assert group["lectureIds"] == ["lecture-01"]
        assert group["reviewState"] == "已按原题页及讲义逐项复核"
        assert not group["reviewIssues"] and not group["reviewNotes"]

        option_keys = {option["key"] for option in group["options"]}
        actual = []
        for stem in group["stems"]:
            assert stem["answer"] and set(stem["answer"]) <= option_keys
            actual.append("".join(stem["answer"]))
        assert actual == EXPECTED[group["id"]], f"{group['id']}: answer drift"

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-01"
        assert evidence["page"] in {1, 2, 3, 4, 6, "3～4"}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture page"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(option["sourceText"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        values.extend(stem["sourceText"] for stem in group["stems"])
        for value in values:
            assert not re.search(r"疾疲|TNMi|TNMo|：：|眼脸|近全圾|[」』|°•“”‘’]", value), f"{group['id']}: OCR residue in {value}"
            assert not re.search(r"\s{2,}", value), f"{group['id']}: repeated spacing"
            assert value.count("（") == value.count("）"), f"{group['id']}: unbalanced punctuation"

    groups_by_id = {group["id"]: group for group in groups}
    assert groups_by_id["p01-g3"]["options"][0]["label"] == "任何TNM₁（有远处转移）"
    assert groups_by_id["p01-g3"]["options"][1]["label"] == "任何TNM₀（无远处转移）"
    assert "T₃、T₄↑，摄碘率↓" in groups_by_id["p02-g1"]["options"][3]["label"]
    assert groups_by_id["p02-g2"]["options"][4]["label"] == "TSH正常或降低"
    assert groups_by_id["p02-g2"]["options"][10]["label"] == "TSH升高"
    assert groups_by_id["p02-g3"]["options"][0]["label"] == "眼睑下垂"

    print({"groups": 9, "stems": 31, "options": 61, "status": "ok"})


if __name__ == "__main__":
    main()
