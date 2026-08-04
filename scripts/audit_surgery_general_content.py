#!/usr/bin/env python3
"""Validate surgery-general question modes, answers, and lecture evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path


FILL_GROUPS = {
    "surgery-general-p02b": 8,
    "surgery-general-p03b": 6,
    "surgery-general-p05": 8,
    "surgery-general-p06": 7,
    "surgery-general-a10": 4,
    "surgery-general-a11a": 2,
    "surgery-general-a11b": 3,
}
RANKING_GROUPS = {
    "surgery-general-a09": ["ABDC", "BDCA", "DBCA", "BDCA", "CDAB", "CDBA", "DBCA"],
    "surgery-general-a12": ["ABCDE", "EDCBA"],
}
REQUIRED_GROUPS = {
    "surgery-general-p01", "surgery-general-p02a", "surgery-general-p02b",
    "surgery-general-p03a", "surgery-general-p03b", "surgery-general-p04",
    "surgery-general-p05", "surgery-general-p06", "surgery-general-p07",
    "surgery-general-p08", "surgery-general-p09", "surgery-general-p10a",
    "surgery-general-p10b", "surgery-general-a01", "surgery-general-a02",
    "surgery-general-a03", "surgery-general-a04", "surgery-general-a05",
    "surgery-general-a06", "surgery-general-a07", "surgery-general-a08",
    "surgery-general-a09", "surgery-general-a10", "surgery-general-a11a",
    "surgery-general-a11b", "surgery-general-a12", "surgery-general-a13",
    "surgery-general-a14", "surgery-general-a15", "surgery-general-a16",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-general-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    by_id = {group["id"]: group for group in groups}

    assert payload["topics"] == ["外科总论"]
    assert len(groups) == 30
    assert len(by_id) == len(groups)
    assert set(by_id) == REQUIRED_GROUPS
    assert sum(len(group["stems"]) for group in groups) == 136
    assert sum(len(group["options"]) for group in groups) == 187

    forbidden = re.compile(r"\s{2,}|[|°•“”‘’]")
    for group in groups:
        assert group["page"] == 0
        assert group["topic"] == "外科总论"
        assert group["hideSource"] is True
        assert group["reviewState"] == "已完成结构校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert not {"sourcePage", "sourceName", "sourceDocument"} & set(group)

        keys = [option["key"] for option in group["options"]]
        assert len(keys) == len(set(keys))
        assert all(option["label"] and option["label"] == option["label"].strip() for option in group["options"])
        if group["options"]:
            source_keys = [option["sourceKey"] for option in group["options"]]
            assert group["optionShuffleVersion"] == 1
            assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options were not shuffled"
            assert set(source_keys) == set(group["optionOriginalOrder"])
        for stem in group["stems"]:
            assert stem["text"] and stem["text"] == stem["text"].strip()
            assert stem["answer"]
            if stem["answerMode"] not in {"填空", "排序"}:
                assert set(stem["answer"]) <= set(keys)

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(forbidden.search(value) for value in values), f"{group['id']}: punctuation or spacing issue"

        evidence = group["lectureEvidence"]
        assert group["lectureIds"] == [evidence["lectureId"]]
        assert evidence["lectureId"] in {"lecture-35", "lecture-36"}
        assert (root / "public" / evidence["image"]).exists()

    for group_id, stem_count in FILL_GROUPS.items():
        group = by_id[group_id]
        assert group["kind"] == "FILL" and group["kindLabel"] == "填空题"
        assert not group["options"] and len(group["stems"]) == stem_count
        assert all(stem["answerMode"] == "填空" for stem in group["stems"])
        assert all(len(stem["blankLabels"]) == len(stem["answer"]) for stem in group["stems"])

    for group_id, expected_answers in RANKING_GROUPS.items():
        group = by_id[group_id]
        assert group["kind"] == "RANK" and group["kindLabel"] == "排序题"
        assert all(stem["answerMode"] == "排序" for stem in group["stems"])
        current_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = ["".join(current_to_source[key] for key in stem["answer"]) for stem in group["stems"]]
        assert semantic_answers == expected_answers

    assert {option["sourceKey"]: option["label"] for option in by_id["surgery-general-a09"]["options"]} == {
        "A": "普鲁卡因", "B": "丁卡因", "C": "利多卡因", "D": "罗哌卡因、布比卡因"
    }
    assert {option["sourceKey"]: option["label"] for option in by_id["surgery-general-a12"]["options"]} == {
        "A": "交感神经", "B": "副交感神经", "C": "感觉神经", "D": "运动神经", "E": "本体感觉"
    }

    p10a = by_id["surgery-general-p10a"]
    p10a_map = {option["key"]: option["sourceKey"] for option in p10a["options"]}
    assert ["".join(p10a_map[key] for key in stem["answer"]) for stem in p10a["stems"]] == [
        "ABC", "D", "E", "F", "G", "H", "I", "J"
    ]
    p10b = by_id["surgery-general-p10b"]
    p10b_map = {option["key"]: option["sourceKey"] for option in p10b["options"]}
    assert ["".join(p10b_map[key] for key in stem["answer"]) for stem in p10b["stems"]] == [
        "A", "BC", "D", "EFGHI", "JK", "L"
    ]

    all_ids = []
    for filename in ["surgery-data.json", "surgery-fracture-data.json", "surgery-general-data.json"]:
        data = json.loads((root / "src/data" / filename).read_text(encoding="utf-8"))
        all_ids.extend(group["id"] for group in data["groups"])
    assert len(all_ids) == len(set(all_ids)), "duplicate surgery group ids"

    print({"groups": 30, "stems": 136, "options": 187, "fill": 7, "ranking": 2, "status": "ok"})


if __name__ == "__main__":
    main()
