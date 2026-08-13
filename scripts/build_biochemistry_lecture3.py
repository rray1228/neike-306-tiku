#!/usr/bin/env python3
"""Generate the checked question-bank payload for biochemistry lecture 03."""

from __future__ import annotations

import json
from pathlib import Path


LECTURE_TITLE = "生化 磷酸戊糖途径、糖原、糖异生"


def letters(value: str) -> list[str]:
    return list(value)


def group(index, title, topic, options, stems, page):
    return {
        "id": f"bio-03-{index:02d}", "page": index, "title": title,
        "kind": "B", "kindLabel": "B型题",
        "options": [{"key": chr(65 + i), "label": label, "sourceText": f"{chr(65 + i)}. {label}"} for i, label in enumerate(options)],
        "stems": [{"number": i + 1, "text": text, "sourceText": f"{i + 1}. {text}", "answerRaw": answer, "answer": letters(answer), "answerMode": "多选" if len(answer) > 1 else "单选"} for i, (text, answer) in enumerate(stems)],
        "sourceText": title, "reviewState": "已按 2027 考研讲义核对", "reviewIssues": [], "reviewNotes": [], "topic": topic,
        "lectureIds": ["lecture-03"],
        "lectureEvidence": {
            "lectureId": "lecture-03", "lectureNumber": 3, "lectureTitle": LECTURE_TITLE, "page": page,
            "image": f"biochemistry/lecture-pages/lecture-03-page-{page:02d}.webp",
            "title": f"第 03 讲《{LECTURE_TITLE}》· 第 {page} 页",
            "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
            "method": "按知识点人工映射至 2027 考研生化第 03 讲，并逐项复核。",
        },
    }


