#!/usr/bin/env python3
"""Import the reviewed fracture overview question bank from its Word source."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "surgery/source-documents/骨折概论_学成选择题_题目与答案.docx"
DEFAULT_OUTPUT = ROOT / "src/data/surgery-fracture-data.json"
PUBLIC_DOCUMENT = "surgery/source-documents/骨折概论_学成选择题_题目与答案.docx"

GROUP_IDS = {
    "第一组\u3000原因": "fracture-g01",
    "第二组\u3000分类": "fracture-g02",
    "第三组\u3000开放性骨折": "fracture-g03",
    "第四组\u3000骨折特有体征": "fracture-g04",
    "第五组\u3000临床愈合标准": "fracture-g05",
    "第六组\u3000骨折愈合过程": "fracture-g06",
    "第七组\u3000影响愈合的因素": "fracture-g07",
    "第八组A\u3000骨折并发症的分类": "fracture-g08a",
    "第八组B\u3000早期并发症": "fracture-g08b",
    "第八组C\u3000晚期并发症": "fracture-g08c",
    "第九组\u3000复位标准": "fracture-g09",
    "第十组\u3000复位方式": "fracture-g10",
    "第十一组\u3000固定与功能锻炼": "fracture-g11",
}

SOURCE_PAGES = {
    "fracture-g01": 1,
    "fracture-g02": 1,
    "fracture-g03": 1,
    "fracture-g04": 2,
    "fracture-g05": 2,
    "fracture-g06": 2,
    "fracture-g07": 3,
    "fracture-g08a": 3,
    "fracture-g08b": 4,
    "fracture-g08c": 4,
    "fracture-g09": 4,
    "fracture-g10": 5,
    "fracture-g11": 5,
}

LECTURE_PAGES = {
    "fracture-g01": 1,
    "fracture-g02": 1,
    "fracture-g03": 2,
    "fracture-g04": 2,
    "fracture-g05": 2,
    "fracture-g06": 2,
    "fracture-g07": 2,
    "fracture-g08a": 3,
    "fracture-g08b": 3,
    "fracture-g08c": 3,
    "fracture-g09": 3,
    "fracture-g10": 4,
    "fracture-g11": 4,
}


def clean(value: str) -> str:
    value = value.replace("\u3000", " ").replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def blocks(document: Document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield "paragraph", Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield "table", Table(child, document)


def parse_answer_table(table: Table) -> dict[int, list[str]]:
    answers: dict[int, list[str]] = {}
    for row in table.rows:
        cells = [clean(cell.text) for cell in row.cells]
        for offset in (0, 2):
            if offset + 1 >= len(cells):
                continue
            number = re.search(r"\d+", cells[offset])
            if not number:
                continue
            answers[int(number.group())] = re.findall(r"[A-Z]", cells[offset + 1])
    return answers


def split_document(document: Document):
    items = list(blocks(document))
    answer_start = next(
        index
        for index, (kind, item) in enumerate(items)
        if kind == "paragraph" and clean(item.text) == "答案"
    )

    questions: dict[str, dict] = {}
    current_title: str | None = None
    reading_stems = False
    for kind, item in items[:answer_start]:
        if kind == "paragraph":
            text = clean(item.text)
            raw_title = item.text.strip()
            if raw_title in GROUP_IDS:
                current_title = raw_title
                questions[current_title] = {"options": [], "stems": []}
                reading_stems = False
            elif current_title and text == "题目":
                reading_stems = True
            elif current_title and reading_stems and re.match(r"^\d+\.", text):
                stem = re.sub(r"^\d+\.\s*", "", text)
                if current_title in {"第一组\u3000原因", "第二组\u3000分类"}:
                    stem = re.sub(r"\s*[A-Z]{1,15}$", "", stem).strip()
                questions[current_title]["stems"].append(stem)
        elif current_title and not reading_stems:
            rows = [[clean(cell.text) for cell in row.cells] for row in item.rows]
            if rows and rows[0][:2] == ["选项", "内容"]:
                questions[current_title]["options"] = [row[:2] for row in rows[1:] if row[0]]

    answers: dict[str, dict[int, list[str]]] = {}
    current_title = None
    for kind, item in items[answer_start + 1 :]:
        if kind == "paragraph" and item.text.strip() in GROUP_IDS:
            current_title = item.text.strip()
        elif kind == "table" and current_title:
            answers[current_title] = parse_answer_table(item)
            current_title = None

    # The Word answer table numbers the second item in group 4 as item 3.
    fourth = "第四组\u3000骨折特有体征"
    if 3 in answers[fourth] and 2 not in answers[fourth]:
        answers[fourth][2] = answers[fourth].pop(3)

    # The Word question section omits group 5; restore it from lecture page 2.
    fifth = "第五组\u3000临床愈合标准"
    questions[fifth] = {
        "options": [
            ["A", "局部无异常活动"],
            ["B", "局部无压痛"],
            ["C", "无纵向叩击痛"],
            ["D", "X线见骨折处有连续性梭形骨痂（骨折线模糊）"],
        ],
        "stems": ["临床愈合标准"],
    }
    return questions, answers


def make_group(raw_title: str, question: dict, answers: dict[int, list[str]]) -> dict:
    group_id = GROUP_IDS[raw_title]
    title = clean(re.sub(r"^第[^ ]+组(?:[ABC])?[\u3000 ]*", "", raw_title))
    options = [
        {"key": key, "label": label, "sourceText": f"{key}. {label}", "ocrScore": 1.0}
        for key, label in question["options"]
    ]
    stems = []
    for number, text in enumerate(question["stems"], 1):
        answer = answers[number]
        stems.append(
            {
                "text": text,
                "answer": answer,
                "answerMode": "多选" if len(answer) > 1 else "单选",
                "sourceText": text,
                "ocrScore": 1.0,
                "reviewMethod": "Word题目答案表与讲义逐项复核",
            }
        )

    review_notes = []
    if group_id == "fracture-g04":
        review_notes.append(
            {
                "title": "答案编号勘误",
                "body": "Word答案表将“可不出现特有体征”误标为第3题；题目区实际只有2题，已按讲义第2页校正为第2题，答案为E、F、G、H。",
            }
        )
    if group_id == "fracture-g05":
        review_notes.append(
            {
                "title": "补回Word漏组",
                "body": "Word答案区含第五组，但题目区整组缺失。已依据讲义第2页“临床愈合标准”补回题干与4个选项，答案为A、B、C、D。",
            }
        )

    lecture_page = LECTURE_PAGES[group_id]
    return {
        "id": group_id,
        "page": SOURCE_PAGES[group_id],
        "sourcePage": SOURCE_PAGES[group_id],
        "sourceName": "骨折概论_学成选择题_题目与答案.docx",
        "sourceDocument": PUBLIC_DOCUMENT,
        "title": title,
        "kind": "B",
        "kindLabel": "B型题",
        "options": options,
        "stems": stems,
        "sourceText": "；".join([item[1] for item in question["options"]] + question["stems"]),
        "reviewState": "已按Word题目答案表与讲义人工复核",
        "reviewIssues": [],
        "reviewNotes": review_notes,
        "topic": "骨折概论",
        "lectureIds": ["lecture-29"],
        "lectureEvidence": {
            "lectureId": "lecture-29",
            "page": lecture_page,
            "image": f"surgery/lecture-pages/lecture-29-page-{lecture_page:02d}.png",
            "title": f"第29讲第{lecture_page}页 · 骨折概论",
            "description": "本题组已按《核心精讲·骨折概论》对应页逐项复核。",
        },
    }


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    document = Document(source)
    questions, answers = split_document(document)

    ordered_titles = list(GROUP_IDS)
    groups = [make_group(title, questions[title], answers[title]) for title in ordered_titles]
    payload = {
        "meta": {
            "title": "骨折概论学成选择题",
            "sourceDocument": source.name,
            "sourcePages": 7,
            "lectureId": "lecture-29",
            "lecturePagesReviewed": [1, 2, 3, 4],
            "generatedBy": "scripts/import_fracture_docx.py",
            "answerNote": "题干、选项与答案表逐项提取，并按骨折概论讲义第1-4页复核；第四组编号错误及第五组漏题已校正。",
        },
        "groups": groups,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        {
            "groups": len(groups),
            "stems": sum(len(group["stems"]) for group in groups),
            "options": sum(len(group["options"]) for group in groups),
            "output": str(output),
        }
    )


if __name__ == "__main__":
    main()
