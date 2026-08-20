#!/usr/bin/env python3
"""Build the verified bilirubin-metabolism and biotransformation banks."""

from __future__ import annotations

import json
import random
from pathlib import Path


TOPIC = "胆色素代谢与生物转化"


def evidence(lecture_number, title, page):
    return {
        "lectureId": f"lecture-{lecture_number:02d}",
        "lectureNumber": lecture_number,
        "lectureTitle": title,
        "page": page,
        "image": f"biochemistry/lecture-pages/lecture-{lecture_number:02d}-page-{page:02d}.webp",
        "title": f"第 {lecture_number:02d} 讲《{title}》· 第 {page} 页",
        "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
        "method": f"按 2027 考研生化第 {lecture_number:02d} 讲及思维导图逐项复核。",
    }


def bank(lecture_number, lecture_title, index, title, options, stems, lecture_page):
    shuffled = list(options)
    random.Random(30600 + lecture_number * 100 + index).shuffle(shuffled)
    if shuffled == options:
        shuffled = shuffled[1:] + shuffled[:1]
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
        "id": f"bio-{lecture_number:02d}-{index:02d}",
        "page": index,
        "title": title,
        "kind": "B",
        "kindLabel": "B型题",
        "options": [{"key": chr(65 + position), "label": label} for position, label in enumerate(shuffled)],
        "stems": formatted_stems,
        "sourceText": title,
        "reviewState": "已按 2027 考研讲义与思维导图核对",
        "reviewIssues": [],
        "reviewNotes": [],
        "topic": TOPIC,
        "lectureIds": [f"lecture-{lecture_number:02d}"],
        "optionShuffleVersion": 1,
        "lectureEvidence": evidence(lecture_number, lecture_title, lecture_page),
    }


def categorized_bank(lecture_number, lecture_title, index, title, categories, stems, lecture_page):
    """Build a bank whose options stay grouped by indicator while shuffling within each group."""
    shuffled_options = []
    for category_index, (category, labels) in enumerate(categories):
        shuffled = list(labels)
        random.Random(30600 + lecture_number * 100 + index * 10 + category_index).shuffle(shuffled)
        if shuffled == labels and len(shuffled) > 1:
            shuffled = shuffled[1:] + shuffled[:1]
        shuffled_options.extend((category, label) for label in shuffled)

    option_keys = {label: chr(65 + position) for position, (_, label) in enumerate(shuffled_options)}
    formatted_stems = []
    for number, (text, answer_labels) in enumerate(stems, 1):
        answer = [option_keys[label] for label in answer_labels]
        formatted_stems.append({
            "number": number,
            "text": text,
            "answerRaw": "、".join(answer),
            "answer": answer,
            "answerMode": "多选",
        })
    return {
        "id": f"bio-{lecture_number:02d}-{index:02d}",
        "page": index,
        "title": title,
        "kind": "B",
        "kindLabel": "B型题",
        "options": [
            {"key": chr(65 + position), "label": label, "category": category}
            for position, (category, label) in enumerate(shuffled_options)
        ],
        "stems": formatted_stems,
        "sourceText": title,
        "reviewState": "已按三种黄疸鉴别表逐项核对",
        "reviewIssues": [],
        "reviewNotes": ["题干固定为三种黄疸；每项指标作为独立选项，并按指标类别分区。"],
        "topic": TOPIC,
        "lectureIds": [f"lecture-{lecture_number:02d}"],
        "optionShuffleVersion": 2,
        "lectureEvidence": evidence(lecture_number, lecture_title, lecture_page),
    }


def payload(lecture_number, title, source_label, page_count, groups):
    return {
        "meta": {
            "title": f"生物化学第 {lecture_number:02d} 讲题库",
            "sourceLabel": source_label,
            "sourcePages": 1,
            "lectureCount": 1,
            "groupCount": len(groups),
            "stemCount": sum(len(group["stems"]) for group in groups),
            "correctionGroupCount": 0,
            "generatedBy": "scripts/build_biochemistry_lecture10_11.py",
            "siteIntegrated": True,
            "lectureLinked": True,
            "answerNote": f"仅收录第 {lecture_number:02d} 讲《{title}》范围内题目；选项已逐组打散，答案按讲义与思维导图复核。",
        },
        "topics": ["全部", TOPIC, "综合"],
        "pages": [{"page": group["page"], "image": "", "topic": TOPIC, "searchText": group["title"]} for group in groups],
        "groups": groups,
        "lectures": [{"id": f"lecture-{lecture_number:02d}", "number": lecture_number, "title": title, "pageCount": page_count}],
    }


