#!/usr/bin/env python3
"""Build the checked biochemistry lecture 04 payload (plasma lipoproteins)."""

from __future__ import annotations

import json
import random
from pathlib import Path


TITLE = "生化 血浆脂蛋白"
TOPIC = "脂代谢"


def bank(index, title, options, stems, lecture_page):
    shuffled = list(options)
    random.Random(30604 + index).shuffle(shuffled)
    if shuffled == options:
        shuffled = shuffled[1:] + shuffled[:1]
    keys = {label: chr(65 + position) for position, label in enumerate(shuffled)}
    return {
        "id": f"bio-04-{index:02d}", "page": index, "title": title, "kind": "B", "kindLabel": "B型题",
        "options": [{"key": chr(65 + position), "label": label} for position, label in enumerate(shuffled)],
        "stems": [{"number": number, "text": text, "answerRaw": "、".join(keys[item] for item in answer), "answer": [keys[item] for item in answer], "answerMode": "多选" if len(answer) > 1 else "单选"} for number, (text, answer) in enumerate(stems, 1)],
        "sourceText": title, "reviewState": "已按 2027 考研讲义核对", "reviewIssues": [], "reviewNotes": [], "topic": TOPIC,
        "lectureIds": ["lecture-04"], "optionShuffleVersion": 1,
        "lectureEvidence": evidence(lecture_page),
    }


def evidence(page):
    return {
        "lectureId": "lecture-04", "lectureNumber": 4, "lectureTitle": TITLE, "page": page,
        "image": f"biochemistry/lecture-pages/lecture-04-page-{page:02d}.webp",
        "title": f"第 04 讲《{TITLE}》· 第 {page} 页", "description": "已按该讲义页逐项核对答案；点击可查看讲义原页。",
        "method": "按知识点人工映射至 2027 考研生化第 04 讲，并逐项复核。",
    }


def ranking_group():
    options = ["VLDL", "HDL", "LDL", "CM"]
    shuffled = list(options)
    random.Random(30642).shuffle(shuffled)
    keys = {label: chr(65 + position) for position, label in enumerate(shuffled)}
    rows = [
        ("按蛋白质含量由高到低排序", ["HDL", "LDL", "VLDL", "CM"]),
        ("按脂肪含量由高到低排序", ["CM", "VLDL", "LDL", "HDL"]),
        ("按胆固醇含量由高到低排序", ["LDL", "HDL", "VLDL", "CM"]),
    ]
    return {
        "id": "bio-04-02", "page": 2, "title": "四类血浆脂蛋白的成分排序", "kind": "RANK", "kindLabel": "排序题",
        "options": [{"key": chr(65 + position), "label": label} for position, label in enumerate(shuffled)],
        "stems": [{"number": number, "text": text, "answerRaw": "＞".join(keys[item] for item in answer), "answer": [keys[item] for item in answer], "answerMode": "排序", "answerDisplay": "＞".join(answer)} for number, (text, answer) in enumerate(rows, 1)],
        "sourceText": "四类脂蛋白的蛋白质、脂肪和胆固醇含量排序", "reviewState": "已按 2027 考研讲义核对", "reviewIssues": [], "reviewNotes": [], "topic": TOPIC,
        "lectureIds": ["lecture-04"], "optionShuffleVersion": 1, "lectureEvidence": evidence(2),
    }


