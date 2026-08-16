#!/usr/bin/env python3
"""Build the checked biochemistry lecture 02 (oxidative phosphorylation) payload."""

from __future__ import annotations

import json
import random
from pathlib import Path


TITLE = "生化 氧化磷酸化"


def group(index, title, topic, options, stems, page):
    source_keys = {chr(65 + position): label for position, label in enumerate(options)}
    shuffled = list(options)
    random.Random(30602 + index).shuffle(shuffled)
    if shuffled == options:
        shuffled = shuffled[1:] + shuffled[:1]
    option_keys = {label: chr(65 + position) for position, label in enumerate(shuffled)}
    return {
        "id": f"bio-02-{index:02d}", "page": index, "title": title, "kind": "B", "kindLabel": "B型题",
        "options": [{"key": chr(65 + i), "label": label} for i, label in enumerate(shuffled)],
        "stems": [{"number": i + 1, "text": text, "answerRaw": "、".join(option_keys[source_keys[key]] for key in answer), "answer": [option_keys[source_keys[key]] for key in answer], "answerMode": "多选" if len(answer) > 1 else "单选"} for i, (text, answer) in enumerate(stems)],
        "sourceText": title, "reviewState": "已按 2027 考研讲义核对", "reviewIssues": [], "reviewNotes": [], "topic": topic,
        "lectureIds": ["lecture-02"], "optionShuffleVersion": 1,
        "lectureEvidence": {"lectureId": "lecture-02", "lectureNumber": 2, "lectureTitle": TITLE, "page": page, "image": f"biochemistry/lecture-pages/lecture-02-page-{page:02d}.webp", "title": f"第 02 讲《{TITLE}》· 第 {page} 页", "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。", "method": "按知识点人工映射至 2027 考研生化第 02 讲，并逐项复核。"},
    }


