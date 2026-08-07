#!/usr/bin/env python3
"""Generate the first biochemistry chapter payload from the revised workbook.

The source workbook is intentionally not copied into the website.  Each group
is linked to one rendered page from the 2027 lecture PDFs instead.
"""

from __future__ import annotations

import json
from pathlib import Path


def letters(value: str) -> list[str]:
    return list(value.replace("、", "").replace("，", "").replace(" ", ""))


def group(index, title, topic, options, stems, lecture, page, notes=None):
    return {
        "id": f"bio-01-{index:02d}", "page": index, "title": title,
        "kind": "B", "kindLabel": "B型题",
        "options": [{"key": chr(65 + i), "label": label, "sourceText": f"{chr(65+i)}. {label}"} for i, label in enumerate(options)],
        "stems": [{"number": i + 1, "text": text, "sourceText": f"{i+1}. {text}", "answerRaw": answer, "answer": letters(answer), "answerMode": "多选" if len(letters(answer)) > 1 else "单选"} for i, (text, answer) in enumerate(stems)],
        "sourceText": title,
        "reviewState": "已按 2027 考研讲义核对",
        "reviewIssues": [], "reviewNotes": notes or [], "topic": topic,
        "lectureIds": [f"lecture-{lecture:02d}"],
        "lectureEvidence": {
            "lectureId": f"lecture-{lecture:02d}", "lectureNumber": lecture,
            "lectureTitle": LECTURES[lecture - 1][1], "page": page,
            "image": f"biochemistry/lecture-pages/lecture-{lecture:02d}-page-{page:02d}.png",
            "title": f"第 {lecture} 讲《{LECTURES[lecture - 1][1]}》· 第 {page} 页",
            "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
            "method": "按知识点人工映射至 2027 考研生化讲义，并逐项复核。",
        },
    }


LECTURES = [
    (1, "生化 糖无氧氧化、糖有氧氧化、红细胞代谢、高能化合物"),
    (2, "生化 氧化磷酸化"),
    (3, "生化 磷酸戊糖途径、糖原、糖异生"),
]

CORRECTION_HIGH_ENERGY = [{
    "title": "答案校对 · 葡萄糖-1-磷酸不属于高能磷酸键",
    "body": "高能磷酸键应为 NDP/NTP、1,3-二磷酸甘油酸/PEP、磷酸肌酸、氨基甲酰磷酸和焦磷酸；G-1-P 为普通磷酸酯键。答案由 EFGHIJ 校正为 EFGHI。",
}]
CORRECTION_KETONE = [{
    "title": "答案校对 · 胆固醇不能生成酮体",
    "body": "胆固醇在人体内不能逆向分解为乙酰 CoA，不能作为酮体来源；酮体可由脂肪酸、亮氨酸/赖氨酸和乙酰 CoA 生成。答案由 ACDE 校正为 CDE。",
}]
CORRECTION_NADH = [{
    "title": "答案校对 · 谷氨酸脱氢酶的还原当量",
    "body": "谷氨酸脱氢酶催化氧化脱氨时以 NAD+ 为辅酶，生成 NADH+H+；不生成 NADPH。答案由 AC 校正为 C。",
}]


