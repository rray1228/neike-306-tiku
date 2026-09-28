#!/usr/bin/env python3
"""Convert the checked vitamin workbook into the lecture 13 site payload."""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

SOURCE = Path("/Users/ray/Downloads/生化_维生素_学成选择题_连续编号版.docx")
OUTPUT = Path(__file__).resolve().parents[1] / "src/data/biochemistry-lecture13-data.json"
LECTURE_NUMBER = 13
TITLE = "生化 维生素"
TOPIC = "维生素"
GROUP_RE = re.compile(r"^第\s*(\d+)\s*组[｜|]\s*(.+)$")
ANSWER_GROUP_RE = re.compile(r"^第\s*(\d+)\s*组$")
QUESTION_RE = re.compile(r"^(\d+)\.\s*(.+)$")


def option_key(position):
    """Return spreadsheet-style option keys: A...Z, AA...AZ, BA..."""
    value = position + 1
    result = []
    while value:
        value, remainder = divmod(value - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))


def parse_options(table):
    return [
        (row.cells[0].text.strip(), row.cells[1].text.strip())
        for row in table.rows[1:]
        if row.cells[0].text.strip() and row.cells[1].text.strip()
    ]


def parse_workbook():
    from docx import Document

    doc = Document(SOURCE)
    groups = []
    current = None
    mode = ""
    answer_group = None

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if text == "答案":
            mode = "answers"
            continue
        if mode == "answers":
            answer_match = ANSWER_GROUP_RE.match(text)
            if answer_match:
                answer_group = int(answer_match.group(1))
                continue
            question = QUESTION_RE.match(text)
            if question and answer_group is not None:
                groups[answer_group - 1]["answers"][int(question.group(1))] = re.findall(r"[A-Z]", question.group(2))
            continue

        group_match = GROUP_RE.match(text)
        if group_match:
            current = {
                "source_index": int(group_match.group(1)),
                "title": group_match.group(2).strip(),
                "stems": [],
                "answers": {},
            }
            groups.append(current)
            mode = ""
            continue
        if current is None:
            continue
        if text == "题目":
            mode = "stems"
            continue
        if mode == "stems":
            question = QUESTION_RE.match(text)
            if question:
                current["stems"].append((int(question.group(1)), question.group(2).strip()))

    # The source has one logical option pool per group, split across tables only
    # for readability. Keep the letters continuous after joining those pieces.
    table_counts = [2, 1, 2, 2, 3]
    tables = iter(doc.tables)
    for group, count in zip(groups, table_counts):
        options = []
        for _ in range(count):
            options.extend(parse_options(next(tables)))
        group["options"] = options
        expected = {number for number, _ in group["stems"]}
        if set(group["answers"]) != expected:
            raise ValueError(f"Group {group['source_index']}: question and answer keys do not match")
        if set(key for key, _ in options) != {chr(65 + i) for i in range(len(options))}:
            raise ValueError(f"Group {group['source_index']}: option keys are not continuous")
        for _, letters in group["answers"].items():
            if not set(letters).issubset(dict(options)):
                raise ValueError(f"Group {group['source_index']}: answer has an unknown option")
    try:
        next(tables)
    except StopIteration:
        return groups
    raise ValueError("Unexpected extra option table")


def merge_cofactor_groups(first, second):
    """Join the two halves of the lecture's single vitamin cofactor table."""
    options = []
    label_to_key = {}
    for group in (first, second):
        for _, label in group["options"]:
            if label not in label_to_key:
                key = option_key(len(options))
                label_to_key[label] = key
                options.append((key, label))

    stems = []
    answers = {}
    next_number = 1
    for group in (first, second):
        original = dict(group["options"])
        for number, text in group["stems"]:
            stems.append((next_number, text))
            answers[next_number] = [label_to_key[original[key]] for key in group["answers"][number]]
            next_number += 1

    return {
        "source_index": first["source_index"],
        "title": "辅因子小结：B族维生素、VitK 与 VitC",
        "stems": stems,
        "answers": answers,
        "options": options,
    }


