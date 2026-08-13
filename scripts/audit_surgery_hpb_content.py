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

    group9 = by_id["p19-g1"]
    assert {option["key"]: option["label"] for option in group9["options"]} == {
        "A": "质地硬、杂质少", "B": "X线常显影", "C": "剖面呈放射状",
        "D": "剖面呈放射状、层状", "E": "质地软、杂质多",
        "F": "X线常不显影", "G": "胆固醇类结石", "H": "胆色素结石",
        "I": "几乎在胆囊", "J": "多在胆管", "K": "X线部分显影",
    }
    assert {stem["text"]: "".join(stem["answer"]) for stem in group9["stems"]} == {
        "纯胆固醇结石": "CFG", "混合性结石": "BDG",
        "黑色素结石": "AHIK", "棕色结石": "EHJK",
        "碳酸钙、磷酸钙、棕榈酸钙等": "B",
    }
    assert group9["lectureEvidence"] == {
        "lectureId": "lecture-16", "page": 1,
        "image": "surgery/lecture-pages/lecture-16-page-01.webp",
        "title": "第16讲第1页 · 胆系结石分类",
        "description": "讲义表格明确：黑色素结石和棕色结石均为X线部分显影。",
    }
    assert (root / "public" / group9["lectureEvidence"]["image"]).exists()

    group26 = by_id["p23-g2"]
    assert {option["key"]: option["label"] for option in group26["options"]} == {
        "A": "经皮穿刺进入肝内胆管，置管减压并持续引流",
        "B": "联合切除胰头、十二指肠及相关胆道等组织的根治性术式",
        "C": "经腹腔镜切除胆囊",
        "D": "深吸气时触及无痛、光滑、肿大的胆囊：见于中下段胆管癌、胰头癌、壶腹癌、十二指肠癌",
        "E": "利用磁共振水成像无创显示胰胆管形态",
        "F": "胆管急性梗阻并发化脓性感染，典型可出现Reynolds五联征",
        "G": "经十二指肠镜逆行插管造影以观察胰胆管",
        "H": "内镜下切开Oddi括约肌并取石，术后留置鼻胆管引流",
        "I": "经皮穿刺进入胆囊，置管减压并持续引流",
    }
    assert {stem["text"]: "".join(stem["answer"]) for stem in group26["stems"]} == {
        "AOSC": "F", "LC": "C", "PTGD": "I", "PTCD": "A",
        "MRCP": "E", "治疗性ERCP": "H", "Whipple术": "B", "Courvoisier征": "D",
    }
    answer_hints = ("AOSC", "LC", "PTGD", "PTCD", "MRCP", "ERCP",
                    "Whipple", "Courvoisier", "EST", "ENBD")
    assert not any(
        hint.casefold() in option["label"].casefold()
        for option in group26["options"]
        for hint in answer_hints
    )
    assert group26["lectureEvidence"]["page"] == 12
    assert (root / "public" / group26["lectureEvidence"]["image"]).exists()

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
