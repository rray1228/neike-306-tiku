#!/usr/bin/env python3
"""Build the checked biochemistry lecture 05 payload (phospholipid, cholesterol and bile acids)."""

from __future__ import annotations

import json
import random
from pathlib import Path


TITLE = "生化 磷脂代谢、胆固醇代谢和胆汁酸"
TOPIC = "脂代谢"


def evidence(page):
    return {"lectureId": "lecture-05", "lectureNumber": 5, "lectureTitle": TITLE, "page": page, "image": f"biochemistry/lecture-pages/lecture-05-page-{page:02d}.webp", "title": f"第 05 讲《{TITLE}》· 第 {page} 页", "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。", "method": "按知识点人工映射至 2027 考研生化第 05 讲，并逐项复核。"}


def bank(index, title, options, stems, lecture_page):
    shuffled = list(options)
    random.Random(30605 + index).shuffle(shuffled)
    if shuffled == options:
        shuffled = shuffled[1:] + shuffled[:1]
    keys = {label: chr(65 + position) for position, label in enumerate(shuffled)}
    return {"id": f"bio-05-{index:02d}", "page": index, "title": title, "kind": "B", "kindLabel": "B型题", "options": [{"key": chr(65 + position), "label": label} for position, label in enumerate(shuffled)], "stems": [{"number": number, "text": text, "answerRaw": "、".join(keys[item] for item in answer), "answer": [keys[item] for item in answer], "answerMode": "多选" if len(answer) > 1 else "单选"} for number, (text, answer) in enumerate(stems, 1)], "sourceText": title, "reviewState": "已按 2027 考研讲义核对", "reviewIssues": [], "reviewNotes": [], "topic": TOPIC, "lectureIds": ["lecture-05"], "optionShuffleVersion": 1, "lectureEvidence": evidence(lecture_page)}


