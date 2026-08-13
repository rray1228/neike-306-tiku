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
            "image": f"biochemistry/lecture-pages/lecture-{lecture:02d}-page-{page:02d}.webp",
            "title": f"第 {lecture} 讲《{LECTURES[lecture - 1][1]}》· 第 {page} 页",
            "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
            "method": "按知识点人工映射至 2027 考研生化讲义，并逐项复核。",
        },
    }


LECTURES = [(1, "生化 糖无氧氧化、糖有氧氧化、红细胞代谢、高能化合物")]


def main():
    carbohydrate = "糖无氧氧化与糖有氧氧化"
    energy = "红细胞代谢与高能化合物"
    groups = [
        group(1, "糖酵解关键酶", carbohydrate, ["长链脂酰 CoA", "PEP→丙酮酸、ATP", "AMP", "G→G-6-P", "ATP", "果糖-2,6-二磷酸（最强激活剂）", "丙氨酸", "F-6-P→F-1,6-DP", "葡萄糖", "G-6-P", "ADP", "柠檬酸", "果糖-1,6-二磷酸"], [("丙酮酸激酶催化：", "B"), ("丙酮酸激酶激活剂：", "M"), ("丙酮酸激酶抑制剂：", "EG"), ("己糖激酶催化：", "D"), ("己糖激酶激活剂：", "I"), ("己糖激酶抑制剂：", "AJ"), ("磷酸果糖激酶-1催化：", "H"), ("磷酸果糖激酶-1激活剂：", "CFK"), ("磷酸果糖激酶-1抑制剂：", "EL")], 1, 4),
        group(2, "关键酶与非关键酶", carbohydrate, ["3-磷酸甘油醛脱氢酶", "异柠檬酸脱氢酶", "己糖激酶", "琥珀酰 CoA 合成酶", "丙酮酸激酶", "磷酸甘油酸激酶", "α-酮戊二酸脱氢酶复合体", "琥珀酸脱氢酶", "丙酮酸脱氢酶复合体", "磷酸果糖激酶-1", "乳酸脱氢酶 LDH", "柠檬酸合酶"], [("关键酶", "BCEGIJL"), ("非关键酶", "ADFHK")], 1, 5),
        group(3, "糖有氧氧化的关键酶", carbohydrate, ["异柠檬酸脱氢酶", "磷酸果糖激酶-1", "α-酮戊二酸脱氢酶复合体", "丙酮酸脱氢酶复合体", "己糖激酶", "柠檬酸合酶", "丙酮酸激酶"], [("糖酵解的关键酶", "BEG"), ("丙酮酸脱羧的关键酶", "D"), ("三羧酸循环的关键酶", "ACF")], 1, 4),
        group(4, "糖代谢途径的意义", carbohydrate, ["三大营养物质最终代谢去路、联系枢纽", "缺氧供能", "为氧化磷酸化提供还原当量", "成熟红细胞获得能量的唯一途径", "向肌肉迅速供能", "瓦伯格效应：恶性肿瘤即使氧供正常也主要进行无氧氧化"], [("无氧氧化的意义", "BDEF"), ("三羧酸循环的意义", "AC")], 1, 6),
        group(11, "糖代谢途径定义", carbohydrate, ["葡萄糖转化为二氧化碳", "葡萄糖转化为 5-磷酸核糖", "葡萄糖转化为乳酸", "葡萄糖转化为丙酮酸"], [("糖酵解途径是指", "D"), ("葡萄糖无氧氧化指", "C"), ("葡萄糖有氧氧化指", "A"), ("葡萄糖磷酸戊糖途径指", "B")], 1, 3),
        group(5, "高能化合物", energy, ["果糖-1,6-二磷酸", "HMG CoA", "氨基甲酰磷酸", "乙酰 CoA", "葡萄糖-1-磷酸", "磷酸肌酸", "三磷酸肌醇", "丙二酰 CoA/丙二酸单酰 CoA", "1,3-二磷酸甘油酸、PEP", "焦磷酸（如 PRPP）", "脂酰 CoA", "NDP、NTP", "2,3-二磷酸甘油酸"], [("高能硫酯键", "BDHK"), ("高能磷酸键", "CEFIJL")], 1, 7),
        group(12, "底物水平磷酸化", energy, ["柠檬酸合酶", "磷酸甘油酸激酶", "丙酮酸激酶", "己糖激酶", "琥珀酰 CoA 合成酶", "丙酮酸脱氢酶"], [("催化底物水平磷酸化的酶", "BCE")], 1, 5),
        group(13, "高能硫酯键的生理角色", energy, ["HMG CoA", "脂酰 CoA", "乙酰 CoA", "丙二酰 CoA/丙二酸单酰 CoA"], [("脂肪酸合成的重要物质", "D"), ("胆固醇、酮体合成的重要物质", "A"), ("三大营养物质最终代谢去路", "C"), ("脂肪酸的活化形式", "B")], 1, 7),
    ]
    pages = [{"page": g["page"], "image": "", "topic": g["topic"], "searchText": g["title"]} for g in groups]
    payload = {"meta": {"title": "生物化学第 1 讲题库", "sourceLabel": "生化第 1 讲学成选择题（修订扩充版）", "sourcePages": 1, "lectureCount": 1, "groupCount": len(groups), "stemCount": sum(len(g["stems"]) for g in groups), "correctionGroupCount": 0, "generatedBy": "scripts/build_biochemistry_chapter1.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "仅收录第 01 讲《糖无氧氧化、糖有氧氧化、红细胞代谢、高能化合物》范围内题目；每题组均已关联对应讲义页。"}, "topics": ["全部", carbohydrate, energy, "综合"], "pages": pages, "groups": groups, "lectures": [{"id": "lecture-01", "number": 1, "title": LECTURES[0][1], "pageCount": 10}]}
    out = Path("src/data/biochemistry-data.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}: {len(groups)} groups, {payload['meta']['stemCount']} stems")


if __name__ == "__main__":
    main()
