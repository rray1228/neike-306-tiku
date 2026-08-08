#!/usr/bin/env python3
"""Validate the musculoskeletal deformity question bank and lecture evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "deformity-g01": [("先天性肌性斜颈", "A"), ("发育性髋关节脱位的重要病因", "BC"), ("发育性髋关节脱位站立前期的病理变化", "DEFGHI"), ("特发性脊柱侧凸", "J")],
    "deformity-g02": [("先天性肌性斜颈的临床表现", "ABC"), ("发育性髋关节脱位的好发特点", "DE"), ("发育性髋关节脱位的临床表现", "FGHIJKLMNOPQ"), ("发育性髋关节脱位的检查", "RST"), ("特发性脊柱侧凸的临床表现及后果", "UVWX")],
    "deformity-g03": [("先天性肌性斜颈＜1岁", "ABCD"), ("先天性肌性斜颈1岁后", "E"), ("发育性髋关节脱位：新生儿期（0～6个月）", "F"), ("发育性髋关节脱位：婴儿期（6个月～1.5岁）", "G"), ("发育性髋关节脱位：幼儿期（1.5～3岁）", "H"), ("发育性髋关节脱位：儿童期及以上（3岁以上）", "HI"), ("特发性脊柱侧凸：Cobb角＜20°", "J"), ("特发性脊柱侧凸：Cobb角20°～40°", "K"), ("特发性脊柱侧凸：Cobb角＞40°", "L")],
    "deformity-g05": [("Cobb角＞10°", "A"), ("Cobb角＜20°", "B"), ("Cobb角20°～40°", "C"), ("Cobb角＞40°", "D")],
    "deformity-g06": [("站立前期", "ABCDEFGHI"), ("站立行走期", "JKLM")],
    "deformity-g07": [("结构性脊柱侧凸", "A"), ("非结构性脊柱侧凸", "BCDEFGHI")],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-deformity-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    assert len(groups) == 7
    assert sum(len(group["stems"]) for group in groups) == 28
    assert sum(len(group["options"]) for group in groups) == 73
    assert [group["id"] for group in groups] == ["deformity-g01", "deformity-g02", "deformity-g03", "deformity-g04", "deformity-g05", "deformity-g06", "deformity-g07"]

    for group in groups:
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-20"]
        assert group["reviewState"] == "已完成讲义校对"
        assert group["hideSource"] is True
        assert not group["reviewIssues"] and not group["reviewNotes"]
        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-20"
        assert evidence["page"] in {1, 2}
        assert (root / "public" / evidence["image"]).exists(), f"{group['id']}: missing lecture image"
        values = [group["title"], group["sourceText"]]
        values += [option["label"] for option in group["options"]]
        values += [stem["text"] for stem in group["stems"]]
        assert not any(re.search(r"\s{2,}|[|•“”‘’]", value) for value in values), f"{group['id']}: punctuation or spacing issue"

        if group["id"] == "deformity-g04":
            assert group["kindLabel"] == "填空题" and not group["options"]
            assert [stem["answer"] for stem in group["stems"]] == [["1", "4"], ["1.5", "6", "45"]]
            continue

        assert group["optionShuffleVersion"] == 1
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert source_keys != group["optionOriginalOrder"], f"{group['id']}: options remain in lecture order"
        assert sorted(source_keys) == sorted(group["optionOriginalOrder"])
        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        actual = [(stem["text"], "".join(display_to_source[key] for key in stem["answer"])) for stem in group["stems"]]
        assert actual == EXPECTED[group["id"]], f"{group['id']}: answer remapping drift"

    print({"groups": 7, "stems": 28, "options": 73, "fill": 1, "shuffled": 6, "status": "ok"})


if __name__ == "__main__":
    main()
