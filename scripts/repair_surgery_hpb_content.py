#!/usr/bin/env python3
"""Clean OCR corruption in hepatobiliary-pancreatic surgery groups."""

from __future__ import annotations

import json
from pathlib import Path


OPTION_UPDATES = {
    "p17-g1": {"I": "胆肠吻合口狭窄（如Whipple术后）"},
    "p17-g2": {"F": "支气管胸膜瘘", "H": "支气管胆瘘"},
    "p17-g3": {
        "C": "血WBC↑，以中性粒细胞为主",
        "I": "血WBC可↑，以嗜酸性粒细胞为主",
    },
    "p18-g1": {"D": "Budd-Chiari综合征（肝静脉和／或下腔静脉阻塞）"},
    "p18-g2": {
        "A": "门静脉压力↑",
        "B": "再出血率↓",
        "C": "临床常用",
        "D": "肠系膜上静脉-下腔静脉分流术",
        "E": "门静脉-腔静脉建立分流通道",
        "F": "脾切除＋贲门周围血管离断术",
        "G": "肝性脑病发生率较低",
        "H": "肝性脑病发生率较高",
        "I": "对肝功能打击较大",
        "J": "阻断门静脉-奇静脉反常血流",
        "K": "门静脉-下腔静脉分流术",
        "L": "近端脾静脉-肾静脉分流术",
        "M": "远端脾静脉-肾静脉分流术",
        "N": "门静脉压力↓",
        "O": "再出血率↑",
        "P": "对肝功能打击较小",
    },
    "p18-g4": {"G": "Courvoisier征（库瓦济埃征）"},
    "p19-g3": {
        "B": "胆囊增大、壁毛糙增厚（＞4 mm）、双边征",
        "C": "肝内胆管＞4 mm、肝外胆管＞10 mm",
    },
    "p20-g1": {
        "A": "鼻胆管引流（ENBD）",
        "B": "经皮经肝胆管穿刺引流（PTCD）",
        "C": "常规T管引流",
    },
    "p20-g2": {
        "A": "胆道无结石残留→术后4周拔管",
        "B": "术后2周行T管造影；若胆道通畅，继续引流1天后闭管",
        "C": "胆道有结石残留→术后4～8周取残余结石",
    },
    "p20-g3": {
        "A": "阵发性胆绞痛：饱餐尤其油腻食物后或夜间出现右上腹绞痛，可向右肩、背部放射",
        "B": "持续性右上腹痛，伴阵发性加剧",
        "D": "WBC明显↑，常＞20×10⁹/L（以中性粒细胞为主），Plt可↓",
        "E": "Murphy征：右上腹触及疼痛、肿大的胆囊",
        "F": "Charcot三联征：胆绞痛、黄疸（随炎症控制呈波动性）、寒战高热",
        "G": "Reynolds五联征：Charcot三联征＋中枢抑制＋休克（血压＜90/60 mmHg）",
        "I": "多无黄疸（仅10%～20%有轻度黄疸）",
        "J": "位于胆囊颈、胆囊管的结石可致Mirizzi综合征",
        "M": "最关键：急诊解除胆管梗阻、降低胆管压力；可行PTCD、ENBD或胆总管切开减压＋T管引流",
        "N": "急诊腹腔镜胆囊切除术（LC）",
        "O": "腹腔镜胆囊切除术（LC）",
        "Q": "1～3个月后彻底手术，以避免复发",
        "S": "急诊PTGD（经皮经肝胆囊穿刺引流）或胆囊造口，3个月后行腹腔镜胆囊切除术",
        "T": "同时抗休克（补充平衡盐液和胶体液）；无好转时纠酸",
    },
    "p21-g2": {
        "C": "结石＜3枚且每枚＜1 cm",
        "E": "胆总管结石，且结石上下方胆管通畅",
    },
    "p21-g4": {"D": "侵犯右肝管（IIIa）或左肝管（IIIb）"},
    "p21-g5": {
        "A": "切除胆囊＋肝外胆管，行胆肠Roux-en-Y吻合术",
        "B": "切除肿瘤及距肿瘤边缘1 cm的胆管，行肝管-空肠Roux-en-Y吻合术",
        "D": "切除胆囊＋肝外胆管＋部分肝，行胆肠Roux-en-Y吻合术",
        "E": "胰头十二指肠切除术（Whipple术），必要时联合切除受累肝组织",
    },
    "p22-g2": {
        "B": "肝外胆管或胆囊与空肠行Roux-en-Y吻合术",
        "D": "Kasai肝门-空肠Roux-en-Y吻合术",
    },
    "p22-g3": {"D": "肝外胆管尤其胆总管囊性扩张，直径最大可达25 cm"},
    "p23-g1": {
        "B": "不伴胆管梗阻时无黄疸",
        "C": "通常无黄疸，但发生Mirizzi综合征时可有黄疸",
        "Q": "持续性胆绞痛伴阵发性加剧、发热、腹膜炎，胆囊壁＞4 mm",
        "R": "阵发性钻顶样绞痛，突发突止，症征不符",
        "T": "好发于胆囊底部、体部",
        "V": "好发于肝左外叶和右后叶，反复肝区、胸背部闷胀痛",
        "X": "Charcot三联征，甚至Reynolds五联征",
        "Y": "CT用于诊断并评估可切除性",
        "Z": "尽量在出生2个月内手术，如Kasai术",
        "a": "手术治疗",
        "b": "Whipple术",
        "d": "以保守治疗为主",
        "e": "尽早完整切除扩张胆管＋胆肠吻合术等",
    },
    "p23-g2": {
        "A": "经皮穿刺进入肝内胆管，置管减压并持续引流",
        "B": "联合切除胰头、十二指肠及相关胆道等组织的根治性术式",
        "C": "经腹腔镜切除胆囊",
        "D": "深吸气时触及无痛、光滑、肿大的胆囊：见于中下段胆管癌、胰头癌、壶腹癌、十二指肠癌",
        "E": "利用磁共振水成像无创显示胰胆管形态",
        "F": "胆管急性梗阻并发化脓性感染，典型可出现Reynolds五联征",
        "G": "经十二指肠镜逆行插管造影以观察胰胆管",
        "H": "内镜下切开Oddi括约肌并取石，术后留置鼻胆管引流",
        "I": "经皮穿刺进入胆囊，置管减压并持续引流",
    },
}