def main():
    glycolysis = "糖酵解与糖有氧氧化"
    gluconeogenesis = "磷酸戊糖途径、糖异生与调控"
    groups = [
        group(1, "糖酵解关键酶", glycolysis, ["PEP→丙酮酸、ATP", "G→G-6-P", "F-6-P→F-1,6-DP", "果糖-1,6-二磷酸", "葡萄糖", "AMP、ADP", "果糖-2,6-二磷酸（最强激活剂）", "ATP、丙氨酸", "G-6-P、长链脂酰 CoA", "ATP、柠檬酸"], [("丙酮酸激酶：①催化 ②激活剂 ③抑制剂", "ADH"), ("己糖激酶：①催化 ②激活剂 ③抑制剂", "BEI"), ("磷酸果糖激酶-1：①催化 ②激活剂 ③抑制剂", "CFGJ")], 1, 4),
        group(2, "关键酶与非关键酶", glycolysis, ["己糖激酶", "磷酸果糖激酶-1", "丙酮酸激酶", "丙酮酸脱氢酶复合体", "柠檬酸合酶", "异柠檬酸脱氢酶", "α-酮戊二酸脱氢酶复合体", "3-磷酸甘油醛脱氢酶", "磷酸甘油酸激酶", "乳酸脱氢酶 LDH", "琥珀酰 CoA 合成酶", "琥珀酸脱氢酶"], [("关键酶", "ABCDEFG"), ("非关键酶", "HIJKL")], 1, 5),
        group(3, "糖有氧氧化的关键酶", glycolysis, ["己糖激酶", "磷酸果糖激酶-1", "丙酮酸激酶", "丙酮酸脱氢酶复合体", "柠檬酸合酶", "异柠檬酸脱氢酶", "α-酮戊二酸脱氢酶复合体"], [("糖酵解的关键酶", "ABC"), ("丙酮酸脱羧的关键酶", "D"), ("三羧酸循环的关键酶", "EFG")], 3, 4),
        group(4, "糖代谢途径的意义", glycolysis, ["缺氧供能", "向肌肉迅速供能", "成熟红细胞获得能量的唯一途径", "瓦伯格效应：恶性肿瘤即使氧供正常也主要进行无氧氧化", "三大营养物质最终代谢去路、联系枢纽", "为氧化磷酸化提供还原当量"], [("无氧氧化的意义", "ABCD"), ("三羧酸循环的意义", "EF")], 1, 6),
        group(5, "高能化合物", glycolysis, ["乙酰 CoA", "脂酰 CoA", "丙二酰 CoA/丙二酸单酰 CoA", "HMG CoA", "NDP、NTP", "1,3-二磷酸甘油酸、PEP", "磷酸肌酸", "氨基甲酰磷酸", "焦磷酸（如 PRPP）", "葡萄糖-1-磷酸", "2,3-二磷酸甘油酸", "果糖-1,6-二磷酸", "三磷酸肌醇"], [("高能硫酯键", "ABCD"), ("高能磷酸键", "EFGHI")], 1, 7, CORRECTION_HIGH_ENERGY),
        group(10, "氧化还原当量与穿梭", glycolysis, ["NADPH", "FADH2", "NADH+H+"], [("琥珀酸在三羧酸循环中氧化脱掉的是", "B"), ("磷酸戊糖途径脱掉的是", "A"), ("谷氨酸脱氢酶脱掉的是", "C"), ("α-磷酸甘油-磷酸二羟丙酮穿梭中，线粒体中 α-磷酸甘油脱掉的是", "B")], 2, 1, CORRECTION_NADH),
        group(11, "糖代谢途径定义", glycolysis, ["葡萄糖转化为 5-磷酸核糖", "葡萄糖转化为丙酮酸", "葡萄糖转化为二氧化碳", "葡萄糖转化为乳酸"], [("糖酵解途径是指", "B"), ("葡萄糖无氧氧化指", "D"), ("葡萄糖有氧氧化指", "C"), ("葡萄糖磷酸戊糖途径指", "A")], 1, 3),
        group(12, "底物水平磷酸化", glycolysis, ["己糖激酶", "磷酸甘油酸激酶", "丙酮酸脱氢酶", "丙酮酸激酶", "柠檬酸合酶", "琥珀酰 CoA 合成酶"], [("催化底物水平磷酸化的酶", "BDF")], 2, 1),
        group(13, "高能硫酯键的生理角色", glycolysis, ["乙酰 CoA", "脂酰 CoA", "丙二酰 CoA/丙二酸单酰 CoA", "HMG CoA"], [("脂肪酸合成的重要物质", "C"), ("胆固醇、酮体合成的重要物质", "D"), ("三大营养物质最终代谢去路", "A"), ("脂肪酸的活化形式", "B")], 1, 7),
        group(6, "糖异生关键酶", gluconeogenesis, ["己糖激酶", "果糖双磷酸酶-1", "磷酸烯醇式丙酮酸羧激酶", "丙酮酸激酶", "葡糖-6-磷酸酶", "磷酸果糖激酶-1", "丙酮酸羧化酶"], [("糖异生的关键酶", "BCEG"), ("催化 G-6-P→G 的酶", "E"), ("催化草酰乙酸→PEP 的酶", "C"), ("消耗能量的酶", "ACFG")], 3, 3),
        group(7, "糖代谢途径的细胞定位", gluconeogenesis, ["糖酵解", "糖异生", "磷酸戊糖途径", "三羧酸循环", "无氧氧化"], [("在胞浆中进行的代谢途径", "ACE"), ("在线粒体中进行的代谢途径", "BD"), ("成熟红细胞可进行的代谢途径", "ACE")], 3, 1),
        group(8, "糖代谢酶活性调节", gluconeogenesis, ["果糖-1,6-二磷酸", "AMP、ADP", "乙酰 CoA", "果糖-2,6-二磷酸", "葡萄糖"], [("丙酮酸羧化酶的激活剂", "C"), ("果糖双磷酸酶-1 的抑制剂", "AD")], 3, 3),
        group(9, "糖异生与酮体", gluconeogenesis, ["胆固醇", "甘油", "亮氨酸、赖氨酸", "软脂酸", "乙酰 CoA", "乳酸"], [("可以进行糖异生的物质", "BF"), ("可以生成酮体的物质", "CDE")], 3, 3, CORRECTION_KETONE),
        group(14, "胰高血糖素对糖代谢的调节", gluconeogenesis, ["果糖双磷酸酶-2", "丙酮酸激酶", "磷酸果糖激酶-2", "磷酸烯醇式丙酮酸羧激酶"], [("胰高血糖素激活的酶有", "AD"), ("胰高血糖素抑制的酶有", "BC")], 3, 3),
        group(15, "NADPH 的作用", gluconeogenesis, ["合成胆红素", "糖异生", "合成氨基酸", "糖原分解", "胆固醇的分解"], [("NADPH 可参与的反应", "ACE")], 3, 1),
    ]
    pages = [{"page": g["page"], "image": "", "topic": g["topic"], "searchText": g["title"]} for g in groups]
    payload = {"meta": {"title": "生物化学题库", "sourceLabel": "生化第一章学成选择题（修订扩充版）", "sourcePages": 1, "lectureCount": 3, "groupCount": len(groups), "stemCount": sum(len(g["stems"]) for g in groups), "correctionGroupCount": 3, "generatedBy": "scripts/build_biochemistry_chapter1.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "第一章题组按糖酵解/糖有氧氧化与磷酸戊糖途径/糖异生两个知识簇重排；答案已按 2027 讲义逐项复核。"}, "topics": ["全部", "糖酵解与糖有氧氧化", "磷酸戊糖途径、糖异生与调控", "综合"], "pages": pages, "groups": groups, "lectures": [{"id": f"lecture-{n:02d}", "number": n, "title": title, "pageCount": {1: 10, 2: 8, 3: 6}[n]} for n, title in LECTURES]}
    out = Path("src/data/biochemistry-data.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}: {len(groups)} groups, {payload['meta']['stemCount']} stems")


if __name__ == "__main__":
    main()