def main():
    pentose = "磷酸戊糖途径"
    glycogen = "糖原合成与分解"
    gluconeogenesis = "糖异生"
    integration = "糖代谢关键酶与中间物"
    groups = [
        group(1, "磷酸戊糖途径", pentose, ["糖和核苷酸代谢联系枢纽", "蚕豆病", "磷酸戊糖途径", "G-6-P", "CO₂", "胆固醇的合成和分解", "胞浆", "2,3-BPG", "NADPH", "参与生物转化", "G-6-P 脱氢酶", "5-磷酸核糖", "合成胆红素、脂肪酸、氨基酸、神经鞘磷脂、脱氧核苷酸、FH₄ 等", "维持 GSH 还原状态等"], [("磷酸戊糖途径部位：", "G"), ("磷酸戊糖途径起始物：", "D"), ("磷酸戊糖途径关键酶：", "K"), ("磷酸戊糖途径产物：", "EIL"), ("G-6-P 脱氢酶缺陷致：", "B"), ("G-6-P 脱氢酶抑制剂：", "I"), ("5-磷酸核糖：", "A"), ("NADPH 的还原作用：", "N"), ("NADPH 可参与：", "J"), ("NADPH 参与的物质代谢：", "FM"), ("体内提供 NADPH 的主要代谢途径：", "C"), ("能够保护血红蛋白处于还原状态的物质：", "I")], 1),
        group(2, "糖原合成与分解：酶的作用", glycogen, ["糖原分解的关键酶", "G-1-P+UTP→UDPG+PPi", "糖原+Pi→G-1-P", "糖原合成的关键酶", "G-1-P⇋G-6-P", "UDPG→糖原+UDP"], [("磷酸葡萄糖变位酶", "E"), ("UDPG 焦磷酸化酶", "B"), ("糖原合酶", "DF"), ("磷酸化酶", "AC")], 2),
        group(3, "肝糖原与肌糖原", glycogen, ["肾上腺素（磷酸化）", "补充血糖（主要是 16 小时内）", "葡萄糖", "胰高血糖素（磷酸化）", "无氧氧化（缺乏 G-6-P 酶）", "快速为肌肉收缩供能（净生成 3 个 ATP）"], [("肝糖原", "BCD"), ("肌糖原", "AEF")], 2),
        group(4, "糖异生关键酶：作用与特点", gluconeogenesis, ["胞浆", "丙酮酸→草酰乙酸", "肌肉没有", "线粒体、胞浆", "生物素（VitB₇）", "G-6-P→G", "草酰乙酸→磷酸烯醇式丙酮酸", "线粒体", "果糖-1,6-二磷酸→果糖-6-磷酸"], [("丙酮酸羧化酶", "BEH"), ("磷酸烯醇式丙酮酸羧激酶", "DG"), ("果糖双磷酸酶-1", "AI"), ("G-6-P 酶", "ACF")], 3),
        group(5, "酶活性调节辨析", gluconeogenesis, ["丙酮酸激酶", "果糖-2,6-二磷酸", "糖皮质激素", "NADPH", "磷酸烯醇式丙酮酸羧激酶", "胰高血糖素", "乙酰 CoA（主要来自脂肪酸）", "磷酸果糖激酶-2", "雌激素", "果糖-1,6-二磷酸", "肾上腺素", "果糖双磷酸酶-2"], [("G6PD 的抑制剂", "D"), ("丙酮酸羧化酶的激活剂", "G"), ("果糖双磷酸酶-1 的抑制剂", "BJ"), ("胰高血糖素激活的酶", "EL"), ("胰高血糖素抑制的酶", "AH"), ("以下激素中，可促使血糖升高的有", "CFK")], 3),
        group(6, "糖异生原料：氨基酸辨析", gluconeogenesis, ["缬氨酸", "赖氨酸", "异亮氨酸", "苯丙氨酸", "色氨酸", "亮氨酸", "酪氨酸", "苏氨酸"], [("生酮氨基酸：只能生成酮体", "BF"), ("生糖兼生酮氨基酸", "CDEGH"), ("氨基酸（除开生酮氨基酸）", "ACDEGH")], 3),
        group(7, "糖异生：其他原料与意义", gluconeogenesis, ["避免乳酸堆积、酸中毒、损失能源物质", "步骤和耗能最少", "合成糖原（三碳途径）", "氨基酸（除开生酮氨基酸）", "甘油", "长期饥饿时肾维持酸碱平衡", "乳酸", "空腹饥饿时肝补充血糖（主要）", "甘油经甘油激酶→α-磷酸甘油，消耗 2 个高能磷酸键"], [("糖异生的原料", "DEG"), ("甘油", "BI"), ("乳酸/Cori 循环", "A"), ("糖异生的意义", "CFH")], 3),
        group(8, "糖代谢关键酶串联", integration, ["果糖双磷酸酶-1", "丙酮酸脱氢酶复合体", "糖原合酶", "α-酮戊二酸脱氢酶复合体", "己糖激酶", "G-6-P 酶（肌肉没有）", "异柠檬酸脱氢酶", "丙酮酸羧化酶", "丙酮酸激酶", "葡糖-6-磷酸脱氢酶 G6PD", "柠檬酸合酶", "磷酸果糖激酶-1", "磷酸化酶", "PEP 羧激酶"], [("糖酵解", "EIL"), ("丙酮酸脱羧→乙酰 CoA", "B"), ("三羧酸循环", "DGK"), ("磷酸戊糖途径", "J"), ("糖原合成", "C"), ("糖原分解", "M"), ("糖异生", "AFHN")], 4),
        group(9, "糖代谢重要中间物辨析", integration, ["磷酸戊糖", "UDPG", "6-磷酸葡萄糖酸内酯", "G-6-P", "果糖-1,6-二磷酸", "6-磷酸葡萄糖酸", "F-6-P"], [("联系糖酵解、磷酸戊糖途径、糖原合成与分解的关键物质", "D"), ("糖异生途径的重要中间产物是", "G"), ("糖原合成的重要中间产物是", "B"), ("糖酵解和磷酸戊糖途径共同的重要中间产物是", "D"), ("糖原合成和糖原分解途径共同的重要中间产物是", "D")], 4),
    ]
    payload = {
        "meta": {"title": "生物化学第 03 讲题库", "sourceLabel": "生化第 03 讲学成选择题（辨析修订版）", "sourcePages": 1, "lectureCount": 1, "groupCount": len(groups), "stemCount": sum(len(g["stems"]) for g in groups), "correctionGroupCount": 0, "generatedBy": "scripts/build_biochemistry_lecture3.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "仅收录第 03 讲《磷酸戊糖途径、糖原、糖异生》范围内题目；选项已逐组打散并按讲义复核。"},
        "topics": ["全部", pentose, glycogen, gluconeogenesis, integration, "综合"],
        "pages": [{"page": g["page"], "image": "", "topic": g["topic"], "searchText": g["title"]} for g in groups],
        "groups": groups,
        "lectures": [{"id": "lecture-03", "number": 3, "title": LECTURE_TITLE, "pageCount": 6}],
    }
    Path("src/data/biochemistry-lecture3-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(groups)} groups and {payload['meta']['stemCount']} stems")


if __name__ == "__main__":
    main()