TITLE_UPDATES = {
    "p18-g2": "门脉高压症·断流术与分流术",
    "p20-g1": "胆道检查后的引流方式",
    "p20-g2": "胆总管探查术后T管管理",
    "p22-g2": "胆管闭锁的手术时机与术式",
    "p23-g1": "胆系疾病综合鉴别",
    "p23-g2": "胆系疾病英文缩写与术式",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = {group["id"]: group for group in payload["groups"]}

    for group_id, updates in OPTION_UPDATES.items():
        group = groups[group_id]
        by_key = {option["key"]: option for option in group["options"]}
        for key, label in updates.items():
            effective_key = {"a": "①", "b": "②", "d": "③", "e": "④"}.get(key, key) \
                if group_id == "p23-g1" else key
            by_key[effective_key]["label"] = label
            by_key[effective_key]["ocrScore"] = 1.0

    for group_id, title in TITLE_UPDATES.items():
        groups[group_id]["title"] = title

    # The source page used OCR-style lowercase keys beyond Z. Replace them with
    # readable circled keys and remap every answer that refers to them.
    composite = groups["p23-g1"]
    key_map = {"a": "①", "b": "②", "d": "③", "e": "④"}
    for option in composite["options"]:
        option["key"] = key_map.get(option["key"], option["key"])
    for stem in composite["stems"]:
        stem["answer"] = [key_map.get(key, key) for key in stem["answer"]]

    # Group 6: re-enter the canonical lecture-page-3 relationships explicitly.
    group6 = groups["p18-g2"]
    canonical_answers = {
        "断流术": ["A", "C", "F", "G", "J", "O", "P"],
        "分流术": ["B", "E", "I", "N"],
        "选择性分流术": ["G", "M"],
        "非选择性分流术": ["H", "D", "K", "L"],
    }
    for stem in group6["stems"]:
        stem["answer"] = canonical_answers[stem["text"]]
        stem["answerMode"] = "多选"
        stem["reviewMethod"] = "讲义第14讲第3页逐项核对"
    group6["lectureIds"] = ["lecture-14"]
    group6["lectureEvidence"] = {
        "lectureId": "lecture-14",
        "page": 3,
        "image": "surgery/lecture-pages/lecture-14-page-03.webp",
        "title": "第14讲 · 门脉高压症第3页",
        "description": "断流术与分流术的压力、再出血率、肝性脑病发生率、肝功能影响及术式已逐项核对。",
    }
    group6["reviewNotes"] = [{
        "title": "第6组答案复核",
        "body": "讲义第3页确认：断流术为A、C、F、G、J、O、P；分流术为B、E、I、N；选择性分流术为G、M；非选择性分流术为H、D、K、L。原答案逻辑正确，误解来自↑、↓等符号被OCR成“个”“」”，现已按讲义重新录入。",
    }]

    # Group 9: the source question page omitted the lecture's shared
    # "X线部分显影" option. The lecture table assigns it to both pigment-stone
    # subtypes, so replace the source page's overbroad visible/non-visible keys.
    group9 = groups["p19-g1"]
    group9["options"] = [
        {"key": "A", "label": "质地硬、杂质少"},
        {"key": "B", "label": "X线常显影"},
        {"key": "C", "label": "剖面呈放射状"},
        {"key": "D", "label": "剖面呈放射状、层状"},
        {"key": "E", "label": "质地软、杂质多"},
        {"key": "F", "label": "X线常不显影"},
        {"key": "G", "label": "胆固醇类结石"},
        {"key": "H", "label": "胆色素结石"},
        {"key": "I", "label": "几乎在胆囊"},
        {"key": "J", "label": "多在胆管"},
        {"key": "K", "label": "X线部分显影"},
    ]
    group9_answers = {
        "纯胆固醇结石": ["C", "F", "G"],
        "混合性结石": ["B", "D", "G"],
        "黑色素结石": ["A", "H", "I", "K"],
        "棕色结石": ["E", "H", "J", "K"],
        "碳酸钙、磷酸钙、棕榈酸钙等": ["B"],
    }
    for stem in group9["stems"]:
        stem["answer"] = group9_answers[stem["text"]]
        stem["answerMode"] = "多选" if len(stem["answer"]) > 1 else "单选"
        stem["reviewMethod"] = "讲义第16讲第1页逐项核对"
    group9["lectureIds"] = ["lecture-16"]
    group9["lectureEvidence"] = {
        "lectureId": "lecture-16",
        "page": 1,
        "image": "surgery/lecture-pages/lecture-16-page-01.webp",
        "title": "第16讲第1页 · 胆系结石分类",
        "description": "讲义表格明确：黑色素结石和棕色结石均为X线部分显影。",
    }
    group9["reviewNotes"] = [{
        "title": "第9组选项与答案补充",
        "body": "原题页漏列“X线部分显影”。按第16讲第1页补为K，并将黑色素结石由AFHI修正为AHIK、棕色结石由BEHJ修正为EHJK；其余三题答案不变。",
    }]

    # Group 26 asks learners to recall abbreviations and named procedures. The
    # original option labels repeated the target strings in parentheses, which
    # revealed the answers. Keep the verified mapping but use definition-only
    # labels with no target acronym or eponym.
    group26 = groups["p23-g2"]
    group26_answers = {
        "AOSC": ["F"],
        "LC": ["C"],
        "PTGD": ["I"],
        "PTCD": ["A"],
        "MRCP": ["E"],
        "治疗性ERCP": ["H"],
        "Whipple术": ["B"],
        "Courvoisier征": ["D"],
    }
    for stem in group26["stems"]:
        stem["answer"] = group26_answers[stem["text"]]
        stem["answerMode"] = "单选"
        stem["reviewMethod"] = "讲义第16讲第12页逐项核对"
    group26["lectureIds"] = ["lecture-16"]
    group26["lectureEvidence"] = {
        "lectureId": "lecture-16",
        "page": 12,
        "image": "surgery/lecture-pages/lecture-16-page-12.webp",
        "title": "第16讲第12页 · 胆系英文缩写与术式",
        "description": "讲义汇总了各缩写、术式和体征的标准对应关系；网站选项已改为不含目标词的定义性描述。",
    }
    group26["reviewNotes"] = [{
        "title": "第26组选项去答案提示",
        "body": "原选项直接重复题干中的缩写或术式名称，已全部改为中文定义、操作过程或临床表现；答案映射仍为F、C、I、A、E、H、B、D。",
    }]

    for group in payload["groups"]:
        if group.get("topic") != "肝胆胰疾病":
            continue
        for option in group.get("options", []):
            option["sourceText"] = f'{option["key"]}. {option["label"]}'
            option["ocrScore"] = 1.0
        for stem in group.get("stems", []):
            stem["sourceText"] = f'{stem["text"]}（{"".join(stem["answer"])}）'
            stem["ocrScore"] = 1.0
        group["sourceText"] = " | ".join(
            [group["title"]]
            + [option["sourceText"] for option in group.get("options", [])]
            + [stem["sourceText"] for stem in group.get("stems", [])]
        )
        group["reviewState"] = "已逐题清理乱码并复核"
        group["reviewIssues"] = []

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
