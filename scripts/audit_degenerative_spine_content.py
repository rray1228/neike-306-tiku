#!/usr/bin/env python3
"""Validate the lecture-27 degenerative cervical/lumbar spine question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_SOURCE_ANSWERS = {
    "degenerative-spine-g01": [set("BF"), set("ADFG"), set("CDEF")],
    "degenerative-spine-g02": [set("BDHILOR"), set("ACFGJKMN"), set("BPQ"), set("BE"), set("BS")],
    "degenerative-spine-g03": [set("FG"), set("EI"), set("A"), set("CH"), set("BD")],
    "degenerative-spine-g04": [set("F"), set("A"), set("C"), set("E"), set("B"), set("D")],
    "degenerative-spine-g05": [set("BDFHN"), set("AEJK"), set("CGILM")],
    "degenerative-spine-g06": [set("BDE"), set("ACEG"), set("H"), set("F")],
    "degenerative-spine-g07": [set("E"), set("E"), set("B"), set("B"), set("B"), set("ABC"), set("D")],
    "degenerative-spine-g08": [set("BE"), set("ACHJ"), set("FK"), set("DGI")],
}

EXPECTED_FILL = [["5", "6"], ["4", "5", "5", "1"]]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-degenerative-spine-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 9
    assert sum(len(group["stems"]) for group in groups) == 39
    assert sum(len(group["options"]) for group in groups) == 79
    assert payload["meta"]["lecturePagesReviewed"] == list(range(1, 11))
    assert [group["id"] for group in groups[:8]] == list(EXPECTED_SOURCE_ANSWERS)

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-27"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True and group["parseWarnings"] == []
        assert group["sourcePdf"] is None and group["sourceImage"] is None
        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-27"
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"
        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    for group in groups[:8]:
        assert group["kindLabel"] == "B型题" and group["optionShuffleVersion"] == 2
        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert source_keys != group["optionOriginalOrder"]
        assert set(source_keys) == set(group["optionOriginalOrder"])
        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [{display_to_source[key] for key in stem["answer"]} for stem in group["stems"]]
        assert semantic_answers == EXPECTED_SOURCE_ANSWERS[group["id"]], f"{group['id']}: answer remapping drift"
        assert all(stem["answer"] and set(stem["answer"]) <= set(option_keys) for stem in group["stems"])

    fill = groups[8]
    assert fill["kind"] == "FILL" and fill["kindLabel"] == "填空题"
    assert fill["options"] == [] and fill["optionOriginalOrder"] == []
    assert [stem["answer"] for stem in fill["stems"]] == EXPECTED_FILL
    assert all(len(stem["answer"]) == len(stem["blankLabels"]) for stem in fill["stems"])

    print({"groups": 9, "stems": 39, "options": 79, "shuffled": 8, "fill": 1, "status": "ok"})


if __name__ == "__main__":
    main()
