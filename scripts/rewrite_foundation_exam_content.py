#!/usr/bin/env python3
"""Rewrite foundation-exam explanations from clean lecture core content."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from review_foundation_jaundice import review_foundation_jaundice

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
KEY = "foundation-mock-exam-20260907"
DATA_FILES = sorted((ROOT / "src/data").glob("*-foundation-mock-exam-data.json"))
INDEX = ROOT / "output/27冲刺押题错题本-20261021/讲义索引/全部讲义逐页文本.json"
PDFTOPPM = Path("/Users/ray/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftoppm")
LECTURE_FILE_OVERRIDES = {
    27: "16 27考研：生化 DNA的合成 核心-真题-串联-导图 天天师兄.pdf",
}
CONTENT_OVERRIDES = {
    51: [
        "结核性腹膜炎常见慢性低热、盗汗和腹部揉面或柔韧感。",
        "肠结核与结核性腹膜炎可并发肠梗阻。",
        "出现停止排气排便、肠型及肠鸣音亢进时，先用立位腹部X线片判断梗阻并观察气液平。",
    ],
    81: [
        "感染、腹泻导致的水电解质紊乱等可诱发肝性脑病；意识模糊、躁动和抽搐提示神经精神症状加重。",
        "减少肠道氨吸收可用乳果糖或弱酸性灌肠液，镇静药尤其苯二氮䓬类应慎用。",
        "利福昔明经口用于减少产氨菌；讲义将阻断异常门-体分流列为反复发作时的处理方向。",
    ],
    147: [
        "RT-PCR先以逆转录酶合成cDNA，再以DNA聚合酶扩增cDNA。",
        "实时荧光定量PCR的扩增阶段需要耐热DNA聚合酶。",
        "探针的标记与合成可利用DNA聚合酶掺入带标记的核苷酸；Western blot检测蛋白质，不使用DNA聚合酶。",
    ],
}


def normalize(text: str) -> str:
    text = text.replace("ttsx", "").replace("×109", "×10⁹").replace("×1012", "×10¹²")
    text = text.replace("可能可能最可能：", "典型提示：").replace("可能最可能：", "典型提示：")
    text = text.replace("、 多揉面", "、揉面")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ·；;，,")
    return text


def tokens(text: str) -> set[str]:
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", text).lower()
    return {text[i:i + 2] for i in range(max(0, len(text) - 1))}


def reviewed_rows() -> dict[int, str]:
    source = (ROOT / "scripts/build_mock_exam_error_book.py").read_text()
    tree = ast.parse(source)
    rows = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "ROWS" for t in node.targets))
    return {row[0]: row[6] for row in rows}


def core_segments(entry: dict) -> list[tuple[int, str]]:
    out = []
    include = True
    for page_no, page in enumerate(entry["pages"], 1):
        kept_lines = []
        for line in page.splitlines():
            if re.search(r"真题解析[·・]", line):
                include = False
                continue
            if re.search(r"(?:核心精讲|思维导图|专题串联|易错小结|考点补充)[·・]", line):
                include = True
            if include:
                kept_lines.append(line)
        chunks = re.split(r"\n\s*\n|(?<=[。；])\s*", "\n".join(kept_lines))
        for raw in chunks:
            value = normalize(raw)
            value = re.sub(r"^[-—]?\d+[-—]?$", "", value)
            if not 10 <= len(value) <= 260:
                continue
            if re.search(r"每日计划|精选答疑|核心精讲很详细|思维导图帮助|真题解析|天天师兄|阶段考试|\d{4}N\d|^[ABCD][.．]", value):
                continue
            if re.search(r"(?:男性|女性)，?\d+\s*岁", value):
                continue
            out.append((page_no, value))
    return out


def clean_title(filename: str) -> str:
    return re.sub(r"^0?\d+\s+27考研：", "", filename).replace(" 核心-真题-串联-导图 天天师兄.pdf", "")


def key_clues(stem: dict, basis: list[str]) -> str:
    text = " ".join(filter(None, [stem.get("sharedText"), stem.get("text")]))
    target = tokens(" ".join(basis))
    clauses = [normalize(x) for x in re.split(r"[。；;！？?]", text)]
    clauses = [x for x in clauses if 8 <= len(x) <= 100 and not re.fullmatch(r"(?:该|此)?患者.*(?:是|为)$", x)]
    scored = sorted(((len(tokens(x) & target), -len(x), x) for x in clauses), reverse=True)
    chosen = []
    for _, _, clause in scored:
        if clause not in chosen:
            chosen.append(clause)
        if len(chosen) == 2:
            break
    return "；".join(chosen) or normalize(text)[:150]


def reasoning(q: int, stem: dict, answer: str, labels: list[str], basis: list[str], reviewed: dict[int, str]) -> str:
    correct = "；".join(labels)
    if q == 51:
        return (
            "题干先以低热、盗汗和腹部揉面感提示结核性腹膜炎，随后出现突发绞痛、停止排气排便、肠型和肠鸣音亢进，"
            "说明当前首先要判断是否并发机械性肠梗阻。立位腹部X线片能快速观察肠管扩张及气液平，因此首选C。"
            "血沉只能反映炎症活动；急性梗阻时结肠镜不是首选；腹部CT可进一步明确病因和部位，但不替代首轮快速腹平片。"
        )
    if q in reviewed:
        return reviewed[q]
    if q == 147:
        return "RT-PCR、实时荧光定量PCR都需要DNA聚合酶完成扩增；探针标记/合成也可利用DNA聚合酶掺入标记核苷酸。Western blot检测的是蛋白质，核心反应为抗原-抗体结合，不使用DNA聚合酶。因此选ABC。"
    if q == 81:
        return "患者有肝硬化和门-体分流基础，感染及腹泻后出现意识模糊、躁动和抽搐，符合肝性脑病。A错在应使用弱酸性而非弱碱性灌肠液；B中地西泮可加重中枢抑制；C中利福昔明应经口而非静脉使用。按本卷答案及讲义的门-体分流处理原则，选择D。"
    clues = key_clues(stem, basis)
    support = "；".join(basis[:2])
    question = stem.get("text", "")
    if "首选" in question or "首先" in question:
        lead = "本题考查的是当前情境下的首选步骤，而不是所有可用检查或治疗。"
    elif "最可能" in question or "诊断" in question:
        lead = "诊断应以题干中的特征性线索组合判断，不能由单个症状作结论。"
    elif "错误" in question or "不包括" in question or "不正确" in question:
        lead = "题干要求选择错误项，需先用讲义中的标准结论逐项反向核对。"
    elif len(answer) > 1:
        lead = "本题为多选题，应按同一讲义判据逐项判断，不能因为某项表述熟悉就漏选。"
    else:
        lead = "先抓题干的决定性线索，再与讲义中的标准结论对应。"
    return f"{lead}关键线索是：{clues}。讲义依据：{support}。因此答案为{answer}（{correct}）。"


def render(entry: dict, page: int, filename: str) -> None:
    target = ROOT / "public/exams" / KEY / filename
    if target.exists():
        return
    prefix = Path("/private/tmp") / f"{KEY}-rewrite-{filename[:-5]}"
    subprocess.run([str(PDFTOPPM), "-f", str(page), "-l", str(page), "-singlefile", "-scale-to", "1500", "-png", entry["path"], str(prefix)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    Image.open(str(prefix) + ".png").convert("RGB").save(target, quality=82, method=4)


def main() -> None:
    index = json.loads(INDEX.read_text())
    by_file = {Path(item["path"]).name: item for item in index}
    reviewed = reviewed_rows()
    violations = []
    counts = {"groups": 0, "shared": 0, "rendered": 0}
    for path in DATA_FILES:
        payload = json.loads(path.read_text())
        for group in payload["groups"]:
            counts["groups"] += 1
            stem = group["stems"][0]
            q = int(stem["sourceQuestion"])
            stem["text"] = normalize(stem.get("text", ""))
            if stem.get("sharedText"):
                stem["sharedText"] = normalize(stem["sharedText"])
            if stem.get("sharedText"):
                counts["shared"] += 1
            evidence = group.get("lectureEvidence")
            if not evidence:
                stem["explanation"] = f"答案为{stem['answerRaw']}。本题属于医学人文，按题干中的伦理原则、行为主体和法律边界逐项判断。"
                stem["knowledgeConnections"] = ["判断顺序：主体与情境", "再看：伦理原则或法律义务", f"结论：{stem['answerRaw']}"]
                continue
            if q in LECTURE_FILE_OVERRIDES:
                evidence["sourceFile"] = LECTURE_FILE_OVERRIDES[q]
                lecture_no = int(re.match(r"\d+", evidence["sourceFile"]).group())
                evidence["lectureId"] = f"foundation-{evidence['sourceSubject']}-{lecture_no:02d}"
                stem["lectureId"] = evidence["lectureId"]
                group["lectureIds"] = [evidence["lectureId"]]
                group["title"] = f"基础摸底卷 · 第{q}题 · {clean_title(evidence['sourceFile'])}"
            entry = by_file.get(evidence["sourceFile"])
            segments = core_segments(entry) if entry else []
            options = {item["key"]: item["label"] for item in group["options"]}
            answer = stem["answerRaw"]
            labels = [options[key] for key in answer]
            query = " ".join(filter(None, [stem.get("sharedText"), stem.get("text"), " ".join(labels) * 3]))
            qt = tokens(query)
            answer_tokens = tokens(" ".join(labels))
            ranked = []
            for page, text in segments:
                segment_tokens = tokens(text)
                relevance = len(qt & segment_tokens) / max(1, len(segment_tokens)) ** 0.5
                answer_match = 2 * len(answer_tokens & segment_tokens) / max(1, len(answer_tokens))
                exact_match = 2 * sum(normalize(label) in normalize(text) for label in labels)
                ranked.append((relevance + answer_match + exact_match, page, text))
            ranked.sort(reverse=True)
            selected = []
            seen = set()
            for score, page_no, text in ranked:
                signature = text[:35]
                if signature in seen:
                    continue
                seen.add(signature)
                selected.append((page_no, text))
                if len(selected) == 4:
                    break
            if not selected:
                violations.append(f"q{q}: no clean lecture core segment")
                selected = [(evidence["page"], f"{evidence['title']}：请结合讲义原页复习。")]
            basis = list(CONTENT_OVERRIDES.get(q, [text for _, text in selected]))
            if q in reviewed and reviewed[q] not in basis:
                basis.insert(0, reviewed[q])
            stem["explanation"] = f"正确答案：{answer}（{'；'.join(labels)}）。\n\n判断思路：{reasoning(q, stem, answer, labels, basis, reviewed)}"
            wrong = [f"{key}. {label}" for key, label in options.items() if key not in answer]
            stem["knowledgeConnections"] = [f"题干线索：{key_clues(stem, basis)}", *[f"讲义要点：{text}" for text in basis[:3]], f"易混项：{'；'.join(wrong)}"]
            group["lectureSummary"] = [f"模块：{clean_title(evidence['sourceFile'])}", *basis[:4]]
            pages = []
            for page_no in dict.fromkeys(page for page, _ in selected[:2]):
                subject = evidence["sourceSubject"]
                lecture_match = re.match(r"(\d+)", evidence["sourceFile"])
                lecture_no = int(lecture_match.group(1)) if lecture_match else 0
                filename = f"lecture-{subject}-{lecture_no:02d}-p{page_no:02d}.webp"
                render(entry, page_no, filename)
                counts["rendered"] += 1
                page_points = [text for p, text in selected if p == page_no][:3]
                pages.append({**evidence, "page": page_no, "pageLabel": f"PDF第{page_no}页", "title": f"{clean_title(evidence['sourceFile'])} · 第{page_no}页", "image": f"exams/{KEY}/{filename}", "description": f"第{q}题对应的讲义核心精讲原页。", "knowledgePoints": page_points, "questionNumbers": [q]})
            group["lectureEvidence"] = pages[0]
            group["lectureEvidencePages"] = pages
            text_dump = json.dumps(group, ensure_ascii=False)
            if re.search(r"\[共用题干\]|\[\d+题\]|\d{4}N\d", text_dump):
                violations.append(f"q{q}: residual question-bank marker")
        review_foundation_jaundice(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({**counts, "violations": violations}, ensure_ascii=False, indent=2))
    if violations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
