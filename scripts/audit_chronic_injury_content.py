#!/usr/bin/env python3
"""Validate the lecture-21 chronic musculoskeletal injury question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "chronic-injury-g01": ["ABCDEFG", "BCDE", "F"],
    "chronic-injury-g02": ["ABCDEFG", "HI", "JKL", "MNO", "PQRST"],
    "chronic-injury-g03": ["ABC", "D", "EFGH", "IJKL", "MN", "O"],
    "chronic-injury-g04": ["A", "B", "C", "D", "E", "F"],
    "chronic-injury-g05": ["ABCDE", "FGHIJ", "KLMNOP", "QRST", "UVWX", "YZ"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-chronic-injury-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 5
    assert sum(len(group["stems"]) for group in groups) == 26
    assert sum(len(group["options"]) for group in groups) == 74
    assert payload["meta"]["lecturePagesReviewed"] == [1, 2, 3, 4]
    assert [group["id"] for group in groups] == list(EXPECTED)

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-21"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"] and not group["parseWarnings"]
        assert group["hideSource"] is True
        assert group["optionShuffleVersion"] == 2
        assert group["sourcePdf"] is None and group["sourceImage"] is None

        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert len(option_keys) == len(set(option_keys))
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in source order"
        assert set(source_keys) == set(group["optionOriginalOrder"])

        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [
            "".join(sorted(display_to_source[key] for key in stem["answer"]))
            for stem in group["stems"]
        ]
        expected = ["".join(sorted(answer)) for answer in EXPECTED[group["id"]]]
        assert semantic_answers == expected, f"{group['id']}: answer remapping drift"
        assert all(stem["answer"] and set(stem["answer"]) <= set(option_keys) for stem in group["stems"])

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-21"
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    assert all(stem["text"] != "髌骨软骨软化症" for stem in groups[1]["stems"])
    assert any(stem["text"] == "髌骨软骨软化症" for stem in groups[2]["stems"])
    print({"groups": 5, "stems": 26, "options": 74, "shuffled": 5, "status": "ok"})


if __name__ == "__main__":
    main()
