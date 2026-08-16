#!/usr/bin/env python3
"""Finalize the audited pathology payload and attach per-stem lecture evidence.

The source question booklet is concise and sometimes uses several stacked
matching tables on one page.  This post-processor keeps the manually verified
repairs and lecture-page mapping deterministic without re-running OCR.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "src/data/pathology-data.json"


# Each tuple is the first lecture page for each stem in the group.  Adjacent
# stems often share one page because the lecture itself presents a comparison
# table.  These locations were checked against all 26 supplied lecture PDFs.
EVIDENCE_PAGES: dict[str, tuple[str, list[int]]] = {
    "p03-g1": ("lecture-01", [2, 2]), "p03-g2": ("lecture-01", [2, 2]),
    "p04-g1": ("lecture-03", [3, 5, 5]),
    "p05-g1": ("lecture-05", [7, 7, 7]),
    "p06-g1": ("lecture-05", [6, 6]), "p06-g2": ("lecture-06", [1, 1]),
    "p07-g1": ("lecture-07", [1, 1, 1, 1]), "p08-g1": ("lecture-07", [3, 3]),
    "p08-g2": ("lecture-09", [1, 1, 2, 2]), "p08-g3": ("lecture-10", [2, 1, 3]),
    "p09-g1": ("lecture-11", [9, 9, 9, 9]), "p09-g2": ("lecture-11", [9, 9]),
    "p09-g3": ("lecture-11", [9, 11, 11]), "p10-g1": ("lecture-11", [11, 11]),
    "p10-g2": ("lecture-14", [1, 1]), "p10-g3": ("lecture-14", [1, 1, 1]),
    "p10-g4": ("lecture-14", [4, 4, 4, 4, 4]),
    "p11-g1": ("lecture-16", [3, 3]), "p11-g2": ("lecture-16", [3, 3]),
    "p11-g3": ("lecture-16", [3, 3, 3, 3]), "p12-g1": ("lecture-16", [1, 1, 1, 2]),
    "p12-g2": ("lecture-16", [2, 2]),
    "p13-g1": ("lecture-17", [4, 4, 4, 4]), "p13-g2": ("lecture-17", [4, 4, 4]),
    "p13-g3": ("lecture-17", [5, 5, 5, 5]), "p14-g1": ("lecture-17", [4, 4, 4]),
    "p14-g2": ("lecture-18", [2, 2]), "p14-g3": ("lecture-18", [3] * 8),
    "p15-g1": ("lecture-18", [6, 6, 6]), "p16-g1": ("lecture-18", [7, 7]),
    "p16-g2": ("lecture-18", [8, 8, 8]), "p17-g1": ("lecture-18", [8, 8]),
    "p17-g2": ("lecture-18", [9, 9]), "p17-g3": ("lecture-18", [9, 9]),
    "p17-g4": ("lecture-18", [10, 10]), "p18-g1": ("lecture-19", [2] * 7),
    "p18-g2": ("lecture-19", [2] * 5),
    "p19-g1": ("lecture-20", [1, 1, 1]), "p20-g1": ("lecture-20", [3, 3, 4, 4, 4, 5]),
    "p21-g1": ("lecture-21", [1, 1]), "p21-g2": ("lecture-21", [2, 2]),
    "p22-g1": ("lecture-21", [2, 2, 2, 2]), "p22-g2": ("lecture-21", [3, 3]),
    "p23-g1": ("lecture-21", [6] * 10), "p23-g2": ("lecture-21", [6] * 10),
    "p24-g1": ("lecture-22", [1, 1, 1]), "p24-g2": ("lecture-22", [4, 4]),
    "p24-g3": ("lecture-22", [5, 5]),
    "p25-g1": ("lecture-23", [1, 1, 13, 13]), "p25-g2": ("lecture-23", [2] * 9),
    "p26-g1": ("lecture-23", [3, 3]), "p26-g2": ("lecture-23", [4, 4]),
    "p26-g3": ("lecture-23", [8, 8]), "p26-g4": ("lecture-23", [9, 9, 9]),
    "p27-g1": ("lecture-23", [9] * 7), "p27-g2": ("lecture-23", [9, 9, 10, 10, 10, 10]),
    "p28-g1": ("lecture-23", [10, 10, 10]), "p28-g2": ("lecture-23", [9, 9, 11, 11]),
    "p28-g3": ("lecture-23", [11, 11, 11, 11, 12]), "p29-g1": ("lecture-23", [12, 12]),
    "p30-g1": ("lecture-24", [2, 2]), "p30-g2": ("lecture-24", [3, 3, 3, 3]),
    "p31-g1": ("lecture-25", [4, 4, 5, 4, 4, 4, 5]),
    "p32-g1": ("lecture-25", [5, 5]), "p32-g2": ("lecture-25", [7] * 6),
    "p32-g3": ("lecture-25", [12] * 5),
    "p33-g1": ("lecture-26", [4, 4]), "p33-g2": ("lecture-26", [9, 9]),
    "p34-g1": ("lecture-26", [10] * 27), "p35-g1": ("lecture-26", [12] * 14),
    "p35-g2": ("lecture-26", [13] * 7), "p36-g1": ("lecture-26", [13] * 9),
    "p36-g2": ("lecture-26", [13] * 5), "p37-g1": ("lecture-26", [13] * 4),
    "p37-g2": ("lecture-26", [13, 13]),
}


def option(key: str, label: str) -> dict:
    return {"key": key, "label": label, "sourceText": f"{key}.{label}"}


def stem(text: str, answer: str) -> dict:
    return {
        "text": text,
        "answer": list(answer),
        "answerMode": "多选" if len(answer) > 1 else "单选",
        "sourceText": f"{text}（{answer}）",
        "sourceY": None,
    }


def make_evidence(lecture_id: str, page: int, lecture_title: str) -> dict:
    number = int(lecture_id.removeprefix("lecture-"))
    return {
        "lectureId": lecture_id,
        "page": page,
        "image": f"pathology/lecture-pages/{lecture_id}-page-{page:02d}.webp",
        "title": f"第{number}讲第{page}页：{lecture_title}",
        "description": f"本题对应第{number}讲第{page}页讲义。",
    }


def repair_and_restore(groups: list[dict]) -> list[dict]:
    groups = [group for group in groups if group["id"] not in {"p05-g2", "p19-g2"}]
    by_id = {group["id"]: group for group in groups}

    # Correct visible OCR glyphs while retaining the source booklet's answer key.
    text_repairs = {
        ("p03-g1", "E"): "血维生素B12↓", ("p03-g1", "F"): "血胃泌素↓",
        ("p06-g1", "H"): "胃酸多正常或↓", ("p06-g1", "J"): "胃酸明显↓（缺乏）",
        ("p06-g1", "A"): "黏膜皱襞呈放射状向溃疡集中",
        ("p06-g1", "F"): "周围黏膜皱襞中断，结节状肥厚",
        ("p09-g1", "A"): "终末细支气管、一级呼吸性细支气管管腔狭窄",
        ("p09-g1", "F"): "炎症所致氧自由基增多→α1-抗胰蛋白酶减少",
        ("p09-g1", "H"): "遗传性α1-抗胰蛋白酶缺乏",
        ("p05-g1", "B"): "Turcot综合征（胶质瘤-息肉病综合征）",
        ("p05-g1", "O"): "绒毛状腺瘤",
        ("p29-g1", "J"): "生化特征为琼脂凝胶电泳呈梯状带（DNA规律降解）",
        ("p29-g1", "Q"): "核固缩、核碎裂、核染色质边集（凋亡小体含核碎片和细胞器成分）",
    }
    for (group_id, key), label in text_repairs.items():
        item = next(item for item in by_id[group_id]["options"] if item["key"] == key)
        item.update(option(key, label))

    by_id["p05-g1"]["title"] = "大肠癌癌前病变与腺瘤"
    by_id["p05-g1"]["sourceText"] = " | ".join([
        *(row["sourceText"] for row in by_id["p05-g1"]["options"]),
        *(row["sourceText"] for row in by_id["p05-g1"]["stems"]),
    ])
    by_id["p29-g1"]["title"] = "坏死与凋亡"
    by_id["p37-g2"]["title"] = "原癌基因与抑癌基因"

    # Page 5 contains a second complete matching group that the original OCR
    # merged into p05-g1's source text.
    gene_group = {
        "id": "p05-g2", "page": 5, "title": "与大肠癌密切相关的基因",
        "kind": "B", "kindLabel": "B型题", "topic": "消化系统",
        "lectureIds": ["lecture-05"],
        "options": [
            option("A", "DPC"), option("B", "RAS"), option("C", "MSH"),
            option("D", "p53"), option("E", "MCC"), option("F", "APC"),
            option("G", "c-MYC"), option("H", "DCC"), option("I", "BRAF"),
            option("J", "MLH"), option("K", "p16"),
        ],
        "stems": [
            stem("原癌基因", "BGI"), stem("抑癌基因", "ADEFHK"),
            stem("错配修复基因", "CJ"), stem("与大肠癌关系最密切的三个基因", "FBD"),
            stem("与遗传性腺瘤性息肉病相关的基因", "F"),
            stem("与遗传性非息肉病性大肠癌/Lynch综合征相关的基因", "C"),
        ],
    }
    gene_group["sourceText"] = " | ".join([
        *(row["sourceText"] for row in gene_group["options"]),
        *(row["sourceText"] for row in gene_group["stems"]),
    ])

    # Page 19 likewise has a second complete primary-vs-secondary TB group.
    tb = by_id["p19-g1"]
    component_options = [
        option("A", "干酪样坏死、空洞"), option("B", "血清反应等免疫应答"),
        option("C", "皮肤红斑和结核菌素试验PPD阳性"),
    ]
    tb["options"] = component_options
    tb["title"] = "结核杆菌细胞壁成分"
    tb["sourceText"] = " | ".join([
        *(row["sourceText"] for row in component_options), *(row["sourceText"] for row in tb["stems"]),
    ])
    tb_group = {
        "id": "p19-g2", "page": 19, "title": "原发性与继发性肺结核",
        "kind": "B", "kindLabel": "B型题", "topic": "传染病",
        "lectureIds": ["lecture-20"],
        "options": [
            option("A", "机体初次感染结核杆菌，无特异免疫力"),
            option("B", "病变常从右肺尖开始，自上而下主要经支气管播散，病变上重下轻、上旧下新"),
            option("C", "好发于儿童"), option("D", "常伴空洞"),
            option("E", "基本病理特征为原发复合征（X线呈哑铃影）"),
            option("F", "若合并AIDS，好发于下叶"),
            option("G", "机体再次感染结核杆菌（内源复发为主），有免疫力"),
            option("H", "肺内原发灶位于上叶下部、下叶上部近胸膜处"),
            option("I", "病变多局限于肺内"),
            option("J", "若合并AIDS，趋于原发性肺结核：肺门、纵隔淋巴结肿大，空洞少见"),
            option("K", "有结核性淋巴管炎"), option("L", "好发于成人，尤其抵抗力低下者"),
            option("M", "若合并AIDS，PPD常呈阴性或弱阳性"),
            option("N", "肺门淋巴结结核：多为单侧肿大，常伴干酪样坏死"),
            option("O", "好发于上叶尖后段、下叶背段和后基底段"),
            option("P", "主要经淋巴道或血道播散"), option("Q", "若合并AIDS，肉芽肿少见"),
        ],
        "stems": [stem("原发性肺结核", "ACEHKNP"), stem("继发性肺结核", "BDFGIJLMOQ")],
    }
    tb_group["sourceText"] = " | ".join([
        *(row["sourceText"] for row in tb_group["options"]), *(row["sourceText"] for row in tb_group["stems"]),
    ])

    restored = []
    for group in groups:
        restored.append(group)
        if group["id"] == "p05-g1":
            restored.append(gene_group)
        if group["id"] == "p19-g1":
            restored.append(tb_group)
    return restored


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    payload["groups"] = repair_and_restore(payload["groups"])
    lecture_titles = {item["id"]: item["title"] for item in payload["lectures"]}

    # Add the two restored group mappings alongside the manually verified map.
    evidence_pages = dict(EVIDENCE_PAGES)
    evidence_pages["p05-g2"] = ("lecture-05", [8] * 6)
    evidence_pages["p19-g2"] = ("lecture-20", [2, 3])

    for group in payload["groups"]:
        lecture_id, pages = evidence_pages[group["id"]]
        if len(pages) != len(group["stems"]):
            raise ValueError(f"{group['id']} evidence count {len(pages)} != {len(group['stems'])}")
        group["reviewState"] = "已按题册原图与讲义逐题复核"
        for row, page in zip(group["stems"], pages, strict=True):
            row["lectureEvidence"] = make_evidence(lecture_id, page, lecture_titles[lecture_id])
        group["lectureEvidence"] = group["stems"][0]["lectureEvidence"]

    payload["meta"].update({
        "generatedBy": "scripts/build_pathology_content.py + scripts/finalize_pathology_content.py",
        "groups": len(payload["groups"]),
        "stems": sum(len(group["stems"]) for group in payload["groups"]),
        "lectureEvidenceStems": sum(len(group["stems"]) for group in payload["groups"]),
        "auditState": "题册原页与讲义逐题复核完成",
    })
    args.data.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
