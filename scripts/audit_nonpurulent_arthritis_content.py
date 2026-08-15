#!/usr/bin/env python3
"""Validate the lecture-24 nonpurulent arthritis question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "nonpurulent-arthritis-g01": ["BCEGJK", "ADFHIL"],
    "nonpurulent-arthritis-g02": ["BCEGHJL", "ADFIKM"],
    "nonpurulent-arthritis-g03": ["BEGIKN", "ADFHJLM", "COP"],
    "nonpurulent-arthritis-g04": ["D", "C", "E", "B", "A"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-nonpurulent-arthritis-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 4
    assert sum(len(group["stems"]) for group in groups) == 12
    assert sum(len(group["options"]) for group in groups) == 46
    assert [group["id"] for group in groups] == list(EXPECTED)
    assert payload["meta"]["lecturePagesReviewed"] == [1, 2, 3, 4]

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-24"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True
        expected_version = 4 if group["id"] in {"nonpurulent-arthritis-g01", "nonpurulent-arthritis-g02"} else 3
        assert group["optionShuffleVersion"] == expected_version

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
        assert evidence["lectureId"] == "lecture-24"
        assert evidence["page"] in {2, 3, "1～2"}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    assert any(option["label"] == "HLA-B₂₇" for group in groups for option in group["options"])
    assert any(option["label"] == "4字试验" for group in groups for option in group["options"])
    group1, group2 = groups[:2]
    assert [option["sourceKey"] for option in group1["options"]] == ["J", "I", "C", "F", "G", "L", "A", "B", "D", "K", "E", "H"]
    assert [option["sourceKey"] for option in group2["options"]] == ["G", "F", "L", "K", "E", "A", "J", "M", "I", "B", "D", "C", "H"]
    ra = next(stem for stem in group2["stems"] if stem["text"] == "类风湿关节炎")
    assert "H" in ra["answer"]
    assert group2["options"][7]["label"] == "晨僵明显而持久"
    print({"groups": 4, "stems": 12, "options": 46, "shuffled": 4, "status": "ok"})


if __name__ == "__main__":
    main()
