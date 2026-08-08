#!/usr/bin/env python3
"""Validate the lecture-23 bone and joint infection question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "ortho-infection-g01": ["ABCDEFGHIJ"],
    "ortho-infection-g02": ["ABCDEFGH"],
    "ortho-infection-g03": ["A"],
    "ortho-infection-g04": ["A", "B", "C"],
    "ortho-infection-g05": ["ABCDEF"],
    "ortho-infection-g06": ["ABCDEFG"],
    "ortho-infection-g07": ["G", "BEJL", "AC", "H", "I", "D", "F", "K"],
    "ortho-infection-g08": ["D", "E", "ABCGHI", "F"],
    "ortho-infection-g09": ["F", "BE", "AC", "DH", "G"],
    "ortho-infection-g10": ["BCDGI", "AEFH"],
    "ortho-infection-g11": ["C", "ABDE"],
    "ortho-infection-g12": ["BCEFGH"],
    "ortho-infection-g13": ["AE", "BCD"],
    "ortho-infection-g14": ["ABCF", "CDE"],
    "ortho-infection-g15": ["A", "C", "D", "B"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-ortho-infection-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 15
    assert sum(len(group["stems"]) for group in groups) == 38
    assert sum(len(group["options"]) for group in groups) == 116
    assert [group["id"] for group in groups] == list(EXPECTED)
    assert payload["meta"]["lecturePagesReviewed"] == [1, 2, 3, 4]

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-23"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True
        assert group["optionShuffleVersion"] == 1

        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert len(option_keys) == len(set(option_keys))
        assert len(source_keys) == len(set(source_keys))
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in source order"
        assert sorted(source_keys) == sorted(group["optionOriginalOrder"])

        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [
            "".join(sorted(display_to_source[key] for key in stem["answer"]))
            for stem in group["stems"]
        ]
        expected = ["".join(sorted(value)) for value in EXPECTED[group["id"]]]
        assert semantic_answers == expected, f"{group['id']}: answer remapping drift"

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-23"
        assert evidence["page"] in {1, 2, 3, 4}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    print({"groups": 15, "stems": 38, "options": 116, "shuffled": 15, "status": "ok"})


if __name__ == "__main__":
    main()
