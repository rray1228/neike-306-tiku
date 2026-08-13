#!/usr/bin/env python3
"""Build the lecture-21 chronic musculoskeletal injury question bank."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE_NAME = "运动系统慢性损伤_学成选择题_题目与答案.docx"

GROUPS = [
    {
        "id": "chronic-injury-g01",
        "title": "一般治疗原则",
        "page": 1,
        "pages": "1",
        "options": [
            ("A", "临床观察、理疗"),
            ("B", "NSAIDs：单独用"),
            ("C", "NSAIDs：短期间断用"),
            ("D", "选择性COX-2抑制剂塞来昔布、美洛昔康"),
            ("E", "减少胃黏膜损害"),
            ("F", "糖皮质激素：不能多次用"),
            ("G", "手术"),
        ],
        "stems": [("一般治疗原则", "ABCDEFG"), ("NSAIDs", "BCDE"), ("糖皮质激素", "F")],
        "order": "DAFCGBE",
        "image": "surgery/lecture-pages/lecture-21-page-01.webp",
        "evidenceTitle": "第21讲第1页：一般治疗原则",
    },
    {
        "id": "chronic-injury-g02",
        "title": "各疾病的临床表现、检查和特点",
        "page": "1～3",
        "pages": "1～3",
        "options": [
            ("A", "女性多见"), ("B", "左侧多见"),
            ("C", "肩关节外旋外展疼痛和受限"), ("D", "肩关节内旋后伸疼痛和受限"),
            ("E", "软组织退变"), ("F", "MRI用于诊断和鉴别诊断"),
            ("G", "6～24个月可自愈"), ("H", "肘关节外侧痛"),
            ("I", "Mills征"), ("J", "弹响指或扳机指"),
            ("K", "痛性结节"), ("L", "Finkelstein征"),
            ("M", "X线示胫骨结节骨骺增大、致密或碎裂"), ("N", "18岁后症状即消失"),
            ("O", "局部隆起不会改变"), ("P", "逐渐加重的髋部疼痛"),
            ("Q", "摇摆式跛行"), ("R", "髋关节屈曲挛缩试验或Thomas征"),
            ("S", "ECT有早期诊断意义"), ("T", "治疗关键时期为血供重建期"),
        ],
        "stems": [
            ("粘连性肩关节囊炎", "ABCDEFG"), ("肱骨外上髁炎（网球肘）", "HI"),
            ("狭窄性腱鞘炎", "JKL"), ("胫骨结节骨软骨病", "MNO"),
            ("股骨头骨软骨病", "PQRST"),
        ],
        "order": "LQCTHBNFPJESAOGRDMİK".replace("İ", "I"),
        "image": "surgery/lecture-pages/lecture-21-page-01-03.webp",
        "evidenceTitle": "第21讲第1～3页：疾病表现、检查和特点",
    },
    {
        "id": "chronic-injury-g03",
        "title": "治疗",
        "page": "1～3",
        "pages": "1～3",
        "options": [
            ("A", "每日做肩关节主动活动"), ("B", "不能用三角巾悬吊固定"),
            ("C", "无效可行关节镜松解术"), ("D", "限制腕关节活动"),
            ("E", "限制活动"), ("F", "NSAIDs"),
            ("G", "注射激素至腱鞘邻近的骨膜"), ("H", "无效可行腱鞘切开减压术"),
            ("I", "限制膝关节剧烈活动"), ("J", "关节内注射玻璃酸钠或透明质酸钠"),
            ("K", "慎用激素"), ("L", "激素不利于软骨修复"),
            ("M", "不宜注射激素"), ("N", "骨骺难以注入"),
            ("O", "治疗关键时期为血供重建期"),
        ],
        "stems": [
            ("粘连性肩关节囊炎", "ABC"), ("肱骨外上髁炎（网球肘）", "D"),
            ("狭窄性腱鞘炎", "EFGH"), ("髌骨软骨软化症", "IJKL"),
            ("胫骨结节骨软骨病", "MN"), ("股骨头骨软骨病", "O"),
        ],
        "order": "JCNFAOGDKMEIBLH",
        "image": "surgery/lecture-pages/lecture-21-page-01-03.webp",
        "evidenceTitle": "第21讲第1～3页：各病治疗",
    },
    {
        "id": "chronic-injury-g04",
        "title": "特殊体征和检查",
        "page": "1～3",
        "pages": "1～3",
        "options": [
            ("A", "Mills征"), ("B", "Finkelstein征"),
            ("C", "髋关节屈曲挛缩试验或Thomas征"), ("D", "MRI"),
            ("E", "ECT"), ("F", "X线示胫骨结节骨骺增大、致密或碎裂"),
        ],
        "stems": [
            ("肱骨外上髁炎", "A"), ("狭窄性腱鞘炎", "B"),
            ("股骨头骨软骨病：体征", "C"), ("粘连性肩关节囊炎：诊断和鉴别诊断", "D"),
            ("股骨头骨软骨病：早期诊断", "E"), ("胫骨结节骨软骨病：影像学", "F"),
        ],
        "order": "EBFADC",
        "image": "surgery/lecture-pages/lecture-21-page-01-03.webp",
        "evidenceTitle": "第21讲第1～3页：特殊体征和检查",
    },
    {
        "id": "chronic-injury-g05",
        "title": "肩痛及关节疾病鉴别诊断",
        "page": 4,
        "pages": "4",
        "options": [
            ("A", "50岁左右多见"), ("B", "肩关节活动受限、疼痛"),
            ("C", "症状向远端多不超过肘关节"), ("D", "X线示肩关节结构正常或骨质疏松"),
            ("E", "软组织退变，依靠MRI诊断"), ("F", "颈肩痛伴上肢放射痛"),
            ("G", "上肢麻木、无力"), ("H", "Eaton征和Spurling征"),
            ("I", "X线示椎间隙狭窄、骨质增生"), ("J", "椎间盘退变"),
            ("K", "中老年人"), ("L", "大关节和远端指间关节多见"),
            ("M", "X线示关节间隙变窄"), ("N", "软骨下骨硬化和囊变"),
            ("O", "关节边缘骨质增生"), ("P", "关节软骨退变"),
            ("Q", "青壮年男性多见"), ("R", "骶髂关节、脊柱、大关节多见"),
            ("S", "骶髂关节变窄、融合"), ("T", "竹节椎"),
            ("U", "青壮年女性多见"), ("V", "腕关节、掌指关节、近端指间关节多见"),
            ("W", "明显晨僵"), ("X", "多发、对称性"),
            ("Y", "落臂征"), ("Z", "疼痛弧"),
        ],
        "stems": [
            ("粘连性肩关节囊炎", "ABCDE"), ("神经根型颈椎病", "FGHIJ"),
            ("原发性骨关节炎", "KLMNOP"), ("强直性脊柱炎", "QRST"),
            ("类风湿关节炎", "UVWX"), ("肩袖损伤", "YZ"),
        ],
        "order": "HSCVKNDYATWFPLZGBUJEXMRIQO",
        "image": "surgery/lecture-pages/lecture-21-page-04.webp",
        "evidenceTitle": "第21讲第4页：肩痛及关节疾病鉴别表",
    },
]


def build_group(spec: dict) -> dict:
    source_options = dict(spec["options"])
    source_order = [key for key, _ in spec["options"]]
    display_keys = [chr(ord("A") + index) for index in range(len(source_order))]
    assert len(spec["order"]) == len(source_order)
    assert set(spec["order"]) == set(source_order)
    source_to_display = {source: display for display, source in zip(display_keys, spec["order"])}
    options = [
        {
            "key": display,
            "label": source_options[source],
            "sourceText": f"{source}. {source_options[source]}",
            "sourceKey": source,
            "ocrScore": 1,
        }
        for display, source in zip(display_keys, spec["order"])
    ]
    stems = []
    for text, answer in spec["stems"]:
        mapped = sorted(source_to_display[key] for key in answer)
        stems.append({
            "text": text,
            "answer": mapped,
            "answerMode": "多选" if len(mapped) > 1 else "单选",
            "sourceText": text,
            "ocrScore": 1,
            "reviewMethod": f"已按第21讲第{spec['pages']}页逐项校对并完成选项重映射",
        })
    return {
        "id": spec["id"],
        "page": 0,
        "title": spec["title"],
        "kind": "B",
        "kindLabel": "B型题",
        "options": options,
        "stems": stems,
        "reviewState": "已完成讲义校对",
        "reviewIssues": [],
        "topic": "骨科",
        "lectureIds": ["lecture-21"],
        "sourceName": SOURCE_NAME,
        "sourceText": spec["title"],
        "sourceImage": None,
        "sourcePdf": None,
        "sourcePage": None,
        "sourceAnswer": [answer for _, answer in spec["stems"]],
        "sourceStemNumbers": [str(index) for index in range(1, len(stems) + 1)],
        "parseWarnings": [],
        "hideSource": True,
        "reviewNotes": [],
        "lectureEvidence": {
            "lectureId": "lecture-21",
            "page": spec["page"],
            "image": spec["image"],
            "title": spec["evidenceTitle"],
            "description": "本题组已对照第21讲讲义原页逐项复核。",
        },
        "optionOriginalOrder": source_order,
        "optionShuffleVersion": 2,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = {
        "meta": {
            "title": "运动系统慢性损伤学成选择题",
            "lectureId": "lecture-21",
            "lecturePagesReviewed": [1, 2, 3, 4],
            "answerNote": "保持Word原有5个题组；剔除第二组中无任何对应选项、无法作答的髌骨软骨软化症空题干。其余题干、选项与答案已按第21讲逐项校对，选项固定打乱并同步重映射答案。",
        },
        "groups": [build_group(spec) for spec in GROUPS],
    }
    target = root / "src/data/surgery-chronic-injury-data.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"path": str(target), "groups": len(payload["groups"]), "stems": sum(len(group["stems"]) for group in payload["groups"])})


if __name__ == "__main__":
    main()
