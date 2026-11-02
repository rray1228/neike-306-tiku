"""Keep foundation question 41 tied to the actual hereditary-jaundice table."""

from copy import deepcopy


GROUP_ID = "med-foundation-mock-exam-20260907-q041"
LECTURE_ID = "foundation-biochemistry-10"

EXPLANATION = (
    "正确答案：B（Crigler-Najjar综合征）。\n\n题干的关键是“UCB甚高、核黄疸、预后极差”，提示胆红素结合过程严重受损，"
    "对应重型Crigler-Najjar综合征（Ⅰ型）。胆红素UDP-葡萄糖醛酸转移酶（UGT）严重缺陷，"
    "使UCB不能充分转化为CB，血UCB显著升高；未与白蛋白结合的UCB具有脂溶性和神经毒性，"
    "可进入脑组织引起核黄疸。\n\n"
    "A．Gilbert综合征：讲义归纳为肝细胞摄取、结合障碍，血UCB升高。"
    "与B同属UCB升高型，但本题进一步给出严重核黄疸及极差预后，应选B。\n\n"
    "B．Crigler-Najjar综合征：胆红素结合障碍，血UCB升高；题干描述的是严重结合障碍所致的重型表现。\n\n"
    "C．Rotor综合征：讲义归纳为摄取、排泄障碍，血UCB和CB均可升高，"
    "与题干突出严重UCB升高的结合障碍不符。\n\n"
    "D．Dubin-Johnson综合征：胆红素排泄障碍，血CB升高，"
    "不是题干所述的UCB极高型黄疸。"
)

CONNECTIONS = [
    "胆红素代谢：血UCB与白蛋白结合运输→肝细胞摄取→UGT催化与UDP-葡萄糖醛酸结合形成CB→经MRP2排入胆汁。",
    "UCB为间接胆红素，脂溶性、毒性较大，不出现在尿液中；CB为直接胆红素，水溶性、毒性较小，可出现在尿液中。",
    "结合障碍：Gilbert与Crigler-Najjar均可出现UCB升高；题干的严重程度是本题区分两者的关键。",
    "排泄障碍：Dubin-Johnson以CB升高为主；Rotor按讲义表格记为摄取、排泄障碍，UCB及CB均升高。",
]

SUMMARY = [
    "Gilbert：摄取、结合障碍→UCB↑。",
    "Crigler-Najjar：结合障碍→UCB↑；重型可出现核黄疸。",
    "Rotor：摄取、排泄障碍→UCB↑、CB↑。",
    "Dubin-Johnson：排泄障碍→CB↑。",
    "UCB→CB为UGT催化的结合反应；CB排入胆汁依赖转运蛋白MRP2。",
]

PAGES = [
    {
        "lectureId": LECTURE_ID, "lectureNumber": 10, "sourceSubject": "biochemistry",
        "sourceFile": "10 27考研：生化 胆色素代谢 核心-真题-串联-导图 天天师兄.pdf",
        "page": 2, "pageLabel": "第10讲 · PDF第2页",
        "title": "胆色素代谢：四种遗传性黄疸对照表与胆红素代谢途径",
        "image": "biochemistry/lecture-pages/lecture-10-page-02.webp",
        "questionNumbers": [41], "optionKeys": ["A", "B", "C", "D"],
        "knowledgePoints": SUMMARY[:4],
    },
    {
        "lectureId": LECTURE_ID, "lectureNumber": 10, "sourceSubject": "biochemistry",
        "sourceFile": "【精编版】生化合集.pdf", "page": 81, "pageLabel": "精编合集 · PDF第81页",
        "title": "胆色素代谢：UCB、CB的转化及尿胆红素",
        "image": "site-assets/biochemistry-review-20261023/precision-page-081.avif",
        "questionNumbers": [41],
        "knowledgePoints": ["UCB为脂溶性未结合胆红素，CB为水溶性结合胆红素。", "尿胆红素指尿CB；UCB不出现在尿液中。"],
    },
]


def review_foundation_jaundice(payload: dict) -> None:
    target = next((group for group in payload.get("groups", []) if group["id"] == GROUP_ID), None)
    if target is None:
        return
    # Preserve the original question, keys, answer, stem position and storage ID.
    target["stems"][0]["explanation"] = EXPLANATION
    target["stems"][0]["knowledgeConnections"] = CONNECTIONS.copy()
    target["lectureSummary"] = SUMMARY.copy()
    target["lectureEvidencePages"] = deepcopy(PAGES)
    target["lectureEvidence"] = target["lectureEvidencePages"][0]
    target["stems"][0]["lectureEvidencePages"] = deepcopy(PAGES)
    for lecture in payload.get("lectures", []):
        if lecture["id"] == LECTURE_ID:
            lecture["pageCount"] = 4
