#!/usr/bin/env python3
"""Import the teacher's pathology and medicine supplements without PDF images.

Pathology pages 35-54 contain 90 questions and answer keys. Medicine pages
55-72 contain 92 questions but no answer key in the supplied PDF. The latter
remain available for practice and are deliberately not auto-graded.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber
from repair_med_pneumonia_case import repair_pneumonia_case


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = "西综课后巩固（教师补充）.pdf"
PATHOLOGY_OUTPUT = ROOT / "src/data/pathology-teacher-supplement.json"
MED_OUTPUT = ROOT / "src/data/med-teacher-supplement.json"
REPORT = ROOT / "reports/teacher-pathology-med-supplement-2026-09-14.md"

PATHOLOGY_PAGES = {section: (35 + (section - 1) * 2, 36 + (section - 1) * 2) for section in range(1, 8)}
MED_PAGES = {1: (55, 57), 2: (58, 61), 3: (62, 65), 4: (66, 67), 5: (68, 69), 6: (70, 72)}
PATHOLOGY_SECTION_NAMES = {
    1: "消化系统疾病", 2: "循环系统疾病", 3: "呼吸系统疾病",
    4: "内分泌系统疾病、免疫性疾病", 5: "生殖系统疾病、乳腺疾病",
    6: "传染病、损伤的修复", 7: "适应和损伤",
    8: "局部血液循环障碍、炎症", 9: "肿瘤",
}

# Individual question mapping, not a whole-handout-section shortcut.
PATHOLOGY_LECTURES = {
    1: [1, 1, 2, 3, 5, 5, 5, 5, 4, 4],
    2: [9, 9, 10, 8, 7, 7, 10, 10, 6, 6],
    3: [12, 11, 13, 11, 14, 14, 15, 15, 15, 13],
    4: [16, 16, 16, 16, 17, 17, 17, 17, 17, 17],
    5: [18, 18, 18, 18, 18, 18, 18, 18, 19, 19],
    6: [20, 20, 21, 21, 21, 21, 21, 22, 22, 22],
    7: [23] * 10,
    8: [24] * 6 + [25] * 4,
    9: [26] * 10,
}

MED_LECTURES = {
    1: [1, 11, 11, 13, 1, 9, 9, 9, 5, 3, 4, 4, 4, 4, 4, 4],
    2: [7, 7, 7, 7, 8, 12, 13, 11, 55, 55, 55, 56, 56, 56, 56, 56, 56, 55, 52],
    3: [54, 54, 54, 53, 54, 53, 49, 49, 49, 49, 49, 50, 50, 50, 50, 50, 51, 51],
    4: [14, 14, 14, 15, 15, 15, 16, 16, 16, 17, 18, 19],
    5: [22, 22, 23, 23, 25, 26, 26, 26, 26, 26, 26, 27],
    6: [28, 29, 29, 29, None, 30, 30, 30, 31, 31, 34, 34, 32, 32, 32],
}

SCANNED_PATHOLOGY = {
    8: """1.【多选题】慢性肝淤血的病理变化有
A 槟榔肝
B 小叶中央见明显脂肪变性的肝细胞
C 严重时网状纤维可塌陷
D Disse间隙的肝星状细胞增生
2.【多选题】以下属于混合血栓的有
A 静脉延续性血栓的体部
B 冠状动脉粥样硬化溃疡处
C 二尖瓣狭窄的左心房内
D 弥散性血管内凝血的微循环
3.【多选题】脂肪栓塞的原因有
A 长骨骨折
B 糖尿病
C 慢性胰腺炎
D 酗酒
4.【单选题】羊水栓塞引起猝死的主要机制不包括
A 过敏性休克
B 羊水栓子阻塞肺静脉
C 反射性血管痉挛
D 引起DIC
5.【多选题】分娩时，由于子宫强烈收缩，可引起
A 血栓栓塞
B 细胞栓塞
C 羊水栓塞
D 空气栓塞
6.【多选题】肺出血性梗死的病理变化有
A 肺下叶、肋膈缘多见
B 病灶呈楔形，尖端朝向肺门
C 梗死灶呈凝固性坏死，可见肺泡轮廓
D 梗死灶呈暗红色，之后变成灰白色
7.【单选题】炎症过程中介导白细胞滚动的主要是
A 选择素
B CD31
C 整合素
D 细菌产物
8.【单选题】中性粒细胞最有效的杀菌系统是
A H₂O₂-MPO-卤素
B 超氧阴离子-H₂O₂-羟自由基
C 乳铁蛋白-溶菌酶-弹性蛋白酶
D 酸性环境-防御素-一氧化氮
9.【多选题】由细胞释放，主要引起疼痛的炎症介质有
A 前列腺素
B 缓激肽
C P物质
D 组胺
10.【多选题】巨噬细胞在炎症中的主要功能有
A 有吞噬作用，参与微生物和坏死组织的清除
B 为B细胞提呈抗原，参与免疫反应
C 分泌细胞因子，参与炎症的蔓延和终止
D 启动组织修复，参与瘢痕形成""",
    9: """1.（多选）恶性肿瘤生长迅速的主要原因有
