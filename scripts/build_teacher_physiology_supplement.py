#!/usr/bin/env python3
"""Extract the teacher's physiology after-class questions from the supplied PDF.

Only PDF pages 2-34 belong to physiology. The other subjects in the combined
handout are deliberately outside this pass. Answers here are transcribed from
the handout, not independently reconciled against the 2027 lecture notes.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/data/physiology-teacher-supplement.json"
REPORT = ROOT / "reports/teacher-physiology-supplement-2026-09-14.md"

SECTION_NAMES = {
    1: "绪论、跨膜转运", 2: "细胞电活动、骨骼肌收缩", 3: "细胞信号转导",
    4: "血液", 5: "心脏泵血、血压", 6: "微循环和冠脉循环、心肌电活动和特性",
    7: "心血管调节、通气功能评价", 8: "肺通气、肺换气、气体运输、呼吸调节",
    9: "消化和吸收", 10: "能量代谢、体温、泌尿概述、肾小球滤过",
    11: "小管重吸收和分泌、尿浓缩稀释、调节", 12: "感觉器官功能、神经元及胶质细胞",
    13: "突触传递、中枢抑制和易化、递质和受体",
    14: "神经系统调控躯体运动、脑电波、睡眠、脑高级功能、下丘脑",
    15: "内分泌概述、钙调节激素、生长激素、胰岛素和胰高血糖素",
    16: "甲状腺激素、糖皮质激素", 17: "生殖",
}

# One primary lecture per question keeps each question in exactly one study set.
# The mixed sections in the handout are split at the question level.
LECTURES = {
    1: [1]*7 + [2]*5,
    2: [3]*8 + [4]*2,
    3: [5]*10,
    4: [8]*10,
    5: [9, 9, 9, 10, 10, 10, 9, 9, 9, 9],
    6: [11, 11] + [12]*8,
    7: [13]*8 + [14]*2,
    8: [15]*5 + [16]*3 + [17]*2,
    9: [18, 18, 19, 20, 20, 20, 21, 21, 21, 20],
    10: [23]*4 + [24]*2 + [25]*4,
    11: [26]*10,
    12: [27]*8 + [28]*2,
    13: [31]*5 + [32]*5,
    14: [33]*5 + [34]*5,
    15: [35] + [36]*2 + [37] + [38]*6,
    16: [39]*5 + [40]*5,
    17: [41]*10,
}

FILL_ANSWERS = {
    1: [
        ["外"], ["负"], ["前", "波动"], ["前", "失误"], ["负"], ["不是"],
        ["条件"], ["H"], ["同", "阿米替林"], ["载体易化"], ["出胞"], ["铁"],
    ],
    2: [
        ["阈强度"], ["Ca2+"], ["降低", "降低"], ["开", "关"],
        ["由大变小、再变大", "由小变大、再变小"],
        ["减小", "减小", "增加", "减小"], ["先增加、后减小"],
        ["Ca2+", "Na+"], ["横", "T", "L"], ["不变", "缩短"],
    ],
}

DISEASE_TERMS = [
    "血友病C", "血友病A", "血友病B", "高血压", "心肌纤维化", "心律失常",
    "支气管哮喘", "COPD", "一氧化碳中毒", "慢性胰腺炎", "青光眼", "远视眼",
    "亨廷顿病", "低钾血症", "骨质疏松", "糖尿病", "甲状腺功能亢进",
]

QUESTION_RE = re.compile(r"^(\d{1,2})\.\s*(.*)$")
OPTION_RE = re.compile(r"^([A-D])\.\s*(.*)$")


def clean(text: str) -> str:
    text = text.replace("\u200b", "").replace("\x01", "")
    return re.sub(r"\s+", " ", text).strip()


def page_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = clean(raw)
        if not line or line.startswith("更多实用资料分享") or re.match(r"^第 \d+ 页 共 34 页$", line):
            continue
        lines.append(line)
    return lines


def parse_fill(page_text: str) -> list[dict]:
    blocks = {1: [], 2: []}
    section = None
    current = None
    for line in page_lines(page_text):
        if line.startswith("一、"):
            section = 1
            continue
        if line.startswith("二、"):
            section = 2
            continue
        match = QUESTION_RE.match(line)
        if match and section:
            current = {"number": int(match.group(1)), "page": 2, "text": match.group(2)}
            blocks[section].append(current)
        elif current:
            current["text"] += " " + line
    assert [len(blocks[1]), len(blocks[2])] == [12, 10]
    result = []
    for section, questions in blocks.items():
        for question in questions:
            number = question["number"]
            answers = FILL_ANSWERS[section][number - 1]
            assert len(re.findall(r"_{2,}", question["text"])) == len(answers), (section, number)
            result.append(make_group(section, number, question["page"], question["text"], [], answers, "填空"))
    return result


def parse_choices(section: int, texts: dict[int, str], answers: list[str]) -> list[dict]:
    first_page = 3 + 2 * (section - 3)
    questions: list[dict] = []
    current = None
    active_option = None
    for page in (first_page, first_page + 1):
        for line in page_lines(texts[page]):
            if line.startswith(tuple("一二三四五六七八九十")) and "、" in line and line.split("、", 1)[1] == SECTION_NAMES[section]:
                continue
            match = QUESTION_RE.match(line)
            if match:
                number = int(match.group(1))
                assert number == len(questions) + 1, (section, number, len(questions))
                current = {"number": number, "page": page, "text": match.group(2), "options": []}
                questions.append(current)
                active_option = None
                continue
            option = OPTION_RE.match(line)
            if option and current:
                assert option.group(1) == "ABCD"[len(current["options"])], (section, current["number"], option.group(1))
                current["options"].append({"key": option.group(1), "label": option.group(2)})
                active_option = current["options"][-1]
            elif current and active_option:
                active_option["label"] += " " + line
            elif current:
                current["text"] += " " + line
    assert len(questions) == 10, (section, len(questions))
    result = []
    for question in questions:
        assert len(question["options"]) == 4, (section, question["number"], question["options"])
        raw_answer = answers[question["number"] - 1]
        assert re.fullmatch(r"[ABCD]+", raw_answer), (section, question["number"], raw_answer)
        assert len(raw_answer) == len(set(raw_answer)), (section, question["number"], raw_answer)
        source_mode = "多选" if "多选" in question["text"] else "单选"
        mode = "多选" if len(raw_answer) > 1 else "单选"
        group = make_group(section, question["number"], question["page"], question["text"], question["options"], list(raw_answer), mode)
        if source_mode != mode:
            group["reviewIssues"] = [f"原题标为{source_mode}，参考答案为{raw_answer}；站内按参考答案设为{mode}，需复核。"]
            group["stems"][0]["answerState"] = "待原题页核对"
        if section == 3 and question["number"] == 4:
            # User confirmed AC on 2026-10-31; the source's single-choice label is a typo.
            group["stems"][0].update({
                "text": "以下属于第二信使的有（多选）",
                "answerRaw": "AC", "answer": ["A", "C"],
                "answerMode": "多选", "answerState": "用户确认答案",
            })
            group["kindLabel"] = "多项选择"
            group["reviewState"] = "用户已确认多选答案"
            group["supplementNotice"] = "答案已确认"
            group.pop("reviewIssues", None)
        result.append(group)
    return result


def make_group(section: int, number: int, page: int, stem_text: str, options: list[dict], answer: list[str], mode: str) -> dict:
    lecture_number = LECTURES[section][number - 1]
    source_section = SECTION_NAMES[section]
    title = re.sub(r"（(?:单选题?|多选题?)）", "", stem_text)
    title = title.replace("__________", "___").replace("________", "___")
    if len(title) > 36:
        title = title[:35] + "…"
    diseases = [term for term in DISEASE_TERMS if term in stem_text]
    return {
        "id": f"phys-teacher-{section:02d}-{number:02d}",
        "page": page,
        "sourceKey": "teacher-2026-08",
        "sourceName": "西综课后巩固·生理（教师补充）.pdf",
        "sourceSection": source_section,
        "sourceQuestion": number,
        "title": title,
        "kind": "F" if mode == "填空" else "A",
        "kindLabel": "填空题" if mode == "填空" else ("多项选择" if mode == "多选" else "单项选择"),
        "options": options,
        "stems": [{"number": number, "text": stem_text, "answerRaw": "、".join(answer) if mode == "填空" else "".join(answer), "answer": answer, "answerMode": mode}],
        "sourceText": stem_text + " " + " ".join(item["label"] for item in options),
        "topic": topic_for_lecture(lecture_number),
        "lectureIds": [f"lecture-{lecture_number:02d}"],
        "diseaseTags": diseases,
        "reviewState": "教师资料答案，未按讲义逐项复核",
        "answerSourceLabel": "教师资料答案",
        "supplement": True,
    }


def topic_for_lecture(number: int) -> str:
    ranges = [
        (1, 1, "绪论"), (2, 5, "细胞基本功能"), (6, 8, "血液"),
        (9, 13, "循环系统"), (14, 17, "呼吸系统"), (18, 22, "消化系统"),
        (23, 26, "泌尿系统"), (27, 29, "感觉系统"), (30, 34, "中枢神经系统"),
        (35, 40, "内分泌"), (41, 41, "生殖系统"),
    ]
    if number == 23:
        return "泌尿系统"  # The site currently places energy metabolism/temperature with renal physiology.
    return next(topic for low, high, topic in ranges if low <= number <= high)


def parse_answer_rows(text: str) -> dict[int, list[str]]:
    rows = {}
    for section in range(3, 18):
        numeral = list("一二三四五六七八九十")
        numeral_name = {3:"三",4:"四",5:"五",6:"六",7:"七",8:"八",9:"九",10:"十",11:"十一",12:"十二",13:"十三",14:"十四",15:"十五",16:"十六",17:"十七"}[section]
        match = re.search(rf"^{numeral_name}\s+((?:[ABCD]+\s+){{9}}[ABCD]+)$", text, re.M)
        assert match, (section, numeral)
        rows[section] = match.group(1).split()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pdf", type=Path)
    args = parser.parse_args()
    with pdfplumber.open(args.source_pdf) as document:
        texts = {page: document.pages[page - 1].extract_text() or "" for page in range(2, 35)}
    answers = parse_answer_rows(texts[34])
    groups = parse_fill(texts[2])
    for section in range(3, 18):
        groups.extend(parse_choices(section, texts, answers[section]))
    assert len(groups) == 172 and len({item["id"] for item in groups}) == 172
    lecture_order = {lecture: [] for lecture in range(1, 42)}
    for group in groups:
        lecture_order[int(group["lectureIds"][0].split("-")[1])].append(group)
    ordered = [group for lecture in lecture_order.values() for group in lecture]
    payload = {
        "meta": {"title": "教师课后巩固·生理补充", "sourcePages": 34, "groupCount": 172,
                 "stemCount": 172, "fillCount": 22, "choiceCount": 150,
                 "answerNote": "答案取自原 PDF 第 33–34 页；尚未按 2027 讲义逐项复核。"},
        "pages": [],
        "groups": ordered,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    topic_counts = Counter(group["topic"] for group in ordered)
    lines = ["# 教师课后巩固：生理题归类", "", "原 PDF 第 2–34 页，共 172 题：填空 22，选择 150。答案取自第 33–34 页，尚未按今年讲义逐项复核。站内每讲在原学成题后接补充题。", "", "| 章节 | 题数 |", "| --- | ---: |"]
    for topic, count in topic_counts.items():
        lines.append(f"| {topic} | {count} |")
    lines += ["", "## 按讲义定位", "", "| 讲义 | 题数 | 原 PDF 节号·题号 |", "| --- | ---: | --- |"]
    for number, lecture in lecture_order.items():
        if lecture:
            refs = "、".join(f"{section_chinese(group['sourceSection'])}-{group['sourceQuestion']}" for group in lecture)
            lines.append(f"| 第 {number} 讲 | {len(lecture)} | {refs} |")
    issues = [group for group in ordered if group.get("reviewIssues")]
    lines += ["", "## 待复核", ""]
    for group in issues:
        lines.append(f"- PDF 第 {group['page']} 页，{group['sourceSection']}第 {group['sourceQuestion']} 题：{group['reviewIssues'][0]}本站保留原答案，但暂不自动判分。")
    tagged = [group for group in ordered if group["diseaseTags"]]
    lines += ["", f"## 疾病相关题（题干明确提及，共 {len(tagged)} 题）", ""]
    for group in tagged:
        lines.append(f"- {'、'.join(group['diseaseTags'])}：{section_chinese(group['sourceSection'])}-{group['sourceQuestion']}，第 {int(group['lectureIds'][0][-2:])} 讲，PDF 第 {group['page']} 页")
    lines += ["", "## 数据原则", "", "每题只设一个主归属讲义；疾病名称保存在 `diseaseTags`，可用于检索。题组保留原 PDF 页码和原答案，未将资料中的推广信息作为站点操作指令。", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print({"groups": len(ordered), "lectures": sum(bool(x) for x in lecture_order.values()), "topics": dict(topic_counts)})


def section_chinese(name: str) -> str:
    return {value: str(key) for key, value in SECTION_NAMES.items()}[name]


if __name__ == "__main__":
    main()
