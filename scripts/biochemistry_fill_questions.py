#!/usr/bin/env python3
"""Shared DOCX fill-in importer for the biochemistry lecture builders."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document


QUESTION_RE = re.compile(r"^F(\d+)\.\s*(.+)$")
ANSWER_RE = re.compile(r"F(\d+)\.\s*(.*?)(?=\s+F\d+\.|$)")


def parse_fill_questions(source: Path):
    document = Document(source)
    questions = {}
    answers = {}
    mode = ""

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if text.startswith("填空题答案"):
            mode = "answers"
            continue
        if text.startswith("填空题"):
            mode = "questions"
            continue
        if text == "答案":
            mode = ""
            continue

        if mode == "questions":
            match = QUESTION_RE.match(text)
            if match:
                questions[int(match.group(1))] = match.group(2).strip()
        elif mode == "answers":
            for number, answer_text in ANSWER_RE.findall(text):
                answers[int(number)] = [item.strip() for item in answer_text.strip().split("；")]

    if not questions:
        raise ValueError(f"No fill-in questions found in {source}")
    if set(questions) != set(answers):
        raise ValueError(
            f"Fill-in question and answer keys differ: questions={sorted(questions)}, answers={sorted(answers)}"
        )

    parsed = []
    for number in sorted(questions):
        text = questions[number]
        answer = answers[number]
        blank_count = text.count("______")
        if blank_count != len(answer):
            raise ValueError(
                f"F{number}: found {blank_count} blanks but {len(answer)} answers: {answer}"
            )
        parsed.append({
            "number": number,
            "text": text,
            "answerRaw": "；".join(answer),
            "answerDisplay": "；".join(answer),
            "answer": answer,
            "answerMode": "填空",
        })
    return parsed


def make_fill_groups(
    questions,
    *,
    lecture_number: int,
    topic: str,
    lecture_id: str,
    start_page: int,
    ranges,
    evidence_for_page,
    review_state: str,
):
    """Build compact fill-in groups from explicit inclusive F-number ranges."""
    by_number = {question["number"]: question for question in questions}
    groups = []
    used = set()
    for offset, (first, last, evidence_page) in enumerate(ranges):
        stems = [by_number[number] for number in range(first, last + 1)]
        if len(stems) != last - first + 1:
            raise ValueError(f"Missing fill-in question in F{first}–F{last}")
        used.update(range(first, last + 1))
        page = start_page + offset
        groups.append({
            "id": f"bio-{lecture_number:02d}-fill-{offset + 1:02d}",
            "page": page,
            "title": f"填空题 F{first}–F{last}",
            "kind": "F",
            "kindLabel": "填空题",
            "options": [],
            "stems": stems,
            "sourceText": f"填空题 F{first}–F{last}",
            "reviewState": review_state,
            "reviewIssues": [],
            "reviewNotes": [],
            "topic": topic,
            "lectureIds": [lecture_id],
            "optionShuffleVersion": 0,
            "lectureEvidence": evidence_for_page(evidence_page),
        })
    if used != set(by_number):
        raise ValueError(f"Fill-in ranges do not cover all questions: missing {sorted(set(by_number) - used)}")
    return groups
