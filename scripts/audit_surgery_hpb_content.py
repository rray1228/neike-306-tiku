#!/usr/bin/env python3
"""Audit the cleaned hepatobiliary-pancreatic surgery section."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "src/data/surgery-data.json").read_text(encoding="utf-8"))
    groups = [group for group in payload["groups"] if group.get("topic") == "肝胆胰疾病"]
    by_id = {group["id"]: group for group in groups}

    assert len(groups) == 26
    forbidden = ("门脉压力个", "再出血率」", "血WBC个", "WBC可个", "支气管胸膜痿", "支气管胆痿", "PTC检查后引流 ｛")
    visible_text = "\n".join(
        [group["title"] for group in groups]
        + [option["label"] for group in groups for option in group["options"]]
        + [stem["text"] for group in groups for stem in group["stems"]]
    )
    assert not any(value in visible_text for value in forbidden)

    group6 = by_id["p18-g2"]
    assert {option["key"]: option["label"] for option in group6["options"]} == {
        "A": "门静脉压力↑", "B": "再出血率↓", "C": "临床常用",
        "D": "肠系膜上静脉-下腔静脉分流术", "E": "门静脉-腔静脉建立分流通道",
        "F": "脾切除＋贲门周围血管离断术", "G": "肝性脑病发生率较低",
        "H": "肝性脑病发生率较高", "I": "对肝功能打击较大",
        "J": "阻断门静脉-奇静脉反常血流", "K": "门静脉-下腔静脉分流术",
        "L": "近端脾静脉-肾静脉分流术", "M": "远端脾静脉-肾静脉分流术",
        "N": "门静脉压力↓", "O": "再出血率↑", "P": "对肝功能打击较小",
    }
    assert {stem["text"]: "".join(stem["answer"]) for stem in group6["stems"]} == {
        "断流术": "ACFGJOP", "分流术": "BEIN", "选择性分流术": "GM", "非选择性分流术": "HDKL",
    }
    assert group6["lectureEvidence"]["page"] == 3
    assert (root / "public" / group6["lectureEvidence"]["image"]).exists()

    composite_keys = {option["key"] for option in by_id["p23-g1"]["options"]}
    assert not composite_keys.intersection({"a", "b", "d", "e"})
    assert {"①", "②", "③", "④"}.issubset(composite_keys)

    valid_answers = []
    for group in groups:
        keys = {option["key"] for option in group["options"]}
        for stem in group["stems"]:
            invalid = set(stem["answer"]) - keys
            if invalid:
                valid_answers.append(f'{group["id"]}:{stem["text"]}:{sorted(invalid)}')
    assert not valid_answers, valid_answers

    print({"groups": len(groups), "stems": sum(len(group["stems"]) for group in groups), "status": "ok"})


if __name__ == "__main__":
    main()