def organize_cofactor_options(group):
    """Deduplicate the shared table and group choices without splitting its stems.

    Keep the existing site's storage keys; displayKey alone controls the new
    continuous lettering, so saved selections do not silently change meaning.
    """
    sections = {
        "衍生物 / 辅因子": [
            ("A", "生物素"), ("E", "钴胺素（含金属）"),
            ("F", "焦磷酸硫胺素（TPP）"), ("G", "磷酸吡哆醛"),
            ("I", "四氢叶酸（FH₄）"), ("L", "辅酶 A（H～SCoA）"),
            ("S", "NAD"), ("X", "FMN"), ("AF", "NADP"),
            ("AQ", "FAD"), ("AR", "酰基载体蛋白（H～SACP）"),
        ],
        "相关酶": [
            ("B", "氨基酸脱羧酶"), ("C", "谷氨酸脱氢酶（NAD 和 NADP）"),
            ("D", "多数脱氢酶"), ("J", "线粒体磷酸甘油脱氢酶"),
            ("K", "黄嘌呤氧化酶"), ("P", "琥珀酸脱氢酶"),
            ("Q", "胆碱脱氢酶"), ("R", "丙酮酸脱氢酶复合体"),
            ("V", "转氨酶"), ("W", "ALA 合酶（合成血红素）"),
            ("Z", "脂酰 CoA 脱氢酶"), ("AC", "γ-谷氨酰羧化酶"),
            ("AD", "丙酮酸羧化酶（糖异生）"), ("AE", "苹果酸酶"),
            ("AJ", "6-磷酸葡萄糖酸脱氢酶"),
            ("AK", "乙酰 CoA 羧化酶（合成脂肪酸）"),
            ("AL", "G6PD"), ("AO", "磷酸化酶（分解糖原）"), ("AP", "羟化酶"),
        ],
        "生理作用 / 缺乏后果": [
            ("H", "α-酮酸（丙酮酸、α-酮戊二酸等）脱羧"),
            ("M", "生物氧化呼吸链的双递氢体"), ("N", "胶原蛋白成熟"),
            ("O", "转移醛基"), ("T", "从头合成嘌呤核苷酸"),
            ("U", "前胶原分子中脯氨酸、赖氨酸的羟化"), ("Y", "递一碳单位"),
            ("AA", "SAM 循环：同型半胱氨酸 + N⁵-CH₃-FH₄ → 甲硫氨酸"),
            ("AG", "影响伤口愈合"), ("AH", "递酰基"), ("AI", "dUMP → dTMP"),
        ],
    }
    wording = {
        "辅酶 A（H～SCoA）": "辅酶 A（CoA）",
        "酰基载体蛋白（H～SACP）": "酰基载体蛋白（ACP）",
        "G6PD": "葡萄糖-6-磷酸脱氢酶（G6PD）",
        "递一碳单位": "转移一碳单位",
        "递酰基": "转移酰基",
        "影响伤口愈合": "缺乏时伤口愈合障碍",
    }
    label_keys = {}
    options = []
    for index, (category, entries) in enumerate(sections.items()):
        entries = list(entries)
        random.Random(31303 + index).shuffle(entries)
        for key, label in entries:
            label_keys[label] = [key]
            label_keys[wording.get(label, label)] = [key]
            options.append({
                "key": key,
                "displayKey": option_key(len(options)),
                "label": wording.get(label, label),
                "category": category,
            })
    label_keys.update({"辅酶 A": ["L"], "ACP": ["AR"], "NAD / NADP": ["S", "AF"]})
    original = {option["key"]: option["label"] for option in group["options"]}
    unknown = set(original.values()) - label_keys.keys()
    if unknown:
        raise ValueError(f"Unreviewed cofactor options: {sorted(unknown)}")
    stems = []
    for stem in group["stems"]:
        answers = list(dict.fromkeys(
            key for old_key in stem["answer"] for key in label_keys[original[old_key]]
        ))
        stems.append({**stem, "answer": answers, "answerRaw": "、".join(answers)})
    return {**group, "options": options, "stems": stems,
            "stackedOptionCategories": True, "optionShuffleVersion": 3}


