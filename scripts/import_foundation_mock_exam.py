#!/usr/bin/env python3
"""Import the 2027 foundation-stage diagnostic exam into the website bank."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

from build_mock_exam_error_book import ROWS, extract_exam
from review_foundation_jaundice import review_foundation_jaundice


ROOT = Path(__file__).resolve().parents[1]
KEY = "foundation-mock-exam-20260907"
SUBJECT_LABELS = {
    "physiology": "生理",
    "biochemistry": "生化",
    "pathology": "病理",
    "med": "内科",
    "surgery": "外科",
}
INDEX_SUBJECTS = {
    "physiology": "生理学",
    "biochemistry": "生物化学",
    "pathology": "病理学",
    "med": "内科",
    "surgery": "外科",
}


def answer_key() -> dict[int, str]:
    out: dict[int, str] = {}
    ranges = {
        (1, 5): "DCBAD", (6, 10): "BDDCA", (11, 15): "DDDAC", (16, 20): "DDBAD",
        (21, 25): "ADCBB", (26, 30): "BDBAC", (31, 35): "ABDBD", (36, 40): "CBCBD",
        (41, 45): "BAABA", (46, 50): "CACBD", (51, 55): "CCCCB", (56, 60): "CDADA",
        (61, 65): "BACCD", (66, 67): "AA", (68, 69): "BD", (70, 72): "ACD",
        (73, 75): "BCD", (76, 78): "CDC", (79, 81): "DDD", (82, 84): "DDB",
        (85, 87): "DAD", (88, 90): "AAD", (91, 92): "CB", (93, 94): "CC",
        (95, 97): "DCB", (98, 99): "AD", (100, 102): "CDC", (103, 105): "CDC",
        (106, 107): "DD", (108, 110): "CAD", (111, 115): "AABDB", (116, 117): "AB",
        (118, 119): "CB", (120, 121): "CB", (122, 123): "BD", (124, 125): "BA",
        (126, 127): "CD", (128, 129): "BD", (130, 131): "AD", (132, 133): "BD",
        (134, 135): "BA",
    }
    for (start, end), letters in ranges.items():
        assert len(letters) == end - start + 1
        for offset, letter in enumerate(letters):
            out[start + offset] = letter
    out.update({
        136: "ABD", 137: "ABC", 138: "BCD", 139: "ABCD", 140: "ABD", 141: "ABD",
        142: "ABD", 143: "ABC", 144: "ACD", 145: "ABD", 146: "ABC", 147: "ABC",
        148: "AD", 149: "ACD", 150: "ACD", 151: "ACD", 152: "ABD", 153: "ABD",
        154: "ACD", 155: "AC", 156: "ACD", 157: "ACD", 158: "BD", 159: "ABCD",
        160: "BC", 161: "ACD", 162: "ABCD", 163: "ABD", 164: "ACD", 165: "AC",
    })
    assert sorted(out) == list(range(1, 166))
    return out


B_PAIRS = {
    (116, 117): {
        "A": "电压门控 Na+ 通道开放，产生净 Na+ 流动",
        "B": "电压门控 Na+ 通道开放，不产生净 Na+ 流动",
        "C": "电压门控 K+ 通道开放，不产生净 K+ 流动",
        "D": "膜两侧 K+ 浓度梯度为 0",
    },
    (118, 119): {"A": "Aα 类纤维", "B": "Aβ 类纤维", "C": "Aδ 类纤维", "D": "B 类纤维"},
    (120, 121): {
        "A": "异柠檬酸脱氢酶", "B": "6-磷酸葡萄糖酸脱氢酶",
        "C": "琥珀酸脱氢酶", "D": "丙酮酸脱氢酶复合体",
    },
    (122, 123): {"A": "5S rRNA", "B": "16S rRNA", "C": "18S rRNA", "D": "28S rRNA"},
    (124, 125): {"A": "鼻咽癌", "B": "淋巴管瘤", "C": "甲状腺滤泡癌", "D": "卵巢粒层细胞瘤"},
    (126, 127): {
        "A": "结节性淋巴细胞为主型", "B": "结节硬化型",
        "C": "混合细胞型", "D": "淋巴细胞减少型",
    },
    (128, 129): {"A": "急性心包炎", "B": "急性心肌炎", "C": "急性心肌梗死", "D": "感染性心内膜炎"},
    (130, 131): {"A": "烟酰胺", "B": "小剂量美蓝", "C": "硫代硫酸钠", "D": "高血糖素"},
    (132, 133): {"A": "血淀粉酶", "B": "血脂肪酶", "C": "血尿素氮", "D": "血正铁白蛋白"},
    (134, 135): {"A": "Perthes 试验", "B": "Buerger 试验", "C": "Pratt 试验", "D": "Trendelenburg 试验"},
}

B_STEMS = {
    116: "膜电位突然由静息电位改变为 0 mV 时",
    117: "膜电位突然由静息电位去极化至 Na+ 平衡电位时",
    118: "传导皮肤粗略触压觉的神经纤维是",
    119: "传导皮肤精细触压觉的神经纤维是",
    120: "以上脱氢酶催化的反应不伴脱羧的是",
    121: "以上脱氢酶需以 NADP+ 作为辅酶的是",
    122: "在蛋白质生物合成的起始阶段，识别 S-D 序列的是",
    123: "在蛋白质生物合成的延长阶段，催化成肽过程的是",
    124: "呈浸润性生长，不发生淋巴转移的是",
    125: "呈浸润性生长，常发生淋巴转移的是",
    126: "上述霍奇金淋巴瘤中镜影细胞最常见于",
    127: "上述霍奇金淋巴瘤中 EBV 感染最常见于",
    128: "男性，46 岁。10 天前发热、恶心、腹泻，2 天来心悸伴心前区痛，夜间睡眠有憋气感。查体：T 37.6℃，P 115 次/分，BP 110/65 mmHg，双肺底偶闻及湿啰音，心尖部闻及 S3 奔马律。心电图示 T 波低平。血清肌钙蛋白升高。该患者最可能的诊断是",
    129: "女性，30 岁。持续发热 2 周，有先天性心脏病史。查体：贫血貌，胸骨左缘 3-4 肋间闻及 4/6 级粗糙收缩期杂音，伴震颤。脾肋下 2 cm。血培养 2 次阳性。入院后第 3 天突感呼吸困难、胸痛，咯血多次，左肺下叶闻及啰音。该患者最可能的诊断是",
    130: "杀鼠剂中毒的有效解毒药是",
    131: "阿米替林中毒的有效解毒药是",
    132: "对发病较晚的急性胰腺炎诊断最有意义的检查是",
    133: "轻症急性胰腺炎阴性，重症胰腺炎阳性的检查是",
    134: "男性，55 岁。左下肢麻木胀痛 3 年，间歇性跛行 1 年，左下肢疼痛逐渐加重，夜间疼痛更甚，吸烟 30 年。查体：屈膝位，左小腿皮温较对侧降低，左足背动脉搏动消失。对该患者最有助于诊断的试验是",
    135: "女性，29 岁。产后 1 周，左腰部酸痛不适 3 天，伴左下肢突发肿胀 2 天。查体：左下肢全肢肿胀，小腿屈肌部位张力高，足背水肿，左大腿和小腿皮肤青紫，足部皮温降低，足背动脉搏动极微弱。对该患者最有助于诊断的试验是",
}


def make_assignments() -> dict[int, tuple[str, str, int | None]]:
    a: dict[int, tuple[str, str, int | None]] = {}
    def put(numbers, site, evidence, lectures):
        for q, lecture in zip(numbers, lectures):
            a[q] = (site, evidence, lecture)
    put(range(1, 17), "physiology", "physiology", [4, 8, 12, 13, 13, 15, 22, 23, 26, 27, 29, 32, 33, 41, 39, 41])
    put(range(17, 29), "biochemistry", "biochemistry", [8, 15, 12, 1, 4, 7, 16, 17, 17, 19, 14, 8])
    put(range(29, 41), "pathology", "pathology", [23, 22, 24, 24, 26, 26, 14, 7, 1, 16, 19, 21])
    put(range(41, 57), "med", "med", [10, 47, 1, 8, 7, 3, 52, 49, 50, 16, 17, 23, 27, 29, 41, 44])
    a[41] = ("med", "biochemistry", 10)
    put(range(57, 68), "surgery", "surgery", [30, 1, 5, 7, 11, 14, 16, 18, 28, 28, 25])
    put(range(68, 95), "med", "med", [9, 9, 53, 53, 53, 13, 13, 13, 54, 54, 54, 22, 22, 20, 27, 27, 27, 35, 35, 35, 38, 38, 38, 45, 45, 36, 36])
    put(range(95, 108), "surgery", "surgery", [10, 10, 10, 16, 16, 15, 15, 15, 25, 25, 25, 27, 27])
    for q in range(108, 116): a[q] = ("med", "med", None)
    put(range(116, 120), "physiology", "physiology", [3, 3, 30, 30])
    put(range(120, 124), "biochemistry", "biochemistry", [2, 3, 18, 18])
    put(range(124, 128), "pathology", "pathology", [26, 26, 26, 26])
    put(range(128, 134), "med", "med", [49, 51, 48, 48, 23, 23])
    put(range(134, 136), "surgery", "surgery", [17, 17])
    put(range(136, 142), "physiology", "physiology", [1, 8, 16, 20, 26, 34])
    put(range(142, 148), "biochemistry", "biochemistry", [12, 2, 9, 8, 19, 14])
    put(range(148, 154), "pathology", "pathology", [23, 23, 25, 3, 20, 21])
    a[153] = ("pathology", "med", 25)
    put(range(154, 160), "med", "med", [10, 54, 14, 26, 28, 40])
    put(range(160, 166), "surgery", "surgery", [32, 4, 9, 16, 28, 20])
    assert sorted(a) == list(range(1, 166))
    return a


def topic(subject: str, lecture: int | None, q: int) -> str:
    if q in range(108, 116): return "医学人文"
    if q == 41: return "消化"
    if q == 153: return "泌尿系统"
    if subject == "med":
        return next(name for lo, hi, name in [(1, 13, "呼吸"), (14, 23, "消化"), (24, 27, "肾脏"), (28, 35, "血液"), (36, 42, "内分泌"), (43, 47, "风湿"), (48, 48, "中毒"), (49, 57, "循环")] if lo <= lecture <= hi)
    if subject == "physiology":
        return next(name for lo, hi, name in [(1, 1, "绪论"), (2, 5, "细胞基本功能"), (6, 8, "血液"), (9, 13, "循环系统"), (14, 17, "呼吸系统"), (18, 22, "消化系统"), (23, 23, "能量代谢与体温"), (24, 26, "泌尿系统"), (27, 34, "神经与感觉"), (35, 40, "内分泌"), (41, 41, "生殖系统")] if lo <= lecture <= hi)
    if subject == "biochemistry":
        return next(name for lo, hi, name in [(1, 3, "糖代谢与生物氧化"), (4, 6, "脂代谢"), (7, 8, "氨基酸与蛋白质"), (9, 9, "核苷酸代谢"), (10, 11, "胆色素与生物转化"), (12, 13, "酶与维生素"), (14, 21, "分子生物学") ] if lo <= lecture <= hi)
    if subject == "pathology":
        return next(name for lo, hi, name in [(1, 5, "消化系统"), (6, 10, "心血管系统"), (11, 15, "呼吸系统"), (16, 16, "内分泌系统"), (17, 17, "免疫性疾病"), (18, 18, "生殖系统"), (19, 19, "乳腺疾病"), (20, 20, "结核"), (21, 21, "传染病"), (22, 22, "损伤与修复"), (23, 23, "适应与损伤"), (24, 24, "局部血液循环障碍"), (25, 25, "炎症"), (26, 26, "肿瘤")] if lo <= lecture <= hi)
    if 20 <= lecture <= 29: return "骨科"
    if lecture >= 30: return "外科总论"
    return next(name for lo, hi, name in [(1, 4, "颈胸与乳房疾病"), (5, 12, "腹部疾病"), (13, 16, "肝胆胰疾病"), (17, 17, "周围血管疾病"), (18, 19, "泌尿外科")] if lo <= lecture <= hi)


def tokens(text: str) -> set[str]:
    text = re.sub(r"\s+", "", text)
    return {text[i:i + 2] for i in range(max(0, len(text) - 1))}


def clean_excerpt(text: str, terms: set[str]) -> str:
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" ·|-")
        if len(line) < 12 or re.search(r"天天师兄|每日计划|by戒不掉|核心精讲", line):
            continue
        score = len(tokens(line) & terms)
        lines.append((score, len(line), line))
    lines.sort(reverse=True)
    chosen = [line for score, _, line in lines if score > 0][:2]
    if not chosen and lines: chosen = [lines[0][2]]
    result = "；".join(chosen)
    return result[:220].rstrip("，；。") + ("。" if result else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--index", type=Path, default=ROOT / "output/27冲刺押题错题本-20261021/讲义索引/全部讲义逐页文本.json")
    args = parser.parse_args()

    questions, _ = extract_exam(args.source)
    for (start, end), options in B_PAIRS.items():
        for q in range(start, end + 1): questions[q] = {"stem": B_STEMS[q], "options": options}
    missing = [q for q in range(1, 166) if q not in questions]
    if missing: raise RuntimeError(f"Missing questions: {missing}")

    answers = answer_key()
    assignments = make_assignments()
    reviewed = {row[0]: row[6] for row in ROWS}
    index = json.loads(args.index.read_text())
    by_subject: dict[str, list[dict]] = {}
    for entry in index: by_subject.setdefault(entry["subject"], []).append(entry)

    page_map: dict[int, int] = {}
    import pdfplumber
    with pdfplumber.open(args.source) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for number in re.findall(r"(?m)^\s*(\d{1,3})\.(?!\d)", text):
                q = int(number)
                if 1 <= q <= 165: page_map[q] = page_no

    render_jobs: dict[tuple[str, int], tuple[dict, str]] = {}
    output_dir = ROOT / "public/exams" / KEY
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {s: {"meta": {"title": f"基础强化摸底考试·{label}", "sourceName": args.source.name, "sourcePages": 28, "answerNote": "答案依据用户提供的答案图；每题附解析、讲义要点和对应讲义原页。"}, "groups": [], "pages": [], "lectures": [], "topics": []} for s, label in SUBJECT_LABELS.items()}
    lecture_meta: dict[str, dict[str, dict]] = {s: {} for s in SUBJECT_LABELS}

    for q in range(1, 166):
        site_subject, evidence_subject, lecture_no = assignments[q]
        question = questions[q]
        answer = answers[q]
        correct_labels = [question["options"][letter] for letter in answer]
        lecture_id = f"foundation-{evidence_subject}-{lecture_no:02d}" if lecture_no else "foundation-medical-humanities"
        evidence = None
        excerpt = ""
        lecture_title = "医学伦理与卫生法规"
        if lecture_no is not None:
            index_subject = INDEX_SUBJECTS[evidence_subject]
            candidates = [entry for entry in by_subject.get(index_subject, []) if re.match(rf"0?{lecture_no}\s", entry["name"])]
            if not candidates: raise RuntimeError(f"No lecture for q{q}: {index_subject} {lecture_no}")
            entry = candidates[0]
            terms = tokens(question["stem"] + " ".join(question["options"].values()) + " ".join(correct_labels))
            scored = [(len(terms & tokens(text)), page_no, text) for page_no, text in enumerate(entry["pages"], 1) if not re.search(r"\n\s*真题解析[·・]", text)]
            _, selected_page, page_text = max(scored, key=lambda item: item[0])
            lecture_title = re.sub(r"^0?\d+\s+27考研：", "", entry["name"]).replace(" 核心-真题-串联-导图 天天师兄.pdf", "")
            filename = f"lecture-{evidence_subject}-{lecture_no:02d}-p{selected_page:02d}.webp"
            token = (entry["path"], selected_page)
            render_jobs.setdefault(token, (entry, filename))
            excerpt = clean_excerpt(page_text, terms)
            evidence = {
                "lectureId": lecture_id, "sourceSubject": evidence_subject, "sourceFile": Path(entry["path"]).name,
                "page": selected_page, "pageLabel": f"PDF第{selected_page}页", "title": f"{lecture_title} · 第{selected_page}页",
                "image": f"exams/{KEY}/{filename}", "description": f"基础强化摸底考试第{q}题对应讲义原页。",
                "knowledgePoints": [lecture_title, excerpt or f"答案依据：{answer}. {'；'.join(correct_labels)}"], "questionNumbers": [q],
            }
        reason = reviewed.get(q)
        if not reason:
            reason = excerpt or f"本题考查{lecture_title}。正确选项直接对应讲义中的标准结论。"
        explanation = f"答案为 {answer}（{'；'.join(correct_labels)}）。{reason}"
        wrong_labels = [f"{key}. {label}" for key, label in question["options"].items() if key not in answer]
        stem = {
            "number": q, "sourceQuestion": q, "sourcePage": page_map.get(q), "text": question["stem"],
            "answerRaw": answer, "answer": list(answer), "answerMode": "多选" if q >= 136 else "单选",
            "answerState": "按用户提供的答案图录入", "lectureId": lecture_id, "explanation": explanation,
            "knowledgeConnections": [f"讲义定位：{lecture_title}", f"必会项：{answer}. {'；'.join(correct_labels)}", f"易混对照：{'；'.join(wrong_labels)}"],
        }
        group = {
            "id": f"{site_subject}-{KEY}-q{q:03d}", "page": page_map.get(q, 1), "sourceKey": f"{site_subject}-{KEY}",
            "sourceName": args.source.name, "sourceSection": SUBJECT_LABELS[site_subject], "sourceQuestion": str(q), "sourceLabel": "基础强化摸底卷",
            "title": f"基础摸底卷 · 第{q}题 · {lecture_title}", "kind": "X" if q >= 136 else "B" if q >= 116 else "A",
            "kindLabel": "多项选择" if q >= 136 else "配伍单选" if q >= 116 else "单项选择", "answerLayout": "rows",
            "topic": topic(site_subject, lecture_no, q), "lectureIds": [lecture_id], "supplement": True,
            "supplementNotice": "已录入完整题干、答案、解析和对应讲义", "answerSourceLabel": "基础摸底卷答案",
            "answerSourceName": "用户提供的答案图", "hideSource": True,
            "options": [{"key": key, "displayKey": key, "label": label} for key, label in question["options"].items()],
            "stems": [stem],
            "lectureSummary": [f"所属模块：{lecture_title}", f"答案依据：{answer}. {'；'.join(correct_labels)}", reason],
        }
        if evidence:
            group["lectureEvidence"] = evidence
            group["lectureEvidencePages"] = [evidence]
        else:
            group["lectureEvidenceNotice"] = "医学人文题以法规与伦理文字讲义要点展示。"
        data[site_subject]["groups"].append(group)
        lecture_meta[site_subject][lecture_id] = {"id": lecture_id, "number": lecture_no or 99, "title": lecture_title, "pageCount": 1}

    catalog = []
    for subject, payload in data.items():
        payload["topics"] = list(dict.fromkeys(group["topic"] for group in payload["groups"]))
        payload["lectures"] = list(lecture_meta[subject].values())
        payload["meta"].update(groupCount=len(payload["groups"]), stemCount=len(payload["groups"]), lectureCount=len(payload["lectures"]))
        target = ROOT / f"src/data/{subject}-foundation-mock-exam-data.json"
        review_foundation_jaundice(payload)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        catalog.append({
            "id": f"{subject}-foundation-mock-exam", "subject": subject, "subjectLabel": SUBJECT_LABELS[subject],
            "title": f"基础强化摸底考试·{SUBJECT_LABELS[subject]}", "category": "基础摸底卷",
            "sourceFile": target.name, "groupIds": [g["id"] for g in payload["groups"]],
            "groupCount": len(payload["groups"]), "stemCount": len(payload["groups"]),
        })
        print(f"{subject}: {len(payload['groups'])} questions")
    (ROOT / "src/data/foundation-mock-exam-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")

    pdftoppm = "/Users/ray/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftoppm"
    def render(item):
        (pdf_path, page_no), (entry, filename) = item
        target = output_dir / filename
        if target.exists(): return
        prefix = Path("/private/tmp") / (KEY + "-" + filename.removesuffix(".webp"))
        subprocess.run([pdftoppm, "-f", str(page_no), "-l", str(page_no), "-singlefile", "-scale-to", "1500", "-png", pdf_path, str(prefix)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        image = Image.open(str(prefix) + ".png").convert("RGB")
        image.save(target, quality=82, method=4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(render, render_jobs.items()))
    print(f"rendered lecture pages: {len(render_jobs)}")


if __name__ == "__main__":
    main()
