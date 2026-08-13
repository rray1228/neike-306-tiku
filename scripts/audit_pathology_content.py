#!/usr/bin/env python3
"""Structural checks for the standalone pathology payload."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "src/data/pathology-data.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["meta"]["siteIntegrated"] is True
    assert payload["meta"]["sourcePdfPages"] == 37
    assert payload["meta"]["sourcePages"] == 35
    assert payload["meta"]["lectureCount"] == 26
    assert payload["meta"]["groups"] == 77
    assert payload["meta"]["stems"] == 315
    assert payload["meta"]["lectureEvidenceStems"] == 315

    ids = [group["id"] for group in payload["groups"]]
    assert len(ids) == len(set(ids)), "duplicate group ids"
    assert all(group["page"] >= 3 for group in payload["groups"])
    assert all(group.get("stems") for group in payload["groups"]), "empty question group"

    invalid_answers = []
    duplicate_answers = []
    duplicate_option_keys = []
    glued_answer_stems = []
    missing_images = []
    missing_lecture_images = []
    for page in payload["pages"]:
        image = root / "public" / page["image"]
        if not image.exists():
            missing_images.append(str(image))
    for group in payload["groups"]:
        option_keys = [option["key"] for option in group.get("options", [])]
        keys = set(option_keys)
        if len(option_keys) != len(keys):
            duplicate_option_keys.append(group["id"])
        for index, stem in enumerate(group.get("stems", [])):
            answer = stem.get("answer", [])
            if len(answer) != len(set(answer)):
                duplicate_answers.append(f"{group['id']}:{index}")
            absent = [key for key in answer if key not in keys]
            if absent:
                invalid_answers.append(f"{group['id']}:{index}={''.join(absent)}")
            if re.search(r"[；;]\s*[A-Z①-⑥]{1,}\s*$", stem.get("text", "")):
                glued_answer_stems.append(f"{group['id']}:{index}")
            evidence = stem.get("lectureEvidence")
            assert evidence, f"missing lecture evidence: {group['id']}:{index}"
            image = root / "public" / evidence["image"]
            if not image.exists():
                missing_lecture_images.append(str(image))

    assert not missing_images, f"missing source images: {missing_images}"
    assert not missing_lecture_images, f"missing lecture images: {missing_lecture_images}"
    assert not duplicate_answers, f"duplicate answer keys: {duplicate_answers}"
    assert not duplicate_option_keys, f"duplicate option keys: {duplicate_option_keys}"
    assert not invalid_answers, f"answers missing from option bank: {invalid_answers}"
    assert not glued_answer_stems, f"answer text glued to stem: {glued_answer_stems}"

    cirrhosis = next(group for group in payload["groups"] if group["id"] == "p04-g1")
    cirrhosis_options = {
        option["key"]: option["label"] for option in cirrhosis["options"]
    }
    cirrhosis_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in cirrhosis["stems"]
    }
    assert cirrhosis_options["E"] == "静水压和通透性↑"
    assert cirrhosis_options["I"] == "雌激素灭活障碍"
    assert cirrhosis_options["U"] == "睾丸萎缩"
    assert cirrhosis_options["④"] == "白/球蛋白↓或倒置"
    assert cirrhosis_options["⑥"] == "有效循环血量↓"
    assert set("①②③④⑤⑥").issubset(cirrhosis_options)
    assert cirrhosis_answers == {
        "肝功能障碍临床表现": "BDFHIJMNRSUWXZ②③④⑤",
        "门脉高压的临床表现": "ACEGKLOPQTV①",
        "腹水形成的机制": "EVW③⑥",
    }
    assert cirrhosis["reviewState"] == "已按题册原图与讲义逐题复核"

    rheumatism = next(group for group in payload["groups"] if group["id"] == "p08-g1")
    rheumatism_options = {
        option["key"]: option["label"] for option in rheumatism["options"]
    }
    rheumatism_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in rheumatism["stems"]
    }
    assert rheumatism_options["B"] == "变态反应为III型"
    assert rheumatism_options["J"] == "变态反应为II型"
    assert rheumatism_answers == {
        "风湿": "ACDFJKL",
        "类风湿": "BEGHILM",
    }
    assert rheumatism["reviewState"] == "已按题册原图与讲义逐题复核"

    groups_by_id = {group["id"]: group for group in payload["groups"]}

    def assert_group(
        group_id: str,
        expected_options: list[tuple[str, str]],
        expected_answers: list[tuple[str, str]],
    ) -> None:
        group = groups_by_id[group_id]
        actual_options = [(item["key"], item["label"]) for item in group["options"]]
        actual_answers = [
            (stem["text"], "".join(stem["answer"])) for stem in group["stems"]
        ]
        assert actual_options == expected_options, f"{group_id} option mismatch"
        assert actual_answers == expected_answers, f"{group_id} answer mismatch"
        assert group["reviewState"] == "已按题册原图与讲义逐题复核"

    thyroid = groups_by_id["p11-g2"]
    thyroid_answers = {
        stem["text"]: "".join(stem["answer"]) for stem in thyroid["stems"]
    }
    assert thyroid_answers["甲状腺腺瘤"] == "BDEGI"
    assert "I" in thyroid_answers["甲状腺腺瘤"]
    assert thyroid["reviewState"] == "已按题册原图与讲义逐题复核"

    page_counts = Counter(group["page"] for group in payload["groups"])
    assert page_counts[5] == 2
    assert page_counts[19] == 2
    assert {page: page_counts[page] for page in [11, 13, 16, 17, 21, 23, 25, 26, 27, 31, 32, 36]} == {
        11: 3, 13: 3, 16: 2, 17: 4, 21: 2, 23: 2,
        25: 2, 26: 4, 27: 2, 31: 1, 32: 3, 36: 2,
    }

    def assert_answers(group_id: str, expected: list[tuple[str, str]]) -> None:
        group = groups_by_id[group_id]
        actual = [(stem["text"], "".join(stem["answer"])) for stem in group["stems"]]
        assert actual == expected, f"{group_id} answer mismatch: {actual}"
        assert group["reviewState"] == "已按题册原图与讲义逐题复核"

    answer_snapshots = {
        "p05-g2": [("原癌基因", "BGI"), ("抑癌基因", "ADEFHK"), ("错配修复基因", "CJ"), ("与大肠癌关系最密切的三个基因", "FBD"), ("与遗传性腺瘤性息肉病相关的基因", "F"), ("与遗传性非息肉病性大肠癌/Lynch综合征相关的基因", "C")],
        "p06-g2": [("急性感染性心内膜炎", "ADFHIKLM"), ("亚急性感染性心内膜炎", "BCDEGJM")],
        "p08-g3": [("扩张型心肌病", "BEGIKMO"), ("肥厚型心肌病", "ADHJLN"), ("限制型心肌病", "CF")],
        "p11-g1": [("慢性淋巴细胞性/自身免疫性甲状腺炎/桥本", "AFHJLMN"), ("亚急性/肉芽肿性/巨细胞性甲状腺炎", "BCDEGIKO")],
        "p11-g2": [("结节性甲状腺肿", "ACFHI"), ("甲状腺腺瘤", "BDEGI")],
        "p11-g3": [("单纯性/弥漫性非毒性甲状腺肿", "AJK"), ("弥漫性毒性甲状腺肿（Graves病）", "BDEF"), ("慢性淋巴细胞性/自身免疫性甲状腺炎/桥本", "BCD"), ("亚急性/肉芽肿性/巨细胞性甲状腺炎", "GHI")],
        "p13-g2": [("超急性排斥反应", "ADF"), ("急性排斥反应", "BE"), ("慢性排斥反应", "C")],
        "p13-g3": [("I型速发型", "ADH"), ("II型细胞毒型", "BCEGKMQRU"), ("III型免疫复合物/血管炎型", "FINST"), ("IV型迟发型", "JLOPV")],
        "p14-g3": [("宫颈癌0期", "H"), ("宫颈癌I期", "ADI"), ("宫颈癌II期", "BF"), ("宫颈癌III期", "CG"), ("宫颈癌IV期", "E"), ("早期/微小浸润癌", "AI"), ("浸润癌", "ABCDEFGI"), ("原位癌", "H")],
        "p16-g2": [("上皮性肿瘤", "ACDGO"), ("由卵母细胞发生的生殖细胞肿瘤", "BEHJL"), ("由卵泡细胞发生的性索间质肿瘤", "FIKMN")],
        "p17-g3": [("粒层细胞瘤/颗粒细胞瘤", "ACE"), ("卵泡膜细胞瘤", "BDE")],
        "p17-g4": [("前列腺增生/肥大", "BEG"), ("前列腺癌", "ACDFG")],
        "p19-g2": [("原发性肺结核", "ACEHKNP"), ("继发性肺结核", "BDFGIJLMOQ")],
        "p21-g1": [("流行性脑脊髓膜炎", "AEHILMS"), ("流行性乙型脑炎", "BCDFGJKNOPQR")],
        "p21-g2": [("细菌性痢疾", "A"), ("中毒性痢疾", "B")],
        "p23-g1": [("肠结核", "A"), ("肠伤寒", "F"), ("细菌性痢疾", "B"), ("阿米巴", "G"), ("溃疡性结肠炎", "H"), ("克罗恩病", "C"), ("消化性溃疡", "I"), ("胃癌溃疡型", "J"), ("胃泌素瘤", "K"), ("应激性溃疡", "E")],
        "p23-g2": [("肠结核", "A"), ("肠伤寒", "F"), ("细菌性痢疾", "B"), ("阿米巴", "G"), ("溃疡性结肠炎", "H"), ("克罗恩病", "C"), ("消化性溃疡", "I"), ("胃癌溃疡型", "D"), ("胃泌素瘤", "J"), ("应激性溃疡", "E")],
        "p24-g3": [("一期愈合", "ABDFIJM"), ("二期愈合", "CEGHKLN")],
        "p25-g1": [("适应", "BDFOQ"), ("可逆性损伤", "ACEGNPR"), ("意外性细胞死亡", "HJLSUW"), ("调节性细胞死亡", "IKMTV")],
        "p26-g3": [("营养不良性钙化", "ABCFHJLO"), ("转移性钙化", "DEGIKNPM")],
        "p26-g4": [("细胞内", "AB"), ("细胞内、间质", "CFG"), ("间质", "DE")],
        "p27-g2": [("凝固性坏死", "ACFM⑥"), ("液化性坏死", "BDORV⑤"), ("干酪样坏死", "EJP"), ("脂肪坏死（特殊的液化性坏死）", "KSW"), ("纤维素/纤维蛋白样坏死（旧称纤维素/纤维蛋白样变性）", "GHILNQTUXY①③"), ("坏疽", "②④")],
        "p28-g1": [("干性坏疽", "ADHJM"), ("湿性坏疽", "BEFKL"), ("气性坏疽", "CEGIL")],
        "p30-g1": [("慢性左心衰", "ADEF"), ("大叶性肺炎", "BCGH")],
        "p30-g2": [("白色血栓", "ADKNRT"), ("混合血栓", "CILMPUVW"), ("红色血栓", "BEHO"), ("纤维素性血栓", "FGJQSX")],
        "p31-g1": [("变质性炎", "ACEH"), ("渗出性炎", "BDFGIJKLNOPQSTUVWZ②"), ("增生性炎", "MRX①"), ("浆液性炎", "BDFJ"), ("纤维素性炎", "GNPS"), ("化脓性炎", "IKOQUWZ"), ("出血性炎", "LTV②")],
        "p32-g1": [("Langhans巨细胞", "ACEG"), ("异物巨细胞", "BDF")],
        "p32-g3": [("结核", "ABE"), ("风湿病", "CDG"), ("伤寒", "FHJ"), ("梅毒III期", "IMN"), ("慢性血吸虫虫卵", "AOP")],
        "p33-g1": [("良性肿瘤", "AEFGIMNOSU"), ("恶性肿瘤", "BCDGHJLPQRT")],
        "p35-g2": [("P53", "ABE"), ("APC", "FGJ"), ("RB", "HM"), ("BRCA", "CI"), ("NF", "DK"), ("WT", "L"), ("VHL", "N")],
        "p36-g1": [("PDGF", "AC"), ("RAS", "EFHJK①"), ("BRAF", "N②"), ("ABL", "BI③"), ("ERBB2/HER2", "DGJQ③"), ("KIT", "MR③"), ("c-MYC", "O"), ("MYC", "S"), ("CyclinD1", "KT")],
        "p36-g2": [("生长因子", "A"), ("信号转导蛋白", "CFI"), ("生长因子受体", "BE"), ("转录因子", "GH"), ("细胞周期调节蛋白", "D")],
        "p37-g2": [("原癌基因", "ACEGJLNOP"), ("抑癌基因", "BDFHIKM")],
    }
    for group_id, expected in answer_snapshots.items():
        assert_answers(group_id, expected)
    assert "I" in "".join(groups_by_id["p16-g2"]["stems"][2]["answer"])
    assert "I" in "".join(groups_by_id["p36-g2"]["stems"][1]["answer"])

    respiratory_ids = [
        group["id"] for group in payload["groups"] if group["topic"] == "呼吸系统"
    ]
    assert respiratory_ids == [
        "p09-g1", "p09-g2", "p09-g3",
        "p10-g1", "p10-g2", "p10-g3", "p10-g4",
    ]

    assert_group(
        "p09-g2",
        [
            ("A", "中性粒细胞活跃导致内源性弹性蛋白酶增多"),
            ("B", "破坏终末细支气管、一级呼吸性细支气管的管壁结构，导致管壁纤维化和管腔狭窄"),
            ("C", "纤毛柱状上皮受损和鳞化导致黏液潴留"),
            ("D", "氧自由基增多导致α1-抗胰蛋白酶减少"),
            ("E", "柱状细胞增多、腺体增生肥大、黏液腺化生，导致呼吸道黏液增多"),
        ],
        [("与细支气管不完全阻塞有关", "BCE"), ("与末梢肺组织弹性减弱有关", "AD")],
    )
    assert_group(
        "p09-g3",
        [
            ("A", "肋骨骨折"), ("B", "腺泡中央型"),
            ("C", "代偿性肺气肿"), ("D", "胸部穿透伤"),
            ("E", "老年性肺气肿"), ("F", "腺泡周围型"),
            ("G", "剧烈咳嗽"), ("H", "全腺泡型"),
            ("I", "瘢痕旁肺气肿（不规则肺气肿）"),
            ("J", "串珠状气泡"), ("K", "皮下气肿"),
        ],
        [("肺泡性/阻塞性肺气肿", "BFH"), ("间质性肺气肿", "ADGJK"), ("其他类型肺气肿", "CEI")],
    )
    assert "I" in "".join(groups_by_id["p09-g3"]["stems"][2]["answer"])
    assert_group(
        "p10-g1",
        [
            ("A", "属于肺泡性/阻塞性肺气肿"), ("B", "瘢痕牵拉"),
            ("C", "累及肺腺泡的结构不定，主要累及肺泡"),
            ("D", "属于其他类型肺气肿"),
            ("E", "累及腺泡远端的所有结构（肺泡管/肺泡囊），即腺泡远端肺气肿"),
        ],
        [("瘢痕旁/不规则肺气肿", "BCD"), ("腺泡周围型/间隔旁型肺气肿", "ABE")],
    )
    assert_group(
        "p10-g2",
        [
            ("A", "军团菌肺炎"), ("B", "病毒性肺炎"),
            ("C", "大叶性肺炎"), ("D", "支原体肺炎"),
            ("E", "小叶性/支气管肺炎"), ("F", "衣原体肺炎"),
        ],
        [("细菌性肺炎", "ACE"), ("间质性肺炎", "BDF")],
    )
    assert_group(
        "p10-g3",
        [
            ("A", "肺泡的纤维素性炎"),
            ("B", "细支气管及末梢肺组织的化脓性炎"),
            ("C", "可呈小叶、大叶等分布"),
            ("D", "以细支气管为中心"),
            ("E", "纤维素性化脓性炎"),
        ],
        [("大叶性肺炎", "A"), ("小叶性/支气管肺炎", "BD"), ("军团菌肺炎", "CE")],
    )
    assert_group(
        "p10-g4",
        [("A", "胞核+胞质"), ("B", "胞质（嗜酸性）"), ("C", "胞核（嗜碱性）")],
        [
            ("单纯疱疹病毒", "C"), ("呼吸道合胞病毒", "B"),
            ("麻疹病毒", "A"), ("腺病毒", "C"), ("巨细胞病毒", "C"),
        ],
    )

    assert_group(
        "p33-g1",
        [
            ("A", "分化相对好（异型性相对小）"),
            ("B", "核分裂象多，可见病理性核分裂象"),
            ("C", "多不规则、边界不清（无包膜）"),
            ("D", "甲状腺滤泡癌"), ("E", "出血、坏死少见"),
            ("F", "多生长缓慢，膨胀性生长"),
            ("G", "体表肿瘤、体腔肿瘤、管道器官腔面、骨软骨瘤可呈外生性生长"),
            ("H", "多复发"), ("I", "不转移"), ("J", "常有副肿瘤综合症"),
            ("L", "分化差（异型性大）"),
            ("M", "核分裂象无或少，无病理性核分裂象"),
            ("N", "多规则、边界较清楚（包膜完整）"),
            ("O", "子宫平滑肌瘤"), ("P", "大量淋巴细胞浸润的乳腺髓样癌"),
            ("Q", "出血、坏死、溃疡形成等多见"),
            ("R", "多生长迅速，浸润性生长"), ("S", "少复发"),
            ("T", "会转移"), ("U", "没有副肿瘤综合症"),
        ],
        [("良性肿瘤", "AEFGIMNOSU"), ("恶性肿瘤", "BCDGHJLPQRT")],
    )

    print({
        "groups": len(payload["groups"]),
        "stems": sum(len(group.get("stems", [])) for group in payload["groups"]),
        "lectures": len(payload["lectures"]),
        "status": "ok",
    })


if __name__ == "__main__":
    main()