A.倍增时间短
B.生长分数高
C.异型性显著
D.生成与死亡比例高
2.（多选）以下属于神经外胚叶恶性肿瘤的是
A.纤维肉瘤
B.黑色素瘤
C.视网膜母细胞瘤
D.胚胎性横纹肌肉瘤
3.（多选）与原癌基因KIT相关的人类肿瘤有
A.急性髓系白血病
B.精原细胞瘤
C.胃癌
D.霍奇金淋巴瘤
4.（单选）调节低氧诱导因子的肿瘤抑制基因是
A.VHL
B.APC
C.BRCA1
D.MSH
5.（多选）参与恶性肿瘤侵袭和转移的机制有
A.癌细胞表面的黏附分子增多
B.癌细胞表达更多的层粘连蛋白受体
C.癌细胞诱导间质产生基质金属蛋白酶
D.癌细胞作阿米巴样运动穿过基底膜
6.（单选）与肺癌相关的间接化学致癌物是
A.芳香胺类
B.亚硝胺类
C.多环芳烃
D.黄曲霉素
7.（多选）以下属于真性肿瘤的有
A.葡萄胎
B.蕈样肉芽肿病
C.动脉瘤
D.创伤性神经瘤
8.（单选）恶性程度最高的体表肿瘤是
A.黑色素瘤
B.纤维肉瘤
C.基底细胞癌
D.皮肤鳞状细胞癌
9.（单选）肿瘤免疫组织化学标记CD31、CD34阳性，提示其最可能的来源是
A.B淋巴细胞
B.T淋巴细胞
C.内皮细胞
D.肌细胞
10.（单选）与着色性干皮病患者发生皮肤癌最相关的机制是
A.遗传性ATM基因受累
B.端粒酶活性增高
C.BCL-2过度表达
D.DNA修复基因异常""",
}
SCANNED_ANSWERS = {8: "ACD ABC ABCD B ABCD ABCD A A AC ACD".split(), 9: "BD BC AB A BCD C AB A C D".split()}

QUESTION_RE = re.compile(r"^(\d{1,2})\.\s*(?!\d)(.*)$")
OPTION_RE = re.compile(r"^([A-D])(?:[.．]\s*|\s+)(.+)$")
SHARED_RE = re.compile(r"^\((\d+)-(\d+)题共用题干\)(.*)$")


def clean(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u200b", "").replace("\u2060", "").replace("\x01", " ")
    value = value.replace("‑", "-").replace("−", "-")
    value = value.translate(str.maketrans("⻝⻓⻅⻔⻛⻆⻘⻣⻩", "食长见门风角青骨黄"))
    value = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", value)
    value = re.sub(r"\b(PaO2|PaCO2)(\d{2,3})(?=mmHg\b)", r"\1 \2", value)
    return re.sub(r"\s+", " ", value).strip()


def lines(text: str) -> list[str]:
    return [item for raw in text.splitlines() if (item := clean(raw))]


def is_noise(line: str) -> bool:
    return bool(re.search(r"课后巩固|更多资料分享|更多实用资料分享|交流群|文档部分内容可能由|每题2分|^病理肿瘤$", line))


def parse_questions(entries: list[tuple[int, str]], expected_count: int, shared_context: bool = False) -> list[dict]:
    questions: list[dict] = []
    current = None
    active_option = None
    pending_context = None
    active_context = None
    in_answers = False
    for page, text in entries:
        for line in lines(text):
            if line.startswith("参考答案"):
                in_answers = True
                continue
            if in_answers or is_noise(line):
                continue
            shared = SHARED_RE.match(line) if shared_context else None
            if shared:
                pending_context = {"start": int(shared.group(1)), "end": int(shared.group(2)), "text": shared.group(3)}
                active_option = None
                continue
            match = QUESTION_RE.match(line)
            if match and int(match.group(1)) == len(questions) + 1:
                number = int(match.group(1))
                if pending_context and number == pending_context["start"]:
                    active_context = pending_context
                    pending_context = None
                context = active_context["text"] if active_context and number <= active_context["end"] else ""
                current = {"number": number, "page": page, "text": match.group(2), "options": [], "context": context}
                questions.append(current)
                active_option = None
                if active_context and number == active_context["end"]:
                    active_context = None
                continue
            if pending_context is not None:
                pending_context["text"] += " " + line
                continue
            option = OPTION_RE.match(line)
            if option and current and len(current["options"]) < 4 and option.group(1) == "ABCD"[len(current["options"])]:
                current["options"].append({"key": option.group(1), "label": option.group(2)})
                active_option = current["options"][-1]
            elif current and active_option:
                active_option["label"] += " " + line
            elif current:
                current["text"] += " " + line
    assert len(questions) == expected_count, (len(questions), expected_count, [(q["number"], q["page"]) for q in questions])
    for question in questions:
        assert len(question["options"]) == 4, (question["number"], question["page"], question["options"])
    return questions


def parse_pathology_answers(text: str) -> list[str]:
    output = []
    reading = False
    for line in lines(text):
        if line.startswith("参考答案"):
            reading = True
            continue
        if not reading:
            continue
        match = re.match(r"^(\d{1,2})\.\s*([ABCD]+)$", line)
        if match and int(match.group(1)) == len(output) + 1:
            output.append(match.group(2))
    assert len(output) == 10, output
    return output


def pathology_topic(lecture: int) -> str:
    ranges = [(1, 5, "消化系统"), (6, 10, "心血管系统"), (11, 15, "呼吸系统"),
              (16, 16, "内分泌系统"), (17, 17, "免疫性疾病"), (18, 18, "生殖系统"),
              (19, 19, "乳腺疾病"), (20, 21, "传染病"), (22, 22, "损伤与修复"),
              (23, 23, "损伤与修复"), (24, 24, "局部血液循环障碍"),
              (25, 25, "炎症"), (26, 26, "肿瘤")]
    return next(topic for low, high, topic in ranges if low <= lecture <= high)


def med_topic(lecture: int | None) -> str:
    if lecture is None:
        return "血液"
    for low, high, topic in [(1, 13, "呼吸"), (14, 23, "消化"), (24, 27, "肾脏"),
                             (28, 35, "血液"), (36, 42, "内分泌"), (43, 47, "风湿"),
                             (48, 48, "中毒"), (49, 57, "循环")]:
        if low <= lecture <= high:
            return topic
    raise ValueError(lecture)


def label_mode(question: dict) -> str:
    return "多选" if "多选" in question["text"] else "单选"


def title_for_question(question: dict) -> str:
    title = re.sub(r"[（(](?:单选题?|多选题?)[）)]", "", question["text"]).strip()
    return title if len(title) <= 42 else title[:41] + "…"


def pathology_groups(texts: dict[int, str]) -> list[dict]:
    groups = []
    for section in range(1, 10):
        if section <= 7:
            pages = PATHOLOGY_PAGES[section]
            questions = parse_questions([(page, texts[page]) for page in pages], 10)
            answers = parse_pathology_answers(texts[pages[1]])
        else:
            first_page = 49 if section == 8 else 52
            chunks = SCANNED_PATHOLOGY[section].split("\n")
            numbered = []
            current_page = first_page
            for line in chunks:
                number = QUESTION_RE.match(clean(line))
                if number and int(number.group(1)) == 7 and section == 8:
                    current_page = 50
                if number and int(number.group(1)) == 8 and section == 9:
                    current_page = 53
                numbered.append((current_page, line))
            questions = parse_questions(numbered, 10)
            answers = SCANNED_ANSWERS[section]
        for question in questions:
            number = question["number"]
            lecture = PATHOLOGY_LECTURES[section][number - 1]
            answer = answers[number - 1]
            source_mode = label_mode(question)
            mode = "多选" if len(answer) > 1 else "单选"
            group = {
                "id": f"path-teacher-{section:02d}-{number:02d}", "page": question["page"],
                "sourceKey": "teacher-2026-08", "sourceName": SOURCE_NAME,
                "sourceSection": PATHOLOGY_SECTION_NAMES[section], "sourceQuestion": number,
                "title": title_for_question(question), "kind": "A",
                "kindLabel": "多项选择" if mode == "多选" else "单项选择",
                "options": question["options"],
                "stems": [{"number": number, "text": question["text"], "answerRaw": answer,
                           "answer": list(answer), "answerMode": mode}],
                "sourceText": question["text"] + " " + " ".join(item["label"] for item in question["options"]),
                "topic": pathology_topic(lecture), "lectureIds": [f"lecture-{lecture:02d}"],
                "reviewState": "教师资料答案，未按讲义逐项复核",
                "answerSourceLabel": "教师资料答案", "supplement": True,
                "supplementNotice": "教师资料答案，尚未按讲义逐项复核",
            }
            if source_mode != mode:
                group["reviewIssues"] = [f"原题标为{source_mode}，参考答案为{answer}；暂不自动判分。"]
                group["stems"][0]["answerState"] = "待原题页核对"
            groups.append(group)
    return groups


def med_groups(texts: dict[int, str]) -> list[dict]:
    groups = []
    expected = {1: 16, 2: 19, 3: 18, 4: 12, 5: 12, 6: 15}
    for section, (first, last) in MED_PAGES.items():
        questions = parse_questions([(page, texts[page]) for page in range(first, last + 1)], expected[section], shared_context=True)
        assert len(MED_LECTURES[section]) == len(questions)
        question_index = 0
        while question_index < len(questions):
            question = questions[question_index]
            context = clean(question["context"])
            block = [question]
            if context:
                next_index = question_index + 1
                while next_index < len(questions):
                    candidate = questions[next_index]
                    if clean(candidate["context"]) != context or candidate["number"] != block[-1]["number"] + 1:
                        break
                    block.append(candidate)
                    next_index += 1
            question_index += len(block)

            if len(block) > 1:
                start_number = block[0]["number"]
                end_number = block[-1]["number"]
                lectures = [MED_LECTURES[section][item["number"] - 1] for item in block]
                topics = {med_topic(lecture) for lecture in lectures}
                assert len(topics) == 1, (section, start_number, end_number, topics)
                options = []
                stems = []
                for item, lecture in zip(block, lectures):
                    number = item["number"]
                    mode = label_mode(item)
                    category = f"第 {number} 题选项"
                    item_options = [{
                        "key": f"q{number}-{option['key']}",
                        "displayKey": option["key"],
                        "label": option["label"],
                        "category": category,
                    } for option in item["options"]]
                    options.extend(item_options)
                    stems.append({
                        "number": number,
                        "text": item["text"],
                        "answerRaw": "",
                        "answer": [],
                        "answerMode": mode,
                        "answerState": "暂无参考答案",
                        "optionCategory": category,
                        "sourceQuestion": number,
                        "lectureId": f"lecture-{lecture:02d}" if lecture else None,
                    })
                lecture_ids = list(dict.fromkeys(stem["lectureId"] for stem in stems if stem["lectureId"]))
                groups.append({
                    "id": f"med-teacher-{section:02d}-{start_number:02d}-{end_number:02d}",
                    "page": block[0]["page"],
                    "sourceKey": "teacher-2026-08",
                    "sourceName": SOURCE_NAME,
                    "sourceSection": f"内科含诊断·第 {section} 组",
                    "sourceQuestion": f"{start_number}–{end_number}",
                    "title": f"第 {start_number}–{end_number} 题共用题干",
                    "kind": "A",
                    "kindLabel": "单项选择",
                    "sharedStem": context,
                    "sharedQuestionCount": len(stems),
                    "options": options,
                    "stems": stems,
                    "sourceText": " ".join([context, *(item["text"] for item in block), *(option["label"] for option in options)]),
                    "topic": next(iter(topics)),
                    "lectureIds": lecture_ids,
                    "reviewState": "原PDF未附内科参考答案，暂不判分",
                    "supplement": True,
                    "supplementNotice": "原PDF未附参考答案，暂不自动判分",
                })
                continue

            number = question["number"]
            lecture = MED_LECTURES[section][number - 1]
            mode = label_mode(question)
            prompt = question["text"]
            group = {
                "id": f"med-teacher-{section:02d}-{number:02d}", "page": question["page"],
                "sourceKey": "teacher-2026-08", "sourceName": SOURCE_NAME,
                "sourceSection": f"内科含诊断·第 {section} 组", "sourceQuestion": number,
                "title": title_for_question(question), "kind": "A",
                "kindLabel": "多项选择" if mode == "多选" else "单项选择",
                "options": question["options"],
                "stems": [{"number": number, "text": prompt, "answerRaw": "", "answer": [],
                           "answerMode": mode, "answerState": "暂无参考答案", "sourceQuestion": number,
                           "lectureId": f"lecture-{lecture:02d}" if lecture else None}],
                "sourceText": prompt + " " + " ".join(item["label"] for item in question["options"]),
                "topic": med_topic(lecture), "lectureIds": [f"lecture-{lecture:02d}"] if lecture else [],
                "reviewState": "原PDF未附内科参考答案，暂不判分",
                "supplement": True, "supplementNotice": "原PDF未附参考答案，暂不自动判分",
            }
            if lecture is None:
                group["reviewIssues"] = ["现有内科讲义目录无骨髓纤维化专章，暂放入血液的未关联讲义。"]
            groups.append(group)
    return groups


def order_by_lecture(groups: list[dict], lecture_count: int) -> list[dict]:
    def first_lecture(group: dict) -> int:
        return min((int(lecture_id[-2:]) for lecture_id in group["lectureIds"]), default=lecture_count + 1)

    return sorted(groups, key=first_lecture)


def save(output: Path, groups: list[dict], subject: str, source_pages: tuple[int, int]) -> None:
    if subject == "内科":
        repair_pneumonia_case({'groups': groups, 'meta': {}})
    output.write_text(json.dumps({
        "meta": {"title": f"教师课后巩固·{subject}补充", "sourcePageRange": list(source_pages),
                 "groupCount": len(groups), "stemCount": sum(len(group["stems"]) for group in groups),
                 "answerNote": "答案按原PDF录入，未按讲义逐项复核" if subject == "病理" else "原PDF未附内科答案，暂不判分"},
        "pages": [], "groups": groups,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pdf", type=Path)
    args = parser.parse_args()
    with pdfplumber.open(args.source_pdf) as document:
        texts = {page: document.pages[page - 1].extract_text() or "" for page in list(range(35, 49)) + list(range(55, 73))}
    pathology = order_by_lecture(pathology_groups(texts), 26)
    med = order_by_lecture(med_groups(texts), 57)
    assert len(pathology) == 90 and sum(len(group["stems"]) for group in med) == 92
    assert len({group["id"] for group in pathology}) == 90
    assert len({group["id"] for group in med}) == len(med)
    save(PATHOLOGY_OUTPUT, pathology, "病理", (35, 54))
    save(MED_OUTPUT, med, "内科", (55, 72))
    report = ["# 教师课后巩固：病理与内科补充题归类", "", "原PDF第35–54页病理90题（其中扫描页20题），第55–72页内科92题。仅将题目文本、来源页码、章节与题号纳入网站；不纳入原PDF图片。内科共用题干的连续小题已合并到同一题组页面。", "", "病理答案取自原PDF，尚未按讲义逐项复核。内科部分在所给PDF中没有答案页，全部暂不自动判分。", ""]
    for subject, groups in [("病理", pathology), ("内科", med)]:
        report += [f"## {subject}归类", "", "| 站内章节 | 题数 |", "| --- | ---: |"]
        topic_counts = Counter()
        for group in groups:
            topic_counts[group["topic"]] += len(group["stems"])
        for topic, count in topic_counts.items():
            report.append(f"| {topic} | {count} |")
        report += ["", "| 对应讲义 | 题数 | 原PDF节号·题号 |", "| --- | ---: | --- |"]
        for lecture in sorted({lecture for group in groups for lecture in group["lectureIds"]}):
            matched = []
            for group in groups:
                for stem in group["stems"]:
                    stem_lecture = stem.get("lectureId") or (group["lectureIds"][0] if len(group["lectureIds"]) == 1 else None)
                    if stem_lecture == lecture:
                        matched.append((group, stem))
            refs = "、".join(f"{group['sourceSection']}·{stem.get('sourceQuestion', group['sourceQuestion'])}" for group, stem in matched)
            report.append(f"| 第 {int(lecture[-2:])} 讲 | {len(matched)} | {refs} |")
        if subject == "内科":
            report += ["", "骨髓纤维化题（内科含诊断6·5）在现有讲义目录中无对应专章，归入血液的“未关联讲义”。"]
        report += [""]
    issues = [group for group in pathology if group.get("reviewIssues")]
    report += ["## 待复核", ""]
    if issues:
        report.extend(f"- 病理PDF第{group['page']}页，{group['sourceSection']}·{group['sourceQuestion']}：{'；'.join(group['reviewIssues'])}" for group in issues)
    else:
        report.append("病理题型与参考答案的选项数量没有冲突；但资料注明部分内容可能由AI生成，仍需逐题核对知识结论。")
    report.append("- 内科92题均缺原资料答案，暂不判分。")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print({"pathology": len(pathology), "med_groups": len(med), "med_stems": sum(len(group["stems"]) for group in med), "shared_med_groups": sum(bool(group.get("sharedStem")) for group in med), "pathology_issues": len(issues), "med_unscored": sum(not stem["answer"] for group in med for stem in group["stems"])})


if __name__ == "__main__":
    main()
