#!/usr/bin/env python3
"""Validate the lecture-22 orthopaedic question bank and shuffled answers."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "ortho-mixed-g01": ["A", "BCD"],
    "ortho-mixed-g02": ["A", "B", "C"],
    "ortho-mixed-g03": ["A", "B", "C", "DE"],
    "ortho-mixed-g04": ["ABC"],
    "ortho-mixed-g05": ["ABC", "DEFGH"],
    "ortho-mixed-g07": ["AB", "C", "D", "EFGH"],
    "ortho-mixed-g08": ["ABCD"],
    "ortho-mixed-g09": ["A", "B", "C"],
    "ortho-mixed-g10": ["A", "BCD"],
    "ortho-mixed-g11": ["ABCD", "AF", "GHIJ", "K"],
    "ortho-mixed-g12": ["A", "B"],
    "ortho-mixed-g13": ["A", "C", "E", "FG"],
    "ortho-mixed-g14": ["A", "B", "C", "D", "EFGH"],
    "ortho-mixed-g15": ["ABC", "DEF", "GHITUV", "JK", "LM", "NOP", "QRSWXYZ"],
    "ortho-mixed-g19": ["ABCDEFG", "H", "I", "J"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-ortho-mixed-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    assert len(groups) == 15
    assert sum(len(group["stems"]) for group in groups) == 48
    assert sum(len(group["options"]) for group in groups) == 105
    assert [group["id"] for group in groups] == list(EXPECTED)

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-22"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True
        expected_shuffle = 3 if group["id"] == "ortho-mixed-g15" else 2 if group["id"] == "ortho-mixed-g19" else 1
        assert group["optionShuffleVersion"] == expected_shuffle
        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert len(option_keys) == len(set(option_keys))
        assert len(source_keys) == len(set(source_keys))
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in lecture order"
        assert sorted(source_keys) == sorted(group["optionOriginalOrder"])

        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = []
        for stem in group["stems"]:
            mapped = "".join(display_to_source[key] for key in stem["answer"])
            semantic_answers.append(mapped if stem["answerMode"] == "排序" else "".join(sorted(mapped)))
        expected = [value if group["kindLabel"] == "排序题" else "".join(sorted(value)) for value in EXPECTED[group["id"]]]
        assert semantic_answers == expected, f"{group['id']}: answer remapping drift"

        if group["kindLabel"] == "排序题":
            assert len(groups) and group["stems"][0]["answerDisplay"] == "切割伤＞碾压伤＞撕脱伤"

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-22"
        assert evidence["page"] in {1, 2, 3, 5, 6}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values += [option["label"] for option in group["options"]]
        values += [stem["text"] for stem in group["stems"]]
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    print({"groups": 15, "stems": 48, "options": 105, "ranking": 1, "shuffled": 15, "status": "ok"})


if __name__ == "__main__":
    main()
