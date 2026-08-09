#!/usr/bin/env python3
"""Validate the lecture-28 limb fracture and dislocation question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_SOURCE_ANSWERS = {
    "limb-fracture-dislocation-g01": [set(x) for x in ["A", "D", "G", "I", "K", "A", "J", "E", "C", "B", "H", "L", "F"]],
    "limb-fracture-dislocation-g02": [set(x) for x in ["FHL", "ABGNR", "EIK", "S", "CDJO", "BPT", "MQ"]],
    "limb-fracture-dislocation-g03": [set(x) for x in ["E", "GM", "HJ", "K", "I", "BCD", "F", "AL"]],
    "limb-fracture-dislocation-g04": [set(x) for x in ["DJKL", "GH", "BCIMO", "AEFN"]],
    "limb-fracture-dislocation-g05": [set(x) for x in ["A", "E", "D", "B", "C"]],
    "limb-fracture-dislocation-g06": [set(x) for x in ["A", "F", "G", "B", "J", "D", "I", "K", "H", "E", "C"]],
    "limb-fracture-dislocation-g07": [set(x) for x in ["E", "A", "L", "J", "B", "H", "G", "H", "O", "F", "N", "I", "CDM", "K"]],
    "limb-fracture-dislocation-g08": [set(x) for x in ["EGI", "C", "A", "D", "JK", "N", "B", "FL", "M", "H"]],
    "limb-fracture-dislocation-g09": [set(x) for x in ["BCD", "AE", "F"]],
}

EXPECTED_FILL = [
    ["1", "45"], ["30", "50"], ["10"], ["5"], ["3"], ["2", "4", "8", "10"],
    ["45", "60", "90"], ["12", "15"], ["3", "3"], ["0.5"], ["1/4", "1/3"],
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-limb-fracture-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 10
    assert sum(len(group["stems"]) for group in groups) == 86
    assert sum(len(group["options"]) for group in groups) == 111
    assert payload["meta"]["lecturePagesReviewed"] == list(range(1, 16))
    assert [group["id"] for group in groups[:9]] == list(EXPECTED_SOURCE_ANSWERS)

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-28"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True and group["parseWarnings"] == []
        assert group["sourcePdf"] is None and group["sourceImage"] is None
        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-28"
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"
        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    for group in groups[:9]:
        assert group["kindLabel"] == "B型题" and group["optionShuffleVersion"] == 2
        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert source_keys != group["optionOriginalOrder"]
        assert set(source_keys) == set(group["optionOriginalOrder"])
        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [{display_to_source[key] for key in stem["answer"]} for stem in group["stems"]]
        assert semantic_answers == EXPECTED_SOURCE_ANSWERS[group["id"]], f"{group['id']}: answer remapping drift"
        assert all(stem["answer"] and set(stem["answer"]) <= set(option_keys) for stem in group["stems"])

    fill = groups[9]
    assert fill["kind"] == "FILL" and fill["kindLabel"] == "填空题"
    assert fill["options"] == [] and fill["optionOriginalOrder"] == []
    assert [stem["answer"] for stem in fill["stems"]] == EXPECTED_FILL
    assert all(len(stem["answer"]) == len(stem["blankLabels"]) for stem in fill["stems"])

    print({"groups": 10, "stems": 86, "options": 111, "shuffled": 9, "fill": 1, "status": "ok"})


if __name__ == "__main__":
    main()
