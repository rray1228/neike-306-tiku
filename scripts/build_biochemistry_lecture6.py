#!/usr/bin/env python3
"""Build the checked biochemistry lecture 06 (lipid metabolism) payload.

Question content comes from the supplied workbook. Answers are checked against
the 2027 lecture 06 handout, and each shared option bank is deterministically
shuffled before export.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


TITLE = "生化 脂肪代谢"
TOPIC = "脂代谢"


def group(index, title, options, stems, lecture_page):
    shuffled = list(options)
    random.Random(30606 + index).shuffle(shuffled)
    option_keys = {label: chr(65 + position) for position, label in enumerate(shuffled)}
    formatted_stems = []
    for number, (text, answer_labels) in enumerate(stems, 1):
        answer = [option_keys[label] for label in answer_labels]
        formatted_stems.append({
            "number": number,
            "text": text.replace("（多选）", "").rstrip(),
            "answerRaw": "、".join(answer),
            "answer": answer,
            "answerMode": "多选" if len(answer) > 1 else "单选",
        })
    return {
        "id": f"bio-06-{index:02d}",
        "page": index,
        "title": title,
        "kind": "B",
        "kindLabel": "B型题",
        "options": [{"key": chr(65 + position), "label": label} for position, label in enumerate(shuffled)],
        "stems": formatted_stems,
        "sourceText": title,
        "reviewState": "已按 2027 考研讲义核对",
        "reviewIssues": [],
        "reviewNotes": [],
        "topic": TOPIC,
        "lectureIds": ["lecture-06"],
        "lectureEvidence": {
            "lectureId": "lecture-06",
            "lectureNumber": 6,
            "lectureTitle": TITLE,
            "page": lecture_page,
            "image": f"biochemistry/lecture-pages/lecture-06-page-{lecture_page:02d}.webp",
            "title": f"第 06 讲《{TITLE}》· 第 {lecture_page} 页",
            "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
            "method": "按知识点人工映射至 2027 考研生化第 06 讲，并逐项复核。",
        },
    }


def main():
    groups = [
        group(1, "脂肪合成途径与甘油来源", [
            "葡萄糖", "肝", "脂肪动员", "需乳糜微粒（CM）", "甘油", "甘油激酶",
            "脂肪细胞等胞浆", "小肠胞浆", "甘油激酶在脂肪和骨骼肌细胞活性很低或缺乏",
            "3-磷酸甘油", "磷酸二羟丙酮", "合成脂肪的甘油只能来自糖酵解的 3-磷酸甘油",
            "既可来自糖酵解的 3-磷酸甘油，也可来自脂肪动员的甘油",
        ], [
            ("甘油一酯途径的特点", ["需乳糜微粒（CM）", "小肠胞浆"]),
            ("甘油二酯途径的部位", ["脂肪细胞等胞浆", "肝"]),
            ("葡萄糖来源的 3-磷酸甘油相关物", ["葡萄糖", "磷酸二羟丙酮", "3-磷酸甘油"]),
            ("脂肪动员来源的 3-磷酸甘油相关物", ["脂肪动员", "甘油", "甘油激酶", "3-磷酸甘油"]),
            ("脂肪和骨骼肌细胞合成脂肪的甘油来源", ["甘油激酶在脂肪和骨骼肌细胞活性很低或缺乏", "合成脂肪的甘油只能来自糖酵解的 3-磷酸甘油"]),
            ("肝脏合成脂肪的甘油来源", ["既可来自糖酵解的 3-磷酸甘油，也可来自脂肪动员的甘油"]),
        ], 1),
        group(2, "乙酰 CoA 羧化酶与脂肪酸合成原料", [
            "柠檬酸", "柠檬酸-丙酮酸循环", "生物素（VitB7）", "糖", "异柠檬酸",
            "胰高血糖素（磷酸化）", "ATP", "氨基酸", "长链脂酰 CoA", "丙二酰 CoA",
            "乙酰 CoA→丙二酰 CoA（丙二酸单酰 CoA）", "乙酰 CoA", "磷酸戊糖途径",
        ], [
            ("乙酰 CoA 羧化酶催化", ["乙酰 CoA→丙二酰 CoA（丙二酸单酰 CoA）"]),
            ("乙酰 CoA 羧化酶的辅因子", ["生物素（VitB7）"]),
            ("乙酰 CoA 羧化酶的激活剂", ["柠檬酸", "异柠檬酸", "乙酰 CoA", "丙二酰 CoA"]),
            ("乙酰 CoA 羧化酶的抑制剂", ["胰高血糖素（磷酸化）", "长链脂酰 CoA"]),
            ("脂肪酸合成的乙酰 CoA 来源", ["糖", "氨基酸"]),
            ("脂肪酸合成的 NADPH 来源", ["柠檬酸-丙酮酸循环", "磷酸戊糖途径"]),
            ("脂肪酸合成还需要", ["ATP"]),
        ], 1),
        group(3, "脂酰基的载体", [
            "辅酶 A/HSCoA", "维生素 B5", "线粒体", "胞浆", "内质网", "酰基载体蛋白/ACP",
        ], [
            ("合成脂肪酸所需的脂酰基载体及部位", ["维生素 B5", "胞浆", "酰基载体蛋白/ACP"]),
            ("脂肪酸合成后延长碳链所需的脂酰基载体及部位", ["辅酶 A/HSCoA", "维生素 B5", "线粒体", "内质网"]),
        ], 1),
        group(4, "脂肪动员的酶与调节", [
            "激素敏感性甘油三酯酯酶（HSL）", "甘油三酯→甘油二酯+脂肪酸", "抗脂解激素", "ATGL",
            "甘油二酯→甘油一酯+脂肪酸", "胰岛素", "儿茶酚胺", "甘油一酯脂肪酶",
            "前列腺素", "胰高血糖素", "脂解激素", "甘油一酯→甘油+脂肪酸",
        ], [
            ("ATGL 催化", ["甘油三酯→甘油二酯+脂肪酸"]),
            ("HSL 催化", ["甘油二酯→甘油一酯+脂肪酸"]),
            ("HSL 的激活剂", ["儿茶酚胺", "胰高血糖素", "脂解激素"]),
            ("HSL 的抑制剂", ["抗脂解激素", "胰岛素", "前列腺素"]),
            ("甘油一酯脂肪酶催化", ["甘油一酯→甘油+脂肪酸"]),
        ], 2),
        group(5, "甘油的利用", [
            "合成脂肪", "氧化分解供能", "糖异生", "消耗 2 个 ATP", "生成 18.5/16.5 个 ATP", "肝脏", "脂肪和骨骼肌细胞",
        ], [
            ("甘油可用于（多选）", ["合成脂肪", "氧化分解供能", "糖异生"]),
            ("2 分子甘油糖异生净消耗", ["消耗 2 个 ATP"]),
            ("1 分子甘油完全氧化可生成", ["生成 18.5/16.5 个 ATP"]),
            ("甘油激酶活性最高的组织", ["肝脏"]),
            ("甘油激酶活性很低或缺乏的组织", ["脂肪和骨骼肌细胞"]),
        ], 2),
        group(6, "脂肪酸 β 氧化：活化、转运与组织特点", [
            "脑不能进行脂肪酸 β 氧化", "肝主要通过氧化脂肪酸获得能量", "肉碱-脂酰肉碱转位酶", "肉碱",
            "肝的脂肪酸 β 氧化非常活跃", "肉碱脂酰转移酶Ⅰ", "成人心肌也主要消耗脂肪酸",
            "肉碱脂酰转移酶Ⅱ", "其他器官主要通过氧化葡萄糖获得能量", "脂酰 CoA 合成酶",
            "肝将多余葡萄糖变为糖原、脂肪储存", "丙二酰 CoA", "脂酰 CoA",
        ], [
            ("脂肪酸活化所需酶和产物", ["脂酰 CoA 合成酶", "脂酰 CoA"]),
            ("脂酰 CoA 进入线粒体需要", ["肉碱-脂酰肉碱转位酶", "肉碱脂酰转移酶Ⅰ", "肉碱脂酰转移酶Ⅱ"]),
            ("脂肪酸 β 氧化的关键酶", ["肉碱脂酰转移酶Ⅰ"]),
            ("抑制肉碱脂酰转移酶Ⅰ", ["丙二酰 CoA"]),
            ("促进脂肪酸 β 氧化", ["肉碱"]),
            ("肝的脂肪酸 β 氧化相关特点", ["肝主要通过氧化脂肪酸获得能量", "肝的脂肪酸 β 氧化非常活跃", "肝将多余葡萄糖变为糖原、脂肪储存"]),
            ("脑的脂肪酸 β 氧化特点", ["脑不能进行脂肪酸 β 氧化"]),
            ("成人心肌的主要供能特点", ["成人心肌也主要消耗脂肪酸"]),
            ("其他器官的主要供能特点", ["其他器官主要通过氧化葡萄糖获得能量"]),
        ], 3),
        group(7, "脂肪酸 β 氧化的四步反应", [
            "β-酮脂酰 CoA 硫解酶", "FADH₂", "硫解", "NADH", "脂酰 CoA 脱氢酶", "加水",
        ], [
            ("脂肪酸 β 氧化第一次脱氢相关物", ["FADH₂", "脂酰 CoA 脱氢酶"]),
            ("脂肪酸 β 氧化第二步反应", ["加水"]),
            ("脂肪酸 β 氧化第二次脱氢产物", ["NADH"]),
            ("脂肪酸 β 氧化第四步反应及酶", ["β-酮脂酰 CoA 硫解酶", "硫解"]),
        ], 3),
        group(8, "偶数碳与奇数碳脂肪酸", [
            "三羧酸循环", "生物氧化", "丙酰 CoA", "糖异生", "乙酰 CoA", "琥珀酰 CoA",
        ], [
            ("偶数碳脂肪酸 β 氧化的去路", ["三羧酸循环", "生物氧化", "乙酰 CoA"]),
            ("奇数碳脂肪酸 β 氧化的去路", ["三羧酸循环", "生物氧化", "丙酰 CoA", "糖异生", "乙酰 CoA", "琥珀酰 CoA"]),
        ], 3),
        group(9, "酮体的合成、分解与意义", [
            "易透过血脑屏障", "β-羟丁酸", "糖尿病", "HMG CoA 裂解酶", "肝线粒体", "HMG CoA 合酶",
            "肝外线粒体", "乙酰乙酰 CoA 硫解酶", "乙酰 CoA", "琥珀酰 CoA 转硫酶", "饥饿",
            "乙酰乙酸硫激酶", "乙酰乙酸", "肝输出能源的一种形式", "丙酮", "脑组织的主要能量来源",
        ], [
            ("酮体包括", ["β-羟丁酸", "乙酰乙酸", "丙酮"]),
            ("酮体合成部位", ["肝线粒体"]),
            ("酮体合成原料", ["乙酰 CoA"]),
            ("参与酮体合成的酶", ["HMG CoA 裂解酶", "HMG CoA 合酶", "乙酰乙酰 CoA 硫解酶"]),
            ("参与酮体分解的酶", ["乙酰乙酰 CoA 硫解酶", "琥珀酰 CoA 转硫酶", "乙酰乙酸硫激酶"]),
            ("酮体分解部位", ["肝外线粒体"]),
            ("酮体的生理意义", ["肝输出能源的一种形式"]),
            ("酮体产生增多的情况", ["糖尿病", "饥饿"]),
            ("饥饿时，酮体成为", ["脑组织的主要能量来源"]),
            ("酮体的特点", ["易透过血脑屏障"]),
        ], 5),
        group(10, "必需脂肪酸", [
            "血栓素 TXA₂", "不能在体内合成", "亚麻酸", "只能从食物获取", "主要存在于植物油脂",
            "花生四烯酸", "前列腺素 PG", "白三烯 LT", "亚油酸",
        ], [
            ("必需脂肪酸的特点", ["不能在体内合成", "只能从食物获取", "主要存在于植物油脂"]),
            ("必需脂肪酸包括", ["亚麻酸", "花生四烯酸", "亚油酸"]),
            ("花生四烯酸的衍生物", ["血栓素 TXA₂", "前列腺素 PG", "白三烯 LT"]),
        ], 5),
    ]
    payload = {
        "meta": {
            "title": "生物化学第 06 讲题库",
            "sourceLabel": "生化第 06 讲学成选择题（脂肪代谢）",
            "sourcePages": 1,
            "lectureCount": 1,
            "groupCount": len(groups),
            "stemCount": sum(len(item["stems"]) for item in groups),
            "correctionGroupCount": 0,
            "generatedBy": "scripts/build_biochemistry_lecture6.py",
            "siteIntegrated": True,
            "lectureLinked": True,
            "answerNote": "仅收录第 06 讲《脂肪代谢》范围内题目；选项已逐组打散，答案已按讲义复核。",
        },
        "topics": ["全部", TOPIC, "综合"],
        "pages": [{"page": item["page"], "image": "", "topic": TOPIC, "searchText": item["title"]} for item in groups],
        "groups": groups,
        "lectures": [{"id": "lecture-06", "number": 6, "title": TITLE, "pageCount": 10}],
    }
    Path("src/data/biochemistry-lecture6-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
