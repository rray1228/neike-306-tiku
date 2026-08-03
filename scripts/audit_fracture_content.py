#!/usr/bin/env python3
"""Validate the imported fracture overview question bank and its evidence files."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


EXPECTED = {
    "fracture-g01": ("ABCDEF", [("直接暴力", "A"), ("间接暴力（受伤部位远处）", "B"), ("病理骨折", "C"), ("疲劳/应力/行军骨折", "DEF")]),
    "fracture-g02": ("ABCDE", [("稳定性骨折（骨折端不易发生移位）", "ABCDE"), ("不完全骨折", "BD")]),
    "fracture-g03": ("ABCDEFGHIJKLMNO", [("开放性骨折是", "A"), ("开放性骨折首要处理", "BC"), ("清创一期愈合", "DE"), ("清创", "FGHIJKL"), ("粉碎性骨折", "MNO")]),
    "fracture-g04": ("ABCDEFGH", [("骨折特有体征", "ABC"), ("可不出现特有体征", "EFGH")]),
    "fracture-g05": ("ABCD", [("临床愈合标准", "ABCD")]),
    "fracture-g06": ("ABCDEFGHIJKL", [("血肿炎症机化期", "A"), ("原始骨痂形成期", "BCDEF"), ("延迟愈合", "G"), ("不愈合", "HI"), ("骨痂改造塑形期", "JKL")]),
    "fracture-g07": ("ABCDEFGHI", [("全身", "A"), ("局部", "BCDEFGHI"), ("骨折类型", "CD"), ("治疗方法", "EFGHI")]),
    "fracture-g08a": ("ABCDEFGHIJKLMN", [("早期并发症", "ABCD"), ("晚期并发症", "EFGHIJKLMN")]),
    "fracture-g08b": ("ABCDEFGHIJKL", [("休克", "ABC"), ("脂肪栓塞", "DE"), ("骨筋膜隔室综合征", "FGHIJKL")]),
    "fracture-g08c": ("ABCDEFGHIJKLM", [("主要与长期卧床有关", "AB"), ("感染", "C"), ("创伤性骨化/骨化性肌炎", "D"), ("创伤性关节炎", "E"), ("急性骨萎缩", "FGHI"), ("缺血性骨坏死", "J"), ("Volkmann缺血性肌挛缩", "KLM")]),
    "fracture-g09": ("ABCDE", [("旋转、成角、分离移位", "A"), ("长骨干横形骨折", "B"), ("干骺端骨折", "C"), ("缩短移位", "DE")]),
    "fracture-g10": ("ABCDEFGHIJKLMN", [("一般先", "A"), ("切开复位的优点", "BCDE"), ("切开复位的指征", "FGHIJKLMN")]),
    "fracture-g11": ("ABCDEF", [("外固定", "ABCD"), ("牵引", "ABCD"), ("内固定", "E"), ("功能锻炼", "F")]),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-fracture-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    assert len(groups) == 13
    assert sum(len(group["stems"]) for group in groups) == 46
    assert sum(len(group["options"]) for group in groups) == 123
    assert [group["id"] for group in groups] == list(EXPECTED)

    for group in groups:
        group_id = group["id"]
        expected_options, expected_stems = EXPECTED[group_id]
        option_keys = "".join(option["key"] for option in group["options"])
        actual_stems = [(stem["text"], "".join(stem["answer"])) for stem in group["stems"]]
        assert option_keys == expected_options, f"{group_id}: option keys drift"
        assert actual_stems == expected_stems, f"{group_id}: stems or answers drift"
        assert len(option_keys) == len(set(option_keys)), f"{group_id}: duplicate option keys"
        assert group["topic"] == "骨折概论"
        assert group["lectureIds"] == ["lecture-29"]
        assert group["reviewState"] == "已按Word题目答案表与讲义人工复核"
        assert not group["reviewIssues"]
        assert group["sourceDocument"] == "surgery/source-documents/骨折概论_学成选择题_题目与答案.docx"
        keys = set(option_keys)
        for option in group["options"]:
            assert option["label"].strip() == option["label"] and option["label"]
        for stem in group["stems"]:
            assert stem["text"].strip() == stem["text"] and stem["text"]
            assert stem["answer"] and set(stem["answer"]) <= keys
        values = [group["title"], group["sourceText"]]
        values += [option["label"] for option in group["options"]]
        values += [stem["text"] for stem in group["stems"]]
        assert not any(re.search(r"\s{2,}|[|°•“”‘’]", value) for value in values), f"{group_id}: punctuation or spacing issue"

        evidence = group["lectureEvidence"]
        assert evidence["lectureId"] == "lecture-29"
        assert (root / "public" / evidence["image"]).exists(), f"{group_id}: missing lecture image"

    fourth = next(group for group in groups if group["id"] == "fracture-g04")
    fifth = next(group for group in groups if group["id"] == "fracture-g05")
    assert fourth["reviewNotes"][0]["title"] == "答案编号勘误"
    assert fifth["reviewNotes"][0]["title"] == "补回Word漏组"
    assert [option["label"] for option in fifth["options"]] == [
        "局部无异常活动",
        "局部无压痛",
        "无纵向叩击痛",
        "X线见骨折处有连续性梭形骨痂（骨折线模糊）",
    ]

    source = root / "surgery/source-documents/骨折概论_学成选择题_题目与答案.docx"
    public_source = root / "public/surgery/source-documents/骨折概论_学成选择题_题目与答案.docx"
    assert source.exists() and public_source.exists()
    assert digest(source) == digest(public_source), "public Word source differs from audited source"

    print({"groups": 13, "stems": 46, "options": 123, "status": "ok"})


if __name__ == "__main__":
    main()
