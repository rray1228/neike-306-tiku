#!/usr/bin/env python3
"""Validate the perioperative and anesthesia question bank and lecture evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_GROUPS = [
    "surgery-general-p01", "surgery-general-p02", "surgery-general-p03",
    "surgery-general-p04", "surgery-general-p05", "surgery-general-p06",
    "surgery-general-p07", "surgery-general-p08", "surgery-general-p09",
    "surgery-general-p10a", "surgery-general-p10b",
    "surgery-general-a01", "surgery-general-a02", "surgery-general-a03",
    "surgery-general-a04", "surgery-general-a05", "surgery-general-a06",
    "surgery-general-a07", "surgery-general-a08", "surgery-general-a09",
    "surgery-general-a10", "surgery-general-a11a", "surgery-general-a11b",
    "surgery-general-a12", "surgery-general-a13", "surgery-general-a14",
    "surgery-general-a15", "surgery-general-a16",
]

EXPECTED_ANSWERS = {
    "surgery-general-p01": ["ABCD", "E", "FGHI"],
    "surgery-general-p02": list("ABCDEFGHIJ"),
    "surgery-general-p03": list("ABCDEFGH"),
    "surgery-general-p04": ["A", "B", "CDEFG", "C", "D", "E", "F", "G"],
    "surgery-general-p05": list("ABCDEFGH"),
    "surgery-general-p06": list("ABCDEFG"),
    "surgery-general-p07": ["A", "BCDE", "FG"],
    "surgery-general-p08": list("ABC"),
    "surgery-general-p09": ["ABC", "DEF", "GH", "IJKL"],
    "surgery-general-p10a": list("ABCDEFGH"),
    "surgery-general-p10b": ["A", "B", "C", "DE", "F", "G"],
    "surgery-general-a01": ["ABCD", "FGH", "IJKLM", "NOP"],
    "surgery-general-a02": ["A", "BCE", "BCD", "FGH", "IJ"],
    "surgery-general-a03": ["A", "B", "CD"],
    "surgery-general-a04": ["A", "B", "CDEFG", "HI", "JK"],
    "surgery-general-a05": ["ABDGIL", "CEFHJKL"],
    "surgery-general-a06": list("ABCD"),
    "surgery-general-a07": ["AB", "ABC", "CD"],
    "surgery-general-a08": ["ABFG", "CDEH"],
    "surgery-general-a09": list("ABCDEFG"),
    "surgery-general-a10": list("ABCD"),
    "surgery-general-a11a": list("AB"),
    "surgery-general-a11b": list("ABC"),
    "surgery-general-a12": list("AB"),
    "surgery-general-a13": list("ABCDEF"),
    "surgery-general-a14": ["E", "A", "B", "C", "D", "F", "G"],
    "surgery-general-a15": ["ABC", "DEFGHIJKLM"],
    "surgery-general-a16": ["ACEGHILM", "BDFIJKLN"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-general-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    assert payload["topics"] == ["外科总论"]
    assert [group["id"] for group in groups] == EXPECTED_GROUPS
    assert len(groups) == 28
    assert sum(len(group["stems"]) for group in groups) == 131
    assert sum(len(group["options"]) for group in groups) == 213

    seen_ids = set()
    forbidden = re.compile(r"\s{2,}|[|°•“”‘’]")
    for group in groups:
        group_id = group["id"]
        assert group_id not in seen_ids
        seen_ids.add(group_id)
        assert group["page"] == 0
        assert group["topic"] == "外科总论"
        assert group["hideSource"] is True
        assert group["reviewState"] == "已完成结构校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert not {"sourcePage", "sourceName", "sourceDocument"} & set(group)

        keys = [option["key"] for option in group["options"]]
        assert len(keys) == len(set(keys))
        assert all(option["label"] and option["label"] == option["label"].strip() for option in group["options"])
        actual_answers = ["".join(stem["answer"]) for stem in group["stems"]]
        assert actual_answers == EXPECTED_ANSWERS[group_id], f"{group_id}: answer drift"
        for stem in group["stems"]:
            assert stem["text"] and stem["text"] == stem["text"].strip()
            assert stem["answer"] and set(stem["answer"]) <= set(keys)

        text_values = [group["title"], group["sourceText"]]
        text_values.extend(option["label"] for option in group["options"])
        text_values.extend(stem["text"] for stem in group["stems"])
        assert not any(forbidden.search(value) for value in text_values), f"{group_id}: punctuation or spacing issue"

        evidence = group["lectureEvidence"]
        assert group["lectureIds"] == [evidence["lectureId"]]
        assert evidence["lectureId"] in {"lecture-35", "lecture-36"}
        assert (root / "public" / evidence["image"]).exists(), f"{group_id}: missing lecture image"

    all_payloads = [
        "surgery-data.json", "surgery-fracture-data.json", "surgery-general-data.json"
    ]
    all_ids = []
    for filename in all_payloads:
        data = json.loads((root / "src/data" / filename).read_text(encoding="utf-8"))
        all_ids.extend(group["id"] for group in data["groups"])
    assert len(all_ids) == len(set(all_ids)), "duplicate surgery group ids"

    print({"groups": 28, "stems": 131, "options": 213, "status": "ok"})


if __name__ == "__main__":
    main()