def main():
    groups = [
        bank(1, "四类血浆脂蛋白的来源、转运与电泳", [
            "α", "减少可致脂肪肝", "减少可致高脂血症", "特征性载脂蛋白为 ApoB48", "增多可致高脂血症", "在血浆中合成", "将胆固醇逆向转运至肝内降解", "前β", "运输内源性胆固醇", "主要运输内源性脂肪", "由肝合成", "运输外源性脂肪和胆固醇", "由小肠合成", "β", "增多是高脂血症最重要的原因", "在血浆中由 VLDL→IDL→LDL 转变",
        ], [
            ("CM 的特点", ["特征性载脂蛋白为 ApoB48", "增多可致高脂血症", "运输外源性脂肪和胆固醇", "由小肠合成"]),
            ("VLDL 的特点", ["减少可致脂肪肝", "增多可致高脂血症", "前β", "主要运输内源性脂肪", "由肝合成"]),
            ("LDL 的特点", ["运输内源性胆固醇", "β", "增多是高脂血症最重要的原因", "在血浆中由 VLDL→IDL→LDL 转变"]),
            ("HDL 的特点", ["α", "减少可致高脂血症", "在血浆中合成", "将胆固醇逆向转运至肝内降解", "由肝合成", "由小肠合成"]),
        ], 1),
        ranking_group(),
        bank(3, "载脂蛋白与脂蛋白代谢酶", [
            "转运甘油三酯", "ApoCⅡ", "ApoB100", "ApoB48", "ApoE", "ApoAⅠ", "脂质交换的连接物", "调节酶活性", "脂蛋白脂肪酶（LPL）", "白蛋白", "卵磷脂胆固醇酰基转移酶（LCAT）", "受体识别",
        ], [
            ("载脂蛋白的功能", ["转运甘油三酯", "脂质交换的连接物", "调节酶活性", "受体识别"]),
            ("HDL 受体的配体", ["ApoAⅠ"]), ("LDL 受体的配体", ["ApoB100", "ApoE"]),
            ("LCAT 的激活剂", ["ApoAⅠ"]), ("LPL 的激活剂", ["ApoCⅡ"]),
            ("乳糜微粒的特征性载脂蛋白", ["ApoB48"]), ("血浆游离脂肪酸的主要载体", ["白蛋白"]),
            ("血浆中胆固醇酯化所需酶", ["卵磷脂胆固醇酰基转移酶（LCAT）"]),
        ], 2),
        bank(4, "脂蛋白的代谢去路", [
            "2/3", "清道夫受体", "LDL 受体", "脂蛋白脂肪酶（LPL）", "血管内皮细胞", "多种细胞", "1/3", "巨噬细胞", "胆固醇逆向转运", "主要在肝", 
        ], [
            ("HDL 的主要代谢作用", ["胆固醇逆向转运"]), ("VLDL 的主要水解酶", ["脂蛋白脂肪酶（LPL）"]),
            ("CM 的主要水解酶", ["脂蛋白脂肪酶（LPL）"]),
            ("LDL 经清道夫受体摄取的特点", ["清道夫受体", "血管内皮细胞", "1/3", "巨噬细胞"]),
            ("LDL 经 LDL 受体摄取的特点", ["2/3", "LDL 受体", "多种细胞", "主要在肝"]),
        ], 2),
        bank(5, "脂蛋白的作用与小肠脂质吸收", [
            "供能", "甘油一酯途径", "构成生物膜", "胆固醇", "甘油二酯", "外源性脂肪", "协助脂溶性维生素吸收", "维持体温", "参与细胞信号转导",
        ], [
            ("脂蛋白及脂类的生理作用", ["供能", "构成生物膜", "协助脂溶性维生素吸收", "维持体温", "参与细胞信号转导"]),
            ("可作为第二信使的脂质", ["甘油二酯"]), ("小肠吸收的外源性脂质原料", ["胆固醇", "外源性脂肪"]),
            ("小肠黏膜细胞合成外源性脂肪和胆固醇酯的途径", ["甘油一酯途径"]),
        ], 1),
    ]
    payload = {"meta": {"title": "生物化学第 04 讲题库", "sourceLabel": "生化第 04 讲学成选择题（血浆脂蛋白）", "sourcePages": 1, "lectureCount": 1, "groupCount": len(groups), "stemCount": sum(len(item["stems"]) for item in groups), "correctionGroupCount": 0, "generatedBy": "scripts/build_biochemistry_lecture4.py", "siteIntegrated": True, "lectureLinked": True, "answerNote": "仅收录第 04 讲《血浆脂蛋白》范围内题目；选项已逐组打散，答案已按讲义复核。"}, "topics": ["全部", TOPIC, "综合"], "pages": [{"page": item["page"], "image": "", "topic": TOPIC, "searchText": item["title"]} for item in groups], "groups": groups, "lectures": [{"id": "lecture-04", "number": 4, "title": TITLE, "pageCount": 4}]}
    Path("src/data/biochemistry-lecture4-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
