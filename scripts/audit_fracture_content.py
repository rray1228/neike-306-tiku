#!/usr/bin/env python3
"""Validate the imported fracture overview question bank and its evidence files."""

from __future__ import annotations

import json
import re
from pathlib import Path


EXPECTED = {
    "fracture-g01": ("ABCDEFGHIJKL", [("直接暴力", "CG"), ("间接暴力（受伤部位远处）", "AEIK"), ("病理骨折", "D"), ("疲劳/应力/行军骨折", "BFHJL")]),
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


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-fracture-data.json").read_text(encoding="utf-8"))
    groups = payload["groups"]
    assert len(groups) == 13
    assert sum(len(group["stems"]) for group in groups) == 46
    assert sum(len(group["options"]) for group in groups) == 129
    assert [group["id"] for group in groups] == list(EXPECTED)

    for group in groups:
        group_id = group["id"]
        expected_options, expected_stems = EXPECTED[group_id]
        option_keys = "".join(option["key"] for option in group["options"])
        display_to_source = {option["key"]: option["sourceKey"] for option in group["options"]}
        actual_stems = [
            (stem["text"], "".join(sorted(display_to_source[key] for key in stem["answer"])))
            for stem in group["stems"]
        ]
        assert option_keys == expected_options, f"{group_id}: option keys drift"
        assert actual_stems == expected_stems, f"{group_id}: stems or answers drift"
        assert len(option_keys) == len(set(option_keys)), f"{group_id}: duplicate option keys"
        source_keys = [option["sourceKey"] for option in group["options"]]
        assert sorted(source_keys) == sorted(group["optionOriginalOrder"]), f"{group_id}: source option drift"
        assert source_keys != group["optionOriginalOrder"], f"{group_id}: options remain in lecture order"
        assert group["optionShuffleVersion"] == 2
        assert group["topic"] == "骨科"
        assert group["lectureIds"] == ["lecture-29"]
        assert group["reviewState"] == "已完成结构校对"
        assert not group["reviewIssues"]
        assert group["hideSource"] is True
        assert not group["reviewNotes"]
        assert not {"sourcePage", "sourceName", "sourceDocument"} & set(group)
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

    fifth = next(group for group in groups if group["id"] == "fracture-g05")
    assert [option["label"] for option in sorted(fifth["options"], key=lambda option: option["sourceKey"])] == [
        "局部无异常活动",
        "局部无压痛",
        "无纵向叩击痛",
        "X线见骨折处有连续性梭形骨痂（骨折线模糊）",
    ]

    first = next(group for group in groups if group["id"] == "fracture-g01")
    assert [option["label"] for option in sorted(first["options"], key=lambda option: option["sourceKey"])] == [
        "肱骨髁上骨折",
        "好发于第2、3跖骨",
        "胫骨干骨折",
        "骨骼本身存在骨髓炎、骨肿瘤等疾病，受轻微外力即发生骨折",
        "髂前上棘撕脱骨折",
        "早期诊断可用MRI、核素检查",
        "髌骨粉碎性骨折",
        "好发于肋骨",
        "桡骨远端骨折",
        "反复轻微外力导致特定部位积累性劳损",
        "髌骨横形骨折",
        "好发于腓骨干下1/3",
    ]
    assert {key for stem in first["stems"] for key in stem["answer"]} == set("ABCDEFGHIJKL")

    print({"groups": 13, "stems": 46, "options": 129, "status": "ok"})


if __name__ == "__main__":
    main()