def main():
    bilirubin_title = "生化 胆色素代谢"
    bilirubin_groups = [
        bank(10, bilirubin_title, 1, "血红素的合成", [
            "血红素加氧酶", "琥珀酰 CoA", "亚铁螯合酶", "磷酸吡哆醛", "甘氨酸", "ALA 脱水酶", "Fe²⁺", "ALA 合酶", "胞质", "粪卟啉原氧化酶", "线粒体", "成熟红细胞", "睾酮", "血红素", "NADPH", "胆绿素还原酶",
        ], [
            ("血红素合成的原料", ["琥珀酰 CoA", "甘氨酸", "Fe²⁺"]),
            ("血红素合成的限速酶", ["ALA 合酶"]),
            ("ALA 合酶所需的辅酶", ["磷酸吡哆醛"]),
            ("可诱导 ALA 合酶", ["睾酮"]),
            ("对 ALA 合酶具有反馈调节作用", ["血红素"]),
            ("血红素合成的起始和终末阶段位于", ["线粒体"]),
            ("血红素合成的中间阶段位于", ["胞质"]),
            ("铅中毒可抑制的酶", ["亚铁螯合酶", "ALA 脱水酶", "粪卟啉原氧化酶"]),
            ("催化血红素向胆绿素转化的酶", ["血红素加氧酶"]),
            ("因缺乏线粒体而不能合成血红素的细胞", ["成熟红细胞"]),
        ], 1),
        bank(10, bilirubin_title, 2, "胆色素的来源、组成与尿三胆", [
            "尿胆红素", "胆汁酸", "过氧化物酶", "胆绿素", "血红蛋白", "尿胆素", "胆固醇", "细胞色素", "胆红素", "肌红蛋白", "尿胆素原", "过氧化氢酶", "胆素原", "胆素", "血红素", "卟胆原",
        ], [
            ("可经代谢生成胆红素的铁卟啉蛋白", ["过氧化物酶", "血红蛋白", "细胞色素", "肌红蛋白", "过氧化氢酶"]),
            ("人体内胆色素", ["胆绿素", "胆红素", "胆素原", "胆素"]),
            ("尿三胆", ["尿胆红素", "尿胆素", "尿胆素原"]),
            ("能够生成胆红素的物质", ["过氧化物酶", "血红蛋白", "细胞色素", "肌红蛋白", "过氧化氢酶"]),
        ], 1),
        bank(10, bilirubin_title, 3, "UCB 与 CB：名称、性质及毒性", [
            "间接胆红素", "非结合胆红素", "游离胆红素", "肝前胆红素", "直接胆红素", "结合胆红素", "葡萄糖醛酸胆红素", "肝胆红素", "脂溶性", "水溶性", "两者均不溶于水", "两者均易溶于水", "易透过细胞膜", "不易透过细胞膜", "与细胞膜通透性无关", "可出现在尿液中", "不会出现在尿液中", "正常情况下二者均大量出现在尿液中", "毒性较大", "毒性较小", "二者毒性完全相同",
        ], [
            ("未结合胆红素 UCB 的名称", ["间接胆红素", "非结合胆红素", "游离胆红素", "肝前胆红素"]),
            ("UCB 的性质与表现", ["脂溶性", "易透过细胞膜", "不会出现在尿液中", "毒性较大"]),
            ("结合胆红素 CB 的名称", ["直接胆红素", "结合胆红素", "葡萄糖醛酸胆红素", "肝胆红素"]),
            ("CB 的性质与表现", ["水溶性", "不易透过细胞膜", "可出现在尿液中", "毒性较小"]),
        ], 2),
        categorized_bank(10, bilirubin_title, 4, "三种黄疸的指标鉴别", [
            ("血主要胆红素", ["血主要胆红素为 UCB↑↑", "血中 CB、UCB 均升高", "血主要胆红素为 CB↑↑"]),
            ("CB/TB", ["CB/TB＜0.2", "CB/TB 为 0.2～0.5", "CB/TB＞0.5"]),
            ("尿胆素原", ["尿胆素原升高", "尿胆素原不定", "尿胆素原降低"]),
            ("尿胆红素", ["尿胆红素阴性", "尿胆红素阳性（＋）", "尿胆红素强阳性（＋＋）"]),
            ("尿色与粪色", ["尿深、粪深", "尿深、粪正常或较浅", "尿深、粪浅甚至白陶土样"]),
            ("ALT、AST、PT", ["ALT、AST、PT 多正常", "ALT、AST、PT 明显升高", "ALT、AST、PT 可升高"]),
            ("ALP、GGT", ["ALP、GGT 多正常", "ALP、GGT 升高", "ALP、GGT 明显升高"]),
        ], [
            ("溶血性黄疸", ["血主要胆红素为 UCB↑↑", "CB/TB＜0.2", "尿胆素原升高", "尿胆红素阴性", "尿深、粪深", "ALT、AST、PT 多正常", "ALP、GGT 多正常"]),
            ("肝细胞性黄疸", ["血中 CB、UCB 均升高", "CB/TB 为 0.2～0.5", "尿胆素原不定", "尿胆红素阳性（＋）", "尿深、粪正常或较浅", "ALT、AST、PT 明显升高", "ALP、GGT 升高"]),
            ("梗阻性黄疸", ["血主要胆红素为 CB↑↑", "CB/TB＞0.5", "尿胆素原降低", "尿胆红素强阳性（＋＋）", "尿深、粪浅甚至白陶土样", "ALT、AST、PT 可升高", "ALP、GGT 明显升高"]),
        ], 2),
        bank(10, bilirubin_title, 5, "遗传性胆红素代谢障碍", [
            "肝细胞摄取＋排泄障碍", "胆红素结合障碍", "肝细胞摄取＋结合障碍", "胆红素排泄障碍", "胆红素生成障碍", "肠肝循环障碍", "UCB↑、CB↑", "CB↑", "UCB↑", "胆红素降低", "CB、UCB 均不变",
        ], [
            ("Gilbert 综合征", ["肝细胞摄取＋结合障碍", "UCB↑"]),
            ("Crigler-Najjar 综合征", ["胆红素结合障碍", "UCB↑"]),
            ("Rotor 综合征", ["肝细胞摄取＋排泄障碍", "UCB↑、CB↑"]),
            ("Dubin-Johnson 综合征", ["胆红素排泄障碍", "CB↑"]),
        ], 2),
    ]
    Path("src/data/biochemistry-lecture10-data.json").write_text(json.dumps(payload(10, bilirubin_title, "胆色素代谢与生物转化学成选择题（胆色素代谢）", 4, bilirubin_groups), ensure_ascii=False, indent=2), encoding="utf-8")

    biotransformation_title = "生化 生物转化"
    biotransformation_groups = [
        bank(11, biotransformation_title, 1, "生物转化概述与Ⅰ相、Ⅱ相反应", [
            "结合反应", "使多数非营养物质水溶性增强", "水解反应", "使所有毒物完全失活", "还原反应", "可使某些激素灭活", "氧化反应", "使多数非营养物质活性降低", "可产生解毒作用，也可能产生致毒作用", "使多数非营养物质水溶性降低", "使极性增强", "第一相反应", "第二相反应", "磷酸化反应", "所有物质均必须先经过Ⅰ相再经过Ⅱ相",
        ], [
            ("生物转化通常产生的总体变化", ["使多数非营养物质水溶性增强", "可使某些激素灭活", "使多数非营养物质活性降低", "使极性增强"]),
            ("生物转化的特点", ["可使某些激素灭活", "使多数非营养物质活性降低", "可产生解毒作用，也可能产生致毒作用"]),
            ("属于Ⅰ相反应", ["水解反应", "还原反应", "氧化反应"]),
            ("Ⅰ相反应中最常见", ["氧化反应"]),
            ("Ⅱ相反应主要是", ["结合反应"]),
            ("“多数非营养物质水溶性降低”对应", ["使多数非营养物质水溶性降低"]),
        ], 1),
        bank(11, biotransformation_title, 2, "Ⅰ相反应的氧化酶类", [
            "UDP-葡萄糖醛酸基转移酶", "醛脱氢酶", "单胺氧化酶", "谷胱甘肽过氧化物酶", "细胞色素 P450", "醇脱氢酶", "羟化酶/单加氧酶", "细胞色素氧化酶", "肝内质网", "肝线粒体", "乙醇→乙醛", "乙醛→乙酸", "细胞核", "葡萄糖醛酸结合",
        ], [
            ("肝细胞中氧化非营养物质的主要酶类", ["羟化酶/单加氧酶"]),
            ("单加氧酶/羟化酶主要依靠的酶系统", ["细胞色素 P450"]),
            ("上述酶系统主要位于", ["肝内质网"]),
            ("肝线粒体中参与生物转化的氧化酶", ["单胺氧化酶"]),
            ("催化乙醇→乙醛", ["醇脱氢酶"]),
            ("催化乙醛→乙酸", ["醛脱氢酶"]),
            ("参与肝生物转化Ⅰ相反应的酶", ["醛脱氢酶", "单胺氧化酶", "细胞色素 P450", "醇脱氢酶", "羟化酶/单加氧酶"]),
            ("属于Ⅱ相结合反应的酶", ["UDP-葡萄糖醛酸基转移酶"]),
        ], 1),
        bank(11, biotransformation_title, 3, "Ⅱ相结合反应：供体、酶与定位", [
            "PAPS", "甘氨酸", "NADPH", "SAM", "GSH", "UDPGA", "乙酰 CoA", "磷酸吡哆醛", "谷胱甘肽-S-转移酶", "甲基转移酶", "葡萄糖醛酸基转移酶", "单加氧酶", "酰基转移酶", "硫酸转移酶", "乙酰基转移酶", "谷胱甘肽过氧化物酶", "线粒体", "细胞核", "内质网", "细胞质", "溶酶体",
        ], [
            ("葡萄糖醛酸结合：供体、酶与定位", ["UDPGA", "葡萄糖醛酸基转移酶", "内质网"]),
            ("硫酸结合：供体、酶与定位", ["PAPS", "硫酸转移酶", "细胞质"]),
            ("乙酰基结合：供体、酶与定位", ["乙酰 CoA", "乙酰基转移酶", "细胞质"]),
            ("谷胱甘肽结合：供体、酶与定位", ["GSH", "谷胱甘肽-S-转移酶", "细胞质"]),
            ("甲基结合：供体、酶与定位", ["SAM", "甲基转移酶", "细胞质"]),
            ("甘氨酰基结合：供体、酶与定位", ["甘氨酸", "酰基转移酶", "线粒体"]),
        ], 1),
        bank(11, biotransformation_title, 4, "苯巴比妥", [
            "抑制肝微粒体单加氧酶", "诱导肝微粒体 UDP-葡萄糖醛酸基转移酶合成", "长期应用可产生耐药性", "减少胆红素与葡萄糖醛酸结合", "诱导肝微粒体单加氧酶合成", "增加胆红素结合", "可用于新生儿黄疸", "抑制细胞色素 P450 合成", "促进未结合胆红素向结合胆红素转化",
        ], [
            ("苯巴比妥长期应用产生耐药性的机制及结果", ["长期应用可产生耐药性", "诱导肝微粒体单加氧酶合成"]),
            ("苯巴比妥影响胆红素代谢的机制及结果", ["诱导肝微粒体 UDP-葡萄糖醛酸基转移酶合成", "增加胆红素结合", "可用于新生儿黄疸", "促进未结合胆红素向结合胆红素转化"]),
        ], 1),
        bank(11, biotransformation_title, 5, "生物转化：解毒不等于一定无毒", [
            "黄曲霉毒素 B₁", "单加氧酶", "环氧黄曲霉毒素", "腺嘌呤", "鸟嘌呤", "DNA 突变", "肝癌", "胆红素", "葡萄糖醛酸基转移酶", "解毒与致毒具有双重性",
        ], [
            ("生物转化具有致毒双重性的经典例子", ["黄曲霉毒素 B₁"]),
            ("将其转化为活性更强中间产物的酶类", ["单加氧酶"]),
            ("形成的活性中间产物", ["环氧黄曲霉毒素"]),
            ("该产物可与 DNA 中结合的碱基", ["鸟嘌呤"]),
            ("后续可能导致的分子变化", ["DNA 突变"]),
            ("最终可增加的疾病风险", ["肝癌"]),
            ("这一过程说明的特点", ["解毒与致毒具有双重性"]),
        ], 1),
    ]
    Path("src/data/biochemistry-lecture11-data.json").write_text(json.dumps(payload(11, biotransformation_title, "胆色素代谢与生物转化学成选择题（生物转化）", 1, biotransformation_groups), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
