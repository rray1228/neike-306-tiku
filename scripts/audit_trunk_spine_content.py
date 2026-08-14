#!/usr/bin/env python3
"""Validate the lecture-26 trunk fracture and spinal cord injury question bank."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED_SOURCE_ANSWERS = {
    "trunk-spine-g01": [
        set("D"), set("H"), set("BIJ"), set("CEM"), set("AL"), set("O"), set("H"),
        set("F"), set("P"), set("P"), set("K"), set("H"), set("GN"),
    ],
    "trunk-spine-g02": [set("BDFHIM"), set("AEGKLNO"), set("CGJP")],
    "trunk-spine-g03": [set("IL"), set("B"), set("K"), set("H"), set("C"), set("F"), set("DG"), set("EJ"), set("A")],
    "trunk-spine-g04": [set("C"), set("A"), set("B")],
    "trunk-spine-g05": [set("CF"), set("BHK"), set("DGI"), set("AEJ")],
    "trunk-spine-g06": [set("ACEF"), set("G"), set("D"), set("H"), set("B")],
    "trunk-spine-g07": [set("ABD"), set("ABC")],
    "trunk-spine-g08": [set("BCEIJQR"), set("DI"), set("AHL"), set("FGNP"), set("JKMO")],
}

EXPECTED_FILL = [
    ["10", "2"], ["1/3"], ["12"], ["6", "8", "12"],
    ["500", "5000"], ["3"], ["2", "4"], ["6", "8"],
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-trunk-spine-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload["groups"]

    assert len(groups) == 9
    assert sum(len(group["stems"]) for group in groups) == 52
    assert sum(len(group["options"]) for group in groups) == 88
    assert [group["id"] for group in groups[:8]] == list(EXPECTED_SOURCE_ANSWERS)
    assert groups[8]["id"] == "trunk-spine-g09"
    assert payload["meta"]["lecturePagesReviewed"] == list(range(1, 8))

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-26"]
        assert group["reviewState"] == "已完成讲义校对"
        assert not group["reviewIssues"] and not group["reviewNotes"]
        assert group["hideSource"] is True
        assert group["parseWarnings"] == []

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-26"
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"

        values = [group["title"], group["sourceText"]]
        values.extend(option["label"] for option in group["options"])
        values.extend(stem["text"] for stem in group["stems"])
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

    for group in groups[:8]:
        assert group["kindLabel"] == "B型题"
        assert group["optionShuffleVersion"] == 3
        option_keys = [option["key"] for option in group["options"]]
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert len(option_keys) == len(set(option_keys))
        assert len(source_keys) == len(set(source_keys))
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in source order"
        assert set(source_keys) == set(group["optionOriginalOrder"])

        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        semantic_answers = [{display_to_source[key] for key in stem["answer"]} for stem in group["stems"]]
        assert semantic_answers == EXPECTED_SOURCE_ANSWERS[group["id"]], f"{group['id']}: answer remapping drift"
        for stem in group["stems"]:
            assert stem["answer"] and set(stem["answer"]) <= set(option_keys)

    group3 = groups[2]
    assert len(group3["stems"]) == 9 and len(group3["options"]) == 12
    assert [stem["text"] for stem in group3["stems"]] == [
        "Jefferson骨折", "爆裂型骨折", "Hangman/缢死者骨折", "Whiplash挥鞭损伤", "Chance骨折",
        "骨盆骨折：临床表现", "骨盆骨折：休克及首要处理", "骨盆骨折：其他并发症", "骨盆骨折：不包括",
    ]
    assert not any("不选" in option["label"] for option in group3["options"])
    assert any(option["label"] == "脊髓损伤" for option in group3["options"])

    group2 = groups[1]
    whiplash = next(option for option in group2["options"] if option["sourceKey"] == "O")
    nonoperative, operative = group2["stems"][:2]
    assert whiplash["key"] not in nonoperative["answer"]
    assert whiplash["key"] in operative["answer"]

    fill = groups[8]
    assert fill["kind"] == "FILL" and fill["kindLabel"] == "填空题"
    assert fill["options"] == [] and fill["optionOriginalOrder"] == []
    assert [stem["answer"] for stem in fill["stems"]] == EXPECTED_FILL
    assert all(len(stem["answer"]) == len(stem["blankLabels"]) for stem in fill["stems"])
    assert all(stem["answerMode"] == "填空" for stem in fill["stems"])

    print({"groups": 9, "stems": 52, "options": 88, "shuffled": 8, "fill": 1, "status": "ok"})


if __name__ == "__main__":
    main()
