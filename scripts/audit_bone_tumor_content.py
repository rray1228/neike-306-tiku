#!/usr/bin/env python3
"""Validate the lecture-25 bone tumor question bank."""

from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path


EXPECTED_SOURCE_ANSWERS = {
    "bone-tumor-g01": [set("ACEGIKM"), set("BDFHJLNO")],
    "bone-tumor-g02": [set("C"), set("AEGH"), set("B"), set("F"), set("D")],
    "bone-tumor-g03": [
        {"B", "I", "M", "⑦", "㉓"},
        {"③", "⑩", "⑱", "㉒", "㉕"},
        {"O", "P", "S", "U", "⑤", "⑥", "⑭", "⑰"},
        {"E", "G", "㉓", "⑨", "⑯"},
        {"C", "N", "W", "㉔"},
        {"F", "L", "④"},
        {"F", "L", "②"},
        {"X", "⑲", "㉑"},
        {"D", "F", "H"},
        {"F", "Z"},
        {"K", "①", "⑪", "⑮"},
        {"Q", "T", "⑧"},
        {"J", "⑫", "㉓"},
        {"A", "⑬"},
    ],
}

CATEGORIES = ["性质", "好发部位与人群", "影像、症状与病理特点", "治疗"]
CATEGORY_COUNTS = {"性质": 6, "好发部位与人群": 9, "影像、症状与病理特点": 18, "治疗": 14}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-bone-tumor-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 3
    assert sum(len(group["stems"]) for group in groups) == 21
    assert sum(len(group["options"]) for group in groups) == 70
    assert [group["id"] for group in groups] == list(EXPECTED_SOURCE_ANSWERS)
    assert payload["meta"]["lecturePagesReviewed"] == list(range(1, 9))

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-25"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True
        assert group["optionShuffleVersion"] == 3

        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert len(option_keys) == len(set(option_keys))
        assert len(source_keys) == len(set(source_keys))
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in source order"
        if group["id"] == "bone-tumor-g03":
            assert set(source_keys) < set(group["optionOriginalOrder"])
        else:
            assert set(source_keys) == set(group["optionOriginalOrder"])

        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [
            {display_to_source[key] for key in stem["answer"]}
            for stem in group["stems"]
        ]
        assert semantic_answers == EXPECTED_SOURCE_ANSWERS[group["id"]], f"{group['id']}: answer remapping drift"
        for stem in group["stems"]:
            assert stem["answer"]
            assert set(stem["answer"]) <= set(option_keys)

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-25"
        assert evidence["page"] in {1, "1～3"}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    group3 = groups[2]
    category_order = list(dict.fromkeys(option["category"] for option in group3["options"]))
    assert category_order == CATEGORIES
    assert Counter(option["category"] for option in group3["options"]) == Counter(CATEGORY_COUNTS)
    assert all("category" not in option for group in groups[:2] for option in group["options"])
    assert all("category" in option for option in group3["options"])
    assert [option["key"] for option in group3["options"]] == group3["optionOriginalOrder"][: len(group3["options"])]
    duplicate_labels = [label for label, count in Counter(option["label"] for option in group3["options"]).items() if count > 1]
    assert duplicate_labels == []
    merged = {option["label"]: option["sourceAliases"] for option in group3["options"] if "sourceAliases" in option}
    assert merged == {
        "青少年多见，好发于长骨干骺端（股骨下端、胫骨上端等）": ["㉓", "⑳", "Y"],
        "手术治疗": ["F", "R", "V"],
    }

    labels = [option["label"] for option in group3["options"]]
    assert any("Codman三角" in label and "ALP" in label for label in labels)
    assert any("地舒单抗" in label for label in labels)
    assert any("阿司匹林" in label for label in labels)
    group2 = groups[1]
    biopsy = next(option for option in group2["options"] if option["sourceKey"] == "C")
    assert biopsy["label"] == "活检"
    assert any(biopsy["key"] in stem["answer"] for stem in group2["stems"] if stem["text"] == "骨肿瘤确诊金标准")
    print({"groups": 3, "stems": 21, "options": 70, "categorized_options": 47, "status": "ok"})


if __name__ == "__main__":
    main()