def main():
    groups = [
        bank(1, "胆固醇酯化：LCAT 与 ACAT", ["在肝合成", "脂酰 CoA 提供脂酰基", "催化胆固醇第 3 位羟基酯化", "催化血浆中胆固醇酯化", "催化细胞内胆固醇酯化", "卵磷脂提供脂酰基", "由相应组织细胞合成"], [("LCAT 的特点", ["在肝合成", "催化胆固醇第 3 位羟基酯化", "催化血浆中胆固醇酯化", "卵磷脂提供脂酰基"]), ("ACAT 的特点", ["脂酰 CoA 提供脂酰基", "催化胆固醇第 3 位羟基酯化", "催化细胞内胆固醇酯化", "由相应组织细胞合成"])], 1),
        bank(2, "甘油磷脂的极性头基", ["丝氨酸", "胆碱", "氢", "磷脂酰甘油", "乙醇胺", "肌醇"], [("磷脂酸的 X 基团", ["氢"]), ("卵磷脂的 X 基团", ["胆碱"]), ("脑磷脂的 X 基团", ["乙醇胺"]), ("磷脂酰丝氨酸的 X 基团", ["丝氨酸"]), ("心磷脂的 X 基团", ["磷脂酰甘油"]), ("磷脂酰肌醇的 X 基团", ["肌醇"])], 2),
        bank(3, "甘油磷脂合成的活化中间物", ["CDP-乙醇胺", "磷脂酰丝氨酸", "脑磷脂", "甘油二酯", "磷脂酰肌醇", "CDP-胆碱", "脂酰 CoA", "肌醇", "CDP-甘油二酯", "卵磷脂", "心磷脂", "丝氨酸", "甘油三酯"], [("甘油二酯途径可合成", ["脑磷脂", "卵磷脂", "甘油三酯"]), ("CDP-甘油二酯途径可合成", ["磷脂酰丝氨酸", "磷脂酰肌醇", "心磷脂"]), ("脑磷脂活化的中间物", ["CDP-乙醇胺"]), ("卵磷脂活化的中间物", ["CDP-胆碱"]), ("甘油三酯合成的脂酰基供体", ["脂酰 CoA"]), ("合成磷脂酰肌醇还需要", ["肌醇"]), ("合成磷脂酰丝氨酸还需要", ["丝氨酸"]), ("磷脂酸合成的关键中间物", ["甘油二酯", "CDP-甘油二酯"])], 2),
        bank(4, "磷脂合成中的甲基化反应", ["脑磷脂", "磷脂酰丝氨酸", "卵磷脂", "鞘磷脂", "S-腺苷甲硫氨酸循环"], [("合成时与甲基化反应有关的磷脂", ["卵磷脂", "鞘磷脂"]), ("甲基供体相关循环", ["S-腺苷甲硫氨酸循环"])], 2),
        bank(5, "磷脂酶的水解产物", ["2-溶血磷脂", "1-溶血磷脂", "1,2-甘油二酯", "磷脂酸"], [("磷脂酶 A₁ 的水解产物", ["2-溶血磷脂"]), ("磷脂酶 A₂ 的水解产物", ["1-溶血磷脂"]), ("磷脂酶 C 的水解产物", ["1,2-甘油二酯"]), ("磷脂酶 D 的水解产物", ["磷脂酸"])], 2),
        bank(6, "胆固醇合成的原料与细胞定位", ["葡萄糖", "胞浆", "磷酸戊糖途径", "NADPH", "小肠", "滑面内质网", "氨基酸", "脂肪酸", "乙酰 CoA", "ATP", "肝", "将乙酰 CoA 从线粒体转运至胞浆", "柠檬酸-丙酮酸循环"], [("胆固醇合成的主要部位", ["胞浆", "小肠", "滑面内质网", "肝"]), ("胆固醇合成的直接原料", ["NADPH", "乙酰 CoA", "ATP"]), ("合成胆固醇的乙酰 CoA 来源", ["葡萄糖", "氨基酸", "脂肪酸"]), ("合成胆固醇的 NADPH 来源", ["磷酸戊糖途径", "柠檬酸-丙酮酸循环"]), ("柠檬酸-丙酮酸循环的作用", ["将乙酰 CoA 从线粒体转运至胞浆"])], 1),
        bank(7, "胆固醇与胆汁酸合成的限速酶调节", ["生长激素", "胆汁酸", "胰高血糖素", "甲状腺激素", "胆固醇 7α-羟化酶", "HMG-CoA 还原酶", "胆固醇", "糖皮质激素", "进食状态", "胰岛素使其去磷酸化", "午夜", "饥饿", "中午", "他汀类药物", "高糖", "高脂"], [("胆固醇合成的关键酶", ["HMG-CoA 还原酶"]), ("HMG-CoA 还原酶的激活因素", ["甲状腺激素", "胰岛素使其去磷酸化"]), ("HMG-CoA 还原酶的抑制因素", ["胆汁酸", "胰高血糖素", "胆固醇", "糖皮质激素", "他汀类药物"]), ("HMG-CoA 还原酶活性较高时", ["进食状态", "午夜", "高糖", "高脂"]), ("HMG-CoA 还原酶活性较低时", ["饥饿", "中午"]), ("胆汁酸合成的关键酶", ["胆固醇 7α-羟化酶"]), ("胆固醇 7α-羟化酶的激活因素", ["生长激素", "甲状腺激素", "胆固醇", "糖皮质激素"]), ("胆固醇 7α-羟化酶的抑制因素", ["胆汁酸"])], 1),
        bank(8, "胆固醇的去路与维生素 D₃ 活化", ["胆色素", "骨化三醇", "血红素", "CO₂ 和 H₂O", "性激素", "维生素 D₃", "紫外线", "7-脱氢胆固醇", "25-羟维生素 D₃", "1,25-二羟维生素 D₃", "醛固酮", "活性维生素 D₃", "胆汁酸", "糖皮质激素"], [("胆固醇最主要的去路", ["胆汁酸"]), ("皮肤中合成维生素 D₃ 所需", ["维生素 D₃", "紫外线", "7-脱氢胆固醇"]), ("维生素 D₃ 在肝内的产物", ["25-羟维生素 D₃"]), ("维生素 D₃ 在肾内的活性产物", ["骨化三醇", "1,25-二羟维生素 D₃", "活性维生素 D₃"]), ("由胆固醇衍生的类固醇激素", ["性激素", "1,25-二羟维生素 D₃", "醛固酮", "糖皮质激素"]), ("胆固醇不能彻底氧化为", ["CO₂ 和 H₂O"]), ("胆固醇不能转变为", ["胆色素"]), ("胆色素的前体", ["血红素"])], 2),
        bank(9, "胆汁酸、肠肝循环与胆石症", ["胆酸", "胆汁酸在肠道丢失过多", "脱氧胆酸", "肠肝循环减少", "肠肝循环", "胆汁中胆固醇过多", "石胆酸", "甘氨酸", "牛磺酸", "回肠", "肝合成胆汁酸不足", "鹅脱氧胆酸"], [("初级胆汁酸", ["胆酸", "鹅脱氧胆酸"]), ("次级胆汁酸", ["脱氧胆酸", "石胆酸"]), ("结合胆汁酸可与下列氨基酸结合", ["甘氨酸", "牛磺酸"]), ("胆汁酸重吸收的主要部位", ["回肠"]), ("胆汁酸回收过程", ["肠肝循环"]), ("胆固醇性胆石症的相关因素", ["胆汁酸在肠道丢失过多", "肠肝循环减少", "胆汁中胆固醇过多", "肝合成胆汁酸不足"])], 2),
    ]
    payload = {"meta": {"title": "生物化学第 05 讲题库", "sourceLabel": "生化第 05 讲学成选择题（磷脂、胆固醇、胆汁酸）", "sourcePages": 1, "lectureCount": 1, "groupCount": len(groups), "stemCount": sum(len(item["stems"]) for item in groups), "correctionGroupCount": 0, "generatedBy": "scripts/build_biochemistry_lecture5.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "仅收录第 05 讲《磷脂代谢、胆固醇代谢和胆汁酸》范围内题目；选项已逐组打散，答案已按讲义复核。"}, "topics": ["全部", TOPIC, "综合"], "pages": [{"page": item["page"], "image": "", "topic": TOPIC, "searchText": item["title"]} for item in groups], "groups": groups, "lectures": [{"id": "lecture-05", "number": 5, "title": TITLE, "pageCount": 5}]}
    Path("src/data/biochemistry-lecture5-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
