#!/usr/bin/env python3
"""Audit the integrated surgery payload and lecture-page assets."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


VERIFIED_GROUPS = {
    "p11-g1": {
        "title": "急性阑尾炎分型",
        "options": {
            "A": "症状轻、无肌紧张", "B": "切口麦氏点",
            "C": "切口右下腹经腹直肌",
            "D": "局限性腹膜炎（局部压痛/反跳痛/肌紧张），阑尾腔内积脓",
            "E": "生理盐水不冲腹腔", "F": "生理盐水冲腹腔",
            "G": "围术期用抗生素", "H": "看情况放引流", "I": "不放引流",
            "J": "生理盐水冲腹腔看情况",
            "K": "阑尾呈暗紫色，腹痛可暂时减轻、但随即弥漫性腹膜炎（全腹压痛/反跳痛/肌紧张），体温进一步升高、肠鸣音、甚至休克",
            "L": "切口偏高",
        },
        "stems": {
            "单纯性": "ABEGI", "化脓性": "BDG", "脓液少": "EI",
            "脓液多": "FH", "坏疽穿孔性": "CFGHK", "妊娠期": "GIJL",
        },
    },
    "p14-g2": {
        "title": "腹股沟管结构",
        "options": {
            "A": "腹股沟镰（腹内斜肌和腹横肌腱膜构成的联合腱）",
            "B": "腹外斜肌腱膜（主要）", "C": "腹横筋膜", "D": "腹内斜肌",
            "F": "腹股沟韧带（腹外斜肌腱膜卷曲形成）", "G": "腹膜",
            "H": "腹横肌", "I": "腔隙韧带",
        },
        "stems": {"前": "BD", "后": "ACG", "上": "DH", "下": "FI"},
    },
    "p28-g1": {
        "title": "泌尿系结石成分与特点",
        "options": {
            "A": "易碎", "B": "硬", "C": "光滑", "D": "蜡样", "E": "鹿角样",
            "F": "桑葚样", "G": "颗粒状", "H": "灰白色", "I": "棕褐色",
            "J": "红色", "K": "黄色", "L": "糙", "M": "最常见",
            "N": "酸化尿液+抗感染", "O": "X线高密度", "P": "X线不显影",
        },
        "stems": {
            "草酸钙": "BFILMO", "磷酸钙": "AEHLNO",
            "尿酸盐": "BCGJP", "胱氨酸": "BCDKP",
        },
    },
    "p26-g3": {
        "title": "膀胱癌T分期",
        "options": {
            "A": "T1", "B": "T3", "C": "Tis",
            "D": "T2", "E": "Ta", "F": "T4",
        },
        "stems": {
            "没有突破基底膜、也没有突出黏膜表面": "C",
            "非浸润性乳头状癌": "E",
            "侵犯固有层或黏膜下层": "A",
            "侵犯肌层": "D",
            "原位癌／非浸润癌": "CE",
            "非肌层浸润的膀胱移行细胞癌": "ACE",
            "肌层浸润的膀胱移行细胞癌": "BDF",
        },
    },
    "p27-g1": {
        "title": "血尿出现时相与病变部位",
        "options": {
            "A": "上尿路（肾和输尿管）病变", "B": "膀胱炎",
            "C": "前尿道损伤", "D": "膀胱结石", "E": "少数肾结核",
            "F": "膀胱结核", "G": "泌外恶性肿瘤（多数膀胱癌、上尿路癌、肾癌等）",
            "H": "膀胱癌", "I": "多数肾结核",
        },
        "stems": {"全程血尿": "AEG", "初始血尿": "C", "终末血尿": "BDFHI"},
    },
    "p28-g2": {
        "title": "尿路结石与胆系结石鉴别",
        "options": {
            "A": "西北地区多见", "B": "与钙代谢异常有关",
            "C": "成分主要是胆固醇等", "D": "X线显影",
            "E": "X线部分显影", "F": "碎石、取石或其它",
            "G": "南方地区多见", "H": "与钙代谢异常无关",
            "I": "成分主要是草酸钙、磷酸钙", "J": "X线不显影",
            "K": "胆囊结石切胆囊、胆管结石取石或其它",
        },
        "stems": {
            "尿路结石": "BFGI", "草酸钙": "D", "磷酸钙": "D",
            "尿酸盐": "J", "胱氨酸": "J", "胆系结石": "ACHK",
            "纯胆固醇结石": "J", "混合性结石": "D", "胆色素结石": "E",
        },
    },
    "p29-g4": {
        "title": "尿失禁类型",
        "options": {
            "A": "尿液不连续从尿道口不自主流出、呈滴沥样、夜间多见",
            "B": "假性尿失禁",
            "C": "完全失去控制排尿的能力，任何时间、体位下尿液均会持续不自主从尿道口流出",
            "D": "患者每次排尿时尿液都难以排尽、膀胱内残余尿逐渐增多、膀胱过度充盈导致膀胱内压超过尿道阻力",
            "E": "多见于膀胱炎、神经源性膀胱、重度膀胱出口梗阻引起的膀胱不稳定收缩",
            "F": "平常控制排尿能力正常，但咳嗽、起立等腹内压增加时少量尿液不自主从尿道口流出",
            "G": "多见于外伤、手术、先天性疾病引起的膀胱颈和尿道括约肌损伤",
            "H": "多见于前列腺增生、肿瘤、尿道狭窄等下尿路慢性梗阻或神经系统疾病导致膀胱逼尿肌收缩无力",
            "I": "严重的尿频、尿急而膀胱不受意识控制就开始排尿",
            "J": "真性尿失禁",
            "K": "多见于多产妇、绝经后引起的阴道前壁支撑力下降和盆腔组织功能障碍或前列腺手术后引起的尿道外括约肌损伤",
        },
        "stems": {
            "持续性尿失禁": "CGJ", "充溢性尿失禁": "ABDH",
            "急迫性尿失禁": "EI", "压力性尿失禁": "FK",
        },
    },
}

VERIFIED_COLORECTAL_OPTIONS = {
    "p11-g2": ["结肠镜", "明确局部浸润、转移等以分期", "判断预后、监测复发、辅助诊断", "与肿瘤分期有关", "直肠指检", "大便隐血试验"],
    "p11-g3": ["结肠脾曲癌", "结肠肝曲癌", "横结肠中部癌", "乙状结肠癌", "降结肠癌", "升结肠癌", "盲肠癌"],
    "p12-g1": ["切除、一期吻合术", "支架置入、限期切除", "右半结肠切除、一期回肠-结肠吻合术", "切除肿瘤、近端造口与远端封闭"],
    "p12-g2": ["腹膜返折以下/距肛缘<7cm/距齿状线<5cm", "腹膜返折以下/距肛缘≤7cm/距齿状线≤5cm", "腹膜返折以上/距肛缘≥7cm/距齿状线≥5cm", "腹膜返折以上/距肛缘>7cm/距齿状线>5cm", "急性肠梗阻不宜行Dixon术", "不耐受Miles术"],
    "p12-g3": ["肛门外括约肌和肛提肌受累", "肛门外括约肌和肛提肌未受累，即使低位也可"],
    "p12-g4": ["肛管", "来源内胚层", "皮肤，相对不易破裂", "肛管动脉", "直肠上静脉→门静脉", "腹股沟浅淋巴结", "直肠上动脉（主要）", "内脏（交感、副交感），痛觉不敏感", "鳞癌", "直肠", "来源于外胚层", "黏膜，易破裂出血", "骶正中动脉", "直肠下静脉和肛管静脉→下腔静脉", "肠系膜下动脉旁和髂内淋巴结", "直肠下动脉", "躯体（阴部神经），痛觉敏感", "腺癌", "内痔", "外痔"],
    "p13-g1": ["出血（鲜血）", "脱出（不能还纳或还纳后再次脱出）", "脱出（需用手还纳）", "脱出（可自行还纳）"],
    "p13-g2": ["12", "9/1/5", "6", "3/7/11"],
    "p13-g3": ["局部症状明显", "局部症状不明显", "最常见", "全身症状明显", "最少见", "全身症状不明显", "可有直肠和/或膀胱刺激征"],
    "p13-g4": ["挂线", "切除肛瘘", "切开肛瘘"],
    "p13-g5": ["柔软光滑", "条索状肿物", "可推动的、有蒂", "不用直肠指检", "易出血肿物", "可出血肿物", "触及不规则", "柔软的血管团", "质硬", "波动感"],
}

VERIFIED_HERNIA_GROUPS = {
    "p14-g1": ("股管结构", "ABCD", {"前": "C", "后": "B", "内": "A", "外": "D"}),
    "p14-g2": ("腹股沟管结构", "ABCDFGHI", {"前": "BD", "后": "ACG", "上": "DH", "下": "FI"}),
    "p14-g3": ("直疝三角/海氏三角/Hesselbach 三角", "ABC", {"内侧": "B", "底部": "C", "外侧": "A"}),
    "p14-g4": ("疝的组成", "AB", {"疝内容物": "B", "疝囊": "A"}),
    "p14-g5": ("腹外疝临床分型", "ABCDEFGH", {"易复疝": "ACD", "难复疝": "ADE", "嵌顿疝": "ABEGH", "绞窄疝": "BEF"}),
    "p14-g6": ("腹外疝类型与常见内容物", "ABCDEF", {"易复疝": "B", "难复疝": "D", "特殊的难复疝-滑动性疝": "ACEF"}),
    "p15-g1": ("特殊类型嵌顿疝", "ABCDE", {"Richter疝（肠管壁疝）": "B", "Littre疝": "A", "Maydl疝（逆行性嵌顿疝）": "EC", "Amyand疝": "D"}),
    "p15-g2": ("腹外疝治疗方式", "ABCDE", {"保守": "BCE", "单纯疝囊高位结扎": "AD"}),
    "p15-g3": ("腹股沟疝修补术式", "ABCDEFGH", {"单纯疝修补/无张力疝修补": "CEG", "疝囊高位结扎+修补加强前壁": "A", "加强后壁": "BDFH"}),
    "p15-g4": ("传统疝修补术特点", "ABCDEF", {"Bassini": "B", "McVay": "ADF", "Shouldice": "CE"}),
    "p16-g1": ("股疝、斜疝与直疝鉴别", "ABCDEFGHIJKLMNOPQRSTUV", {"股疝": "ADHIKNT", "斜疝": "CFJLMOQSU", "直疝": "BCEGIKPRV"}),
    "p16-g2": ("隐睾（阴囊空虚感）治疗", "ABCDE", {"1岁内": "D", "1岁后": "A", "2岁前": "E", "睾丸萎缩且对侧睾丸正常": "B", "双侧睾丸不能下降": "C"}),
}

VERIFIED_HERNIA_OPTIONS = {
    "p14-g1": ["腔隙韧带（腹股沟韧带的延伸结构）", "耻骨梳/Cooper韧带（腹股沟韧带的延伸结构）", "腹股沟韧带", "股血管"],
    "p14-g2": ["腹股沟镰（腹内斜肌和腹横肌腱膜构成的联合腱）", "腹外斜肌腱膜（主要）", "腹横筋膜", "腹内斜肌", "腹股沟韧带（腹外斜肌腱膜卷曲形成）", "腹膜", "腹横肌", "腔隙韧带"],
    "p14-g3": ["腹壁下动脉", "腹直肌外缘", "腹股沟韧带"],
    "p14-g4": ["壁层腹膜", "脏层腹膜"],
    "p14-g5": ["无腹膜刺激征", "有疼痛", "包块可消失", "无疼痛", "包块不可消失", "有腹膜刺激征", "包块因卡住反而增大", "可伴机械性肠梗阻（肠鸣音亢进）"],
    "p14-g6": ["盲肠", "小肠", "阑尾", "大网膜", "乙状结肠", "膀胱"],
    "p15-g1": ["嵌顿内容物为小肠憩室，如Meckel憩室", "嵌顿内容物仅为部分肠管壁，局部肿块不明显，多无肠梗阻，易误诊", "即使疝囊内肠管存活，也必须将腹腔内相关肠袢牵出检查，以防遗漏隐匿在腹腔内的坏死肠袢", "嵌顿内容物为阑尾，常感染化脓（appendix）", "嵌顿肠管包括几个肠袢，呈W形"],
    "p15-g2": ["＞1岁婴幼儿", "＜1岁", "＜2岁脐疝", "绞窄疝", "不耐受手术"],
    "p15-g3": ["Ferguson", "Bassini", "Rutkow", "McVay", "Stoppa", "Shouldice", "Lichtenstein", "Halsted法"],
    "p15-g4": ["股疝", "最常用", "成人的大斜疝和直疝", "严重薄弱者", "重点修补腹横筋膜和内环", "把腹内斜肌和联合腱缝合至耻骨梳韧带"],
    "p16-g1": ["中老年肥胖女性多见", "好发老年男性", "包块在腹股沟韧带上方", "疝块小呈半球形", "半球形、基底较宽", "多进入阴囊/大阴唇", "偶尔进入阴囊/大阴唇", "绝对不进入阴囊/大阴唇", "咳嗽冲击感不明显", "回纳疝块后压住内口疝块不再突出", "回纳疝块后压住内口疝块仍可突出", "咳嗽冲击感多明显", "易嵌顿", "最易嵌顿", "疝囊颈在腹壁下动脉外侧", "疝囊颈在腹壁下动脉内侧", "精索/子宫圆韧带在疝囊后方", "精索/子宫圆韧带在疝囊前外方", "好发儿童、青年男性", "包块在腹股沟韧带下方", "椭圆或梨形、呈蒂柄状", "不易嵌顿"],
    "p16-g2": ["短期用hCG", "切除未降睾丸", "睾丸自体移植术", "自行下降", "睾丸固定术"],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/surgery-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["sourcePdfPages"] == 29
    assert payload["meta"]["sourcePages"] == 29
    assert payload["meta"]["lectureCount"] == 38

    ids = [group["id"] for group in payload["groups"]]
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert all(group.get("stems") for group in payload["groups"]), "empty question group"

    invalid_answers = []
    duplicate_answers = []
    duplicate_option_keys = []
    empty_answers = []
    text_issues = []
    missing_images = []
    missing_lecture_evidence = []
    lecture_images = set()
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        evidence = group.get("lectureEvidence") or {}
        evidence_image = evidence.get("image", "")
        if not evidence_image:
            missing_lecture_evidence.append(group["id"])
        else:
            lecture_images.add(evidence_image)
            image_path = root / "public" / evidence_image
            if not image_path.exists():
                missing_images.append(str(image_path))
        option_keys = [option["key"] for option in group.get("options", [])]
        keys = set(option_keys)
        if len(option_keys) != len(keys):
            duplicate_option_keys.append(group["id"])
        if group.get("reviewState") == "待原题页核对" or group.get("reviewIssues"):
            text_issues.append(f"{group['id']}:review")
        values = [group.get("title", "")]
        values.extend(option.get("label", "") for option in group.get("options", []))
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            values.append(stem.get("text", ""))
            if stem.get("answerState") or not answer:
                empty_answers.append(f"{group['id']}:{index}")
            if len(answer) != len(set(answer)):
                duplicate_answers.append(f"{group['id']}:{index}")
            absent = [key for key in answer if key not in keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{index}={''.join(absent)}")
        for value in values:
            if (
                not value.strip()
                or any(char in value for char in "|°•“”‘’")
                or "请结合原题页" in value
                or value.count("（") != value.count("）")
                or value.count("(") != value.count(")")
                or re.search(r"\s{2,}", value)
            ):
                text_issues.append(f"{group['id']}:{value}")

    assert not missing_images, f"missing source images: {missing_images}"
    assert not missing_lecture_evidence, f"groups without lecture evidence: {missing_lecture_evidence}"
    for image_name in sorted(lecture_images):
        image_path = root / "public" / image_name
        header = image_path.read_bytes()[:12]
        assert image_path.suffix.lower() == ".webp", f"lecture image extension is not WebP: {image_name}"
        assert header[:4] == b"RIFF" and header[8:12] == b"WEBP", \
            f"lecture image content is not WebP: {image_name}"
    assert not duplicate_option_keys, f"duplicate option keys: {duplicate_option_keys}"
    assert not empty_answers, f"empty or unresolved answers: {empty_answers}"
    assert not duplicate_answers, f"duplicate answer keys: {duplicate_answers}"
    assert not invalid_answers, f"answers missing from option bank: {invalid_answers}"
    assert not text_issues, f"text/review issues: {text_issues}"

    groups_by_id = {group["id"]: group for group in payload["groups"]}
    corrected_cross_chapter_pages = {
        "p05-g4": ("lecture-04", 1),
        "p06-g1": ("lecture-04", 2),
        "p06-g2": ("lecture-05", 1),
        "p06-g3": ("lecture-05", 2),
        "p06-g4": ("lecture-05", 3),
        "p07-g3": ("lecture-06", 1),
        "p07-g4": ("lecture-06", 1),
        "p18-g4": ("lecture-16", 12),
    }
    for group_id, expected in corrected_cross_chapter_pages.items():
        evidence = groups_by_id[group_id]["lectureEvidence"]
        assert (evidence["lectureId"], evidence["page"]) == expected, \
            f"{group_id}: cross-chapter lecture evidence drift"
    colorectal_ids = {group["id"] for group in payload["groups"] if group["topic"] == "结直肠与肛管疾病"}
    assert colorectal_ids == set(VERIFIED_COLORECTAL_OPTIONS), f"colorectal group drift: {sorted(colorectal_ids)}"
    for group_id, expected_options in VERIFIED_COLORECTAL_OPTIONS.items():
        actual_options = [item["label"] for item in groups_by_id[group_id]["options"]]
        assert actual_options == expected_options, f"{group_id}: colorectal option drift"

    for group_id, expected in VERIFIED_GROUPS.items():
        group = groups_by_id[group_id]
        assert group["title"] == expected["title"], f"{group_id}: title drift"
        assert {item["key"]: item["label"] for item in group["options"]} == expected["options"], \
            f"{group_id}: option drift"
        assert {item["text"]: "".join(item["answer"]) for item in group["stems"]} == expected["stems"], \
            f"{group_id}: stem/answer drift"

    hernia_ids = {group["id"] for group in payload["groups"] if group["topic"] == "腹外疝"}
    assert hernia_ids == set(VERIFIED_HERNIA_GROUPS), f"hernia group drift: {sorted(hernia_ids)}"
    for group_id, (title, option_keys, stems) in VERIFIED_HERNIA_GROUPS.items():
        group = groups_by_id[group_id]
        assert group["title"] == title, f"{group_id}: title drift"
        assert "".join(item["key"] for item in group["options"]) == option_keys, f"{group_id}: option-key drift"
        assert {item["text"]: "".join(item["answer"]) for item in group["stems"]} == stems, \
            f"{group_id}: hernia stem/answer drift"
        assert group["reviewState"] == "已按原题页人工复核", f"{group_id}: review state drift"
        assert [item["label"] for item in group["options"]] == VERIFIED_HERNIA_OPTIONS[group_id], \
            f"{group_id}: hernia option drift"

    assert groups_by_id["p15-g4"]["reviewNotes"] == [{
        "title": "Halsted原题信息不完整",
        "body": "原题第15页列出了Halsted，但没有圈选答案；第12讲也仅列出术式名称，选项池中没有Halsted的专属特点。因此未擅自配答案，也不将其纳入计分题干。",
    }], "p15-g4: Halsted review note drift"

    hernia_evidence = {
        "p14-g2": {
            "lectureId": "lecture-12", "page": 1,
            "image": "surgery/lecture-pages/lecture-12-page-01.webp",
            "title": "第12讲第1页 · 股管与腹股沟管结构",
            "description": "讲义逐项列出股环四界、腹股沟管四壁及直疝三角边界，用于核对本页解剖题组。",
        },
        "p16-g1": {
            "lectureId": "lecture-12", "page": 5,
            "image": "surgery/lecture-pages/lecture-12-page-05.webp",
            "title": "第12讲第5页 · 股疝、斜疝与直疝鉴别",
            "description": "讲义表格对照好发人群、突出途径、压内口试验、外形、阴囊关系、咳嗽冲击感、精索位置、动脉关系及嵌顿几率。",
        },
    }
    for group_id, evidence in hernia_evidence.items():
        assert groups_by_id[group_id]["lectureEvidence"] == evidence, f"{group_id}: lecture evidence drift"
        evidence_image = root / "public" / evidence["image"]
        assert evidence_image.exists(), f"missing lecture evidence image: {evidence_image}"

    phosphate_evidence = groups_by_id["p28-g1"]["lectureEvidence"]
    assert phosphate_evidence == {
        "lectureId": "lecture-19",
        "page": 1,
        "image": "surgery/lecture-pages/lecture-19-page-01.webp",
        "title": "第19讲第1页 · 泌尿系结石",
        "description": "讲义在“磷酸钙”条目下明确列出“酸化尿液+抗感染”，因此本题答案包含 N。",
    }, "p28-g1: lecture evidence drift"
    lecture_image = root / "public" / phosphate_evidence["image"]
    assert lecture_image.exists(), f"missing lecture evidence image: {lecture_image}"

    colorectal_evidence = groups_by_id["p12-g4"]["lectureEvidence"]
    assert colorectal_evidence == {
        "lectureId": "lecture-11",
        "page": 1,
        "image": "surgery/lecture-pages/lecture-11-page-01.webp",
        "title": "第11讲第1页 · 齿状线上下鉴别",
        "description": "讲义表格逐项列出齿状线上下的分界、来源、组织、血管、淋巴、神经、癌变及痔的对应关系。",
    }, "p12-g4: lecture evidence drift"
    colorectal_lecture_image = root / "public" / colorectal_evidence["image"]
    assert colorectal_lecture_image.exists(), f"missing lecture evidence image: {colorectal_lecture_image}"

    bladder_staging_evidence = groups_by_id["p26-g3"]["lectureEvidence"]
    assert bladder_staging_evidence == {
        "lectureId": "lecture-18", "page": 2,
        "image": "surgery/lecture-pages/lecture-18-page-02.webp",
        "title": "第18讲第2页 · 膀胱癌T分期",
        "description": "讲义明确区分Tis、Ta、T1及T2-T4：T1侵犯固有层或黏膜下层，T2侵犯肌层。",
    }, "p26-g3: lecture evidence drift"
    bladder_staging_image = root / "public" / bladder_staging_evidence["image"]
    assert bladder_staging_image.exists(), f"missing lecture evidence image: {bladder_staging_image}"

    hematuria_evidence = groups_by_id["p27-g1"]["lectureEvidence"]
    assert hematuria_evidence == {
        "lectureId": "lecture-18", "page": 3,
        "image": "surgery/lecture-pages/lecture-18-page-03.webp",
        "title": "第18讲第3页 · 尿三杯与血尿时相",
        "description": "讲义明确：终末血尿可见于肾和膀胱结核、膀胱炎、膀胱结石及膀胱癌。",
    }, "p27-g1: lecture evidence drift"
    hematuria_image = root / "public" / hematuria_evidence["image"]
    assert hematuria_image.exists(), f"missing lecture evidence image: {hematuria_image}"

    stone_comparison_evidence = groups_by_id["p28-g2"]["lectureEvidence"]
    assert stone_comparison_evidence == {
        "lectureId": "lecture-19", "page": 2,
        "image": "surgery/lecture-pages/lecture-19-page-02.webp",
        "title": "第19讲第2页 · 尿路结石与胆系结石鉴别",
        "description": "讲义表格逐项对照地区、钙代谢、主要成分、X线表现和治疗方式。",
    }, "p28-g2: lecture evidence drift"
    stone_comparison_image = root / "public" / stone_comparison_evidence["image"]
    assert stone_comparison_image.exists(), f"missing lecture evidence image: {stone_comparison_image}"

    unresolved = [
        f"{group['id']}:{index}"
        for group in payload["groups"]
        for index, stem in enumerate(group["stems"])
        if stem.get("answerState")
    ]
    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group["stems"]) for group in payload["groups"]),
        "resolved": sum(
            1 for group in payload["groups"] for stem in group["stems"]
            if not stem.get("answerState")
        ),
        "unresolved": len(unresolved),
        "reviewStates": dict(Counter(group["reviewState"] for group in payload["groups"])),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