def main():
    shuttle = "胞浆还原当量穿梭与 ATP"
    chain = "呼吸链组成与 P/O 比值"
    regulation = "氧化磷酸化调节与抑制"
    groups = [
        group(1, "胞浆 H 穿梭进入线粒体", shuttle, ["脑", "骨骼肌", "肝", "心", "肾", "磷酸二羟丙酮", "α-磷酸甘油", "草酰乙酸", "天冬氨酸", "苹果酸", "丙酮酸"], [("α-磷酸甘油-磷酸二羟丙酮穿梭：组织", "AB"), ("α-磷酸甘油-磷酸二羟丙酮穿梭：直接参与的重要中间产物", "FG"), ("苹果酸-天冬氨酸穿梭：组织", "CDE"), ("苹果酸-天冬氨酸穿梭：直接参与的重要中间产物", "HIJ")], 1),
        group(2, "ATP 与产生 ATP 的方式", shuttle, ["GTP", "UTP", "CTP", "1,3-二磷酸甘油酸→3-磷酸甘油酸+ATP", "磷酸烯醇式丙酮酸→丙酮酸+ATP", "琥珀酰 CoA→琥珀酸+ATP/GTP", "底物水平磷酸化", "氧化磷酸化/生物氧化（最主要）"], [("合成蛋白质需要", "A"), ("合成糖原需要", "B"), ("合成磷脂需要", "C"), ("产生 ATP 的方式", "GH"), ("底物水平磷酸化", "DEF")], 1),
        group(3, "递 H 与递电子体辨析", chain, ["FH₄", "CoQ", "细胞色素 Cyt", "FAD", "铁硫蛋白 Fe-S", "NAD+"], [("不参与递 H 的有", "ACE"), ("在呼吸链中可传递电子的有", "BCDEF"), ("单递电子体", "CE")], 2),
        group(4, "呼吸链复合体Ⅰ～Ⅳ对比", chain, ["NADH-泛醌还原酶", "琥珀酸-泛醌还原酶", "泛醌-细胞色素 c 还原酶", "细胞色素 c 氧化酶", "FMN", "FAD", "Fe-S", "血红素", "CuA", "CuB", "有质子泵功能", "没有质子泵功能（不能耦联产生 ATP）", "Q 循环"], [("复合体Ⅰ：酶、辅基、质子泵功能", "AEGK"), ("复合体Ⅱ：酶、辅基、质子泵功能", "BFGL"), ("复合体Ⅲ：酶、辅基、质子泵功能、特点", "CGHKM"), ("复合体Ⅳ：酶、辅基、质子泵功能", "DHIJK")], 2),
        group(5, "CoQ、Cyt c、ATP 合酶与化学渗透假说", chain, ["水溶性（与线粒体内膜结合疏松）", "脂溶性强（在线粒体内膜自由扩散）", "双电子传递体", "单电子载体", "不属于任何复合体", "亲水的 F₁（生成 ATP）", "疏水的 F₀（离子通道）", "复合体Ⅰ、Ⅲ、Ⅳ将 H⁺从线粒体基质泵至线粒体膜间隙", "H⁺顺浓度回流时释放能量并耦联生成 ATP", "4 个 H⁺顺浓度回流，其中 1 个 H⁺驱动 F₁ 合成 ATP"], [("Cyt c", "ADE"), ("辅酶 Q/CoQ/泛醌", "BCE"), ("ATP 合酶（复合体Ⅴ）", "FG"), ("化学渗透假说", "HIJ")], 2),
        group(6, "NADH+H⁺、FADH₂ 呼吸链与 P/O 比值", chain, ["多数", "琥珀酸", "脂酰 CoA", "线粒体中的 α-磷酸甘油", "胆碱", "复合体Ⅰ（4H⁺）", "复合体Ⅱ（0H⁺）", "复合体Ⅲ（4H⁺）", "复合体Ⅳ（2H⁺）", "10H⁺", "6H⁺", "2.5", "1.5", "1", "生成 ATP 数与消耗 1/2 O₂ 的比值"], [("NADH+H⁺ 呼吸链：来源", "A"), ("NADH+H⁺ 呼吸链：各复合体泵 H⁺数及总数", "FHIJ"), ("NADH+H⁺ 呼吸链：P/O", "L"), ("FADH₂ 呼吸链：来源", "BCDE"), ("FADH₂ 呼吸链：各复合体泵 H⁺数及总数", "GHIK"), ("FADH₂ 呼吸链：P/O", "M"), ("抗坏血酸的 P/O", "N"), ("P/O 比值", "O")], 3),
        group(7, "呼吸链抑制剂、解偶联剂与 ATP 合酶抑制剂", regulation, ["鱼藤酮", "抗霉素", "粘噻唑菌醇", "异戊巴比妥", "萎锈灵", "粉蝶霉素", "CN⁻阻断氧化型 a₃", "CO 阻断还原型 a₃-O₂", "寡霉素", "二环己基碳二亚胺 DCCD", "游离脂肪酸", "二硝基苯酚", "新生儿褐/棕色脂肪组织的解偶联蛋白", "ADP"], [("抑制呼吸链复合体Ⅰ的物质", "ADF"), ("抑制呼吸链复合体Ⅱ的物质", "E"), ("抑制呼吸链复合体Ⅲ的物质", "BC"), ("导致整条呼吸链失效的呼吸链抑制剂", "GH"), ("ATP 合酶抑制剂", "IJ"), ("解偶联剂", "KLM"), ("氧化磷酸化调节最重要的物质", "N")], 3),
        group(8, "氧化磷酸化调节与解偶联机制", regulation, ["ADP", "线粒体 mtDNA 突变", "线粒体内膜选择性协调转运：影响 H⁺、ATP-ADP 转位酶等", "甲状腺激素激动核受体→促进基因表达", "诱导钠钾泵→利用 ATP↑→ADP↑→氧化磷酸化速率↑", "诱导解偶联蛋白→电子传递能量转化为热能→基础代谢率和产热↑", "氧利用继续但磷酸化停止", "能在线粒体内膜自由移动、破坏 H⁺电化学梯度", "形成质子通道", "促进 H⁺经解偶联蛋白回流", "不能维持体温→新生儿硬肿症", "结合 F₀ 的 c 亚基"], [("氧化磷酸化的调节：①最主要 ②线粒体 ③线粒体内膜 ④脂溶性配体", "ABCD"), ("甲状腺激素", "EF"), ("解偶联后的结果", "G"), ("二硝基苯酚", "H"), ("新生儿褐/棕色脂肪组织的解偶联蛋白", "I"), ("游离脂肪酸", "J"), ("新生儿缺乏棕色脂肪组织", "K"), ("寡霉素", "L")], 3),
    ]
    payload = {"meta": {"title": "生物化学第 02 讲题库", "sourceLabel": "生化第 02 讲学成选择题（辨析版）", "sourcePages": 1, "lectureCount": 1, "groupCount": len(groups), "stemCount": sum(len(g["stems"]) for g in groups), "correctionGroupCount": 0, "generatedBy": "scripts/build_biochemistry_lecture2.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "仅收录第 02 讲《氧化磷酸化》范围内题目；选项与答案已按讲义复核。"}, "topics": ["全部", shuttle, chain, regulation, "综合"], "pages": [{"page": g["page"], "image": "", "topic": g["topic"], "searchText": g["title"]} for g in groups], "groups": groups, "lectures": [{"id": "lecture-02", "number": 2, "title": TITLE, "pageCount": 8}]}
    Path("src/data/biochemistry-lecture2-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