def evidence():
    return {
        "lectureId": "lecture-13",
        "lectureNumber": LECTURE_NUMBER,
        "lectureTitle": TITLE,
        "page": "思维导图",
        "image": "biochemistry/lecture-pages/lecture-13-mind-map.webp",
        "title": f"第 13 讲《{TITLE}》· 思维导图",
        "description": "已按维生素讲义、真题要点与辅因子表逐项核对；点击可放大查看思维导图。",
        "method": "按 2027 考研生化第 13 讲维生素思维导图及配套选择题逐项复核。",
    }


def make_group(source_group, display_index):
    original = dict(source_group["options"])
    labels = list(original.values())
    shuffled = list(labels)
    random.Random(30600 + LECTURE_NUMBER * 100 + source_group["source_index"]).shuffle(shuffled)
    if shuffled == labels:
        shuffled = shuffled[1:] + shuffled[:1]
    output_keys = {label: option_key(position) for position, label in enumerate(shuffled)}
    stems = []
    for number, text in source_group["stems"]:
        if source_group["source_index"] == 1 and number == 3:
            answer_labels = ["VitA", "VitD", "VitE", "VitK"]
        elif source_group["source_index"] == 1 and number == 4:
            # The fat-soluble vitamins share both nuclear-receptor ligand
            # activity and slow excretion/accumulation in this lecture's scope.
            answer_labels = ["代谢产物可与核受体结合", "排泄少、易蓄积"]
        else:
            answer_labels = [original[key] for key in source_group["answers"][number]]
        answers = [output_keys[label] for label in answer_labels]
        stems.append({
            "number": number,
            "text": text.replace("（多选）", "").rstrip(),
            "answerRaw": "、".join(answers),
            "answer": answers,
            "answerMode": "多选" if len(answers) > 1 else "单选",
        })
    return {
        "id": f"bio-13-{display_index:02d}",
        "page": display_index,
        "title": source_group["title"],
        "kind": "B",
        "kindLabel": "B型题",
        "options": [{"key": option_key(position), "label": label} for position, label in enumerate(shuffled)],
        "stems": stems,
        "sourceText": source_group["title"],
        "reviewState": "已按维生素讲义、真题要点与思维导图核对",
        "reviewIssues": [],
        "reviewNotes": [],
        "topic": TOPIC,
        "lectureIds": ["lecture-13"],
        "optionShuffleVersion": 1,
        "lectureEvidence": evidence(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-cofactor-group", action="store_true",
                        help="Update only group 3 from the checked-in data; keep other groups untouched")
    args = parser.parse_args()
    if args.refresh_cofactor_group:
        payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
        matches = [group for group in payload["groups"] if group["id"] == "bio-13-03"]
        if len(matches) != 1:
            raise ValueError("Expected exactly one vitamin cofactor group")
        payload["groups"] = [organize_cofactor_options(group) if group["id"] == "bio-13-03" else group
                             for group in payload["groups"]]
        OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    source_groups = parse_workbook()
    source_groups = [
        *source_groups[:2],
        merge_cofactor_groups(source_groups[2], source_groups[3]),
        *source_groups[4:],
    ]
    groups = [make_group(group, index) for index, group in enumerate(source_groups, 1)]
    groups[2] = organize_cofactor_options(groups[2])
    payload = {
        "meta": {
            "title": "生物化学第 13 讲题库",
            "sourceLabel": "生化第 13 讲学成选择题（维生素）",
            "sourcePages": 1,
            "lectureCount": 1,
            "groupCount": len(groups),
            "stemCount": sum(len(group["stems"]) for group in groups),
            "correctionGroupCount": 0,
            "generatedBy": "scripts/build_biochemistry_lecture13.py",
            "siteIntegrated": True,
            "lectureLinked": True,
            "answerNote": "仅收录第 13 讲《维生素》范围内题目；每组选项均已打散，答案按讲义、真题与辅因子表复核。",
        },
        "topics": ["全部", TOPIC, "综合"],
        "pages": [{"page": group["page"], "image": "", "topic": TOPIC, "searchText": group["title"]} for group in groups],
        "groups": groups,
        "lectures": [{"id": "lecture-13", "number": LECTURE_NUMBER, "title": TITLE, "pageCount": 2}],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
