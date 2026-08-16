#!/usr/bin/env python3
"""Build the surgery question payload from the scanned workbook.

The surgery workbook is split into compact horizontal question bands. Each band
usually contains a shared option bank on the left and one or more blue prompts
with answer bubbles on the right. OCR is treated as an extraction aid: answers
that cannot be reconciled with the visible option keys are kept as unresolved
instead of being guessed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image

import build_med_content as shared


RIGHT_X = 420
PAGE_WIDTH = 767
KEY_SEQUENCE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")

TOPICS = [
    "颈部疾病",
    "乳房疾病",
    "胸部疾病",
    "胃十二指肠疾病",
    "腹部损伤与感染",
    "小肠与阑尾疾病",
    "结直肠与肛管疾病",
    "腹外疝",
    "肝胆胰疾病",
    "周围血管疾病",
    "泌尿外科",
]

PAGE_TOPIC = {
    1: "颈部疾病", 2: "颈部疾病",
    3: "乳房疾病", 4: "乳房疾病", 5: "乳房疾病",
    6: "胸部疾病", 7: "胃十二指肠疾病",
    8: "腹部损伤与感染", 9: "小肠与阑尾疾病",
    10: "小肠与阑尾疾病", 11: "小肠与阑尾疾病",
    12: "结直肠与肛管疾病", 13: "结直肠与肛管疾病",
    14: "腹外疝", 15: "腹外疝", 16: "腹外疝",
    17: "肝胆胰疾病", 18: "肝胆胰疾病", 19: "肝胆胰疾病",
    20: "肝胆胰疾病", 21: "肝胆胰疾病", 22: "肝胆胰疾病",
    23: "肝胆胰疾病", 24: "周围血管疾病",
    25: "周围血管疾病", 26: "泌尿外科", 27: "泌尿外科",
    28: "泌尿外科", 29: "泌尿外科",
}

# Page 3 starts with the final thyroid group before moving into breast disease.
SEGMENT_TOPIC_OVERRIDES = {(3, 1): "颈部疾病"}

LECTURE_IDS = {
    "颈部疾病": ["lecture-01"],
    "乳房疾病": ["lecture-03"],
    "胸部疾病": ["lecture-02", "lecture-04"],
    "胃十二指肠疾病": ["lecture-05"],
    "腹部损伤与感染": ["lecture-06", "lecture-07"],
    "小肠与阑尾疾病": ["lecture-08", "lecture-09"],
    "结直肠与肛管疾病": ["lecture-10", "lecture-11"],
    "腹外疝": ["lecture-12"],
    "肝胆胰疾病": ["lecture-13", "lecture-14", "lecture-15", "lecture-16"],
    "周围血管疾病": ["lecture-17"],
    "泌尿外科": ["lecture-18", "lecture-19"],
}

NOISE = ("小红书", "385106504", "beautiful things", "Daily Reminder", "It's time")

# These repairs were transcribed from the 300 dpi source pages after the first
# OCR pass. They cover compact answer bubbles, vertical table answers, and the
# few bands containing more than one logical option bank.
MANUAL_STEMS = {
    "p01-g3": [("I期", "B"), ("II期", "A")],
    "p02-g3": [("喉上神经内支", "E"), ("喉上神经外支", "B"), ("一侧喉返神经", "G"),
                ("双侧喉返神经", "DH"), ("颈交感神经 Horner 综合征", "ACFI")],
    "p03-g4": [("T0", "A"), ("T1", "C"), ("T2", "E"), ("T3", "H"), ("T4", "BDGI")],
    "p04-g1": [("N0", "B"), ("N1", "AE"), ("N2", "AD"), ("N3", "C")],
    "p04-g4": [("凹陷（酒窝征）", "B"), ("水肿（橘皮样变）", "C"), ("卫星结节", "A")],
    "p04-g5": [("筛查", "D"), ("金标准", "A"), ("CA153", "C"),
                ("抑癌基因、乳腺癌易感基因缺陷", "E"), ("放射性核素骨扫描 ECT", "B")],
    "p04-g6": [("I腋下组", "B"), ("II腋中组", "C"), ("III腋上组", "A")],
    "p05-g1": [("改良根治术", "BD"), ("扩大根治术", "F"),
                ("全乳房切除术（不清扫淋巴结）", "AEI"), ("保乳乳腺癌切除术", "BCJ"),
                ("淋巴结清扫：腋淋巴结阳性", "G"), ("淋巴结清扫：腋淋巴结阴性", "H")],
    "p05-g2": [("乳腺癌", "EHJNQ"), ("乳腺纤维腺瘤", "AFJMP"), ("乳腺囊性增生病", "DL"),
                ("急性乳腺炎", "BGKO"), ("乳管内乳头状瘤", "I"),
                ("浆细胞乳腺炎（无菌性炎症）：急性炎症表现", "H"),
                ("浆细胞乳腺炎（无菌性炎症）：慢性炎症表现", "C")],
    "p05-g3": [("乳腺癌", "C"), ("正常月经", "F"), ("感染", "D"), ("乳腺囊性增生病", "B"),
                ("早期妊娠", "F"), ("乳管内乳头状瘤", "C"), ("若乳管阻塞", "A")],
    "p06-g1": [("前纵隔", "BDF"), ("前上纵隔", "DF"), ("中纵隔", "ACG"), ("后纵隔", "E")],
    "p06-g2": [("I型", "D"), ("II型", "A"), ("III型", "C"), ("IV型", "B"),
                ("边界清楚", "AD"), ("最常见", "C"), ("预后最差", "B")],
    "p06-g3": [("内镜", "D"), ("超声内镜", "B"), ("筛查", "C"),
                ("判断预后、监测复发、辅助诊断", "A"), ("CT/MRI", "E")],
    "p07-g1": [("Tis", "F"), ("T1a", "D"), ("T1b", "B"), ("T2", "G"),
                ("T3", "A"), ("T4a", "C"), ("T4b", "E")],
    "p08-g2": [("脾", "ADMVY"), ("肝", "AEFHc"), ("空回肠", "BEHLQW"),
                ("十二指肠2/3部", "BCGHKNPT"), ("胰腺", "ACIJO"), ("结肠", "BCQR"),
                ("少数污染轻（多为右半结肠损伤）", "X"), ("大多污染重（多为左半结肠损伤）", "a"),
                ("直肠上段损伤", "BCQRZ"), ("直肠下段损伤", "SUb")],
    "p09-g3": [("完全性肠梗阻", "A"), ("不完全性肠梗阻", "B")],
    "p09-g4": [("高位（空肠）", "DE"), ("回肠", "AC"), ("大肠", "AB")],
    "p10-g1": [("闭袢性梗阻", "ACEGI")],
    "p10-g3": [("结肠充气试验（Rovsing征）", "A"), ("腰大肌试验（Psoas征）", "CE"),
                ("闭孔内肌试验（Obturator征）", "BD")],
    "p11-g1": [("单纯性", "ABEGI"), ("化脓性", "BDG"), ("脓液少", "EI"),
                ("脓液多", "FH"), ("坏疽穿孔性", "CFGHK"), ("妊娠期", "GIJL")],
    "p11-g3": [("右半结肠切除术", "BFG"), ("横结肠切除术", "C"),
                ("左半结肠切除术", "AE"), ("乙状结肠切除术", "D")],
    "p12-g1": [("右半结肠癌并发急性肠梗阻", "C"), ("左半结肠癌：先解决梗阻", "B"),
                ("左半结肠癌：具备一期吻合条件", "A"), ("左半结肠癌：肠管扩张、水肿明显", "D")],
    "p12-g2": [("Miles术", "A"), ("Dixon术", "C"), ("Hartmann术", "EF")],
    "p12-g3": [("Miles术", "A"), ("Dixon术", "B")],
    "p13-g1": [("I度", "A"), ("II度", "AD"), ("III度", "AC"), ("IV度", "AB")],
    "p13-g2": [("内痔截石位", "D"), ("内痔膝胸位", "B"), ("肛裂截石位", "C"), ("肛裂膝胸位", "A")],
    "p13-g5": [("直肠癌", "EGI"), ("直肠息肉", "ACF"), ("痔（内痔）", "H"),
                ("肛瘘", "B"), ("盆腔脓肿", "J"), ("肛裂", "D")],
    "p14-g2": [("前", "BD"), ("后", "ACG"), ("上", "DH"), ("下", "FI")],
    "p14-g3": [("内侧", "B"), ("底部", "C"), ("外侧", "A")],
    "p15-g1": [("Richter疝（肠管壁疝）", "B"), ("Littre疝", "A"),
                ("Maydl疝（逆行性嵌顿疝）", "EC"), ("Amyand疝", "D")],
    "p15-g4": [("Bassini", "B"), ("McVay", "ADF"), ("Shouldice", "CE")],
    "p16-g2": [("1岁内", "D"), ("1岁后", "A"), ("2岁前", "E"),
                ("睾丸萎缩且对侧睾丸正常", "B"), ("双侧睾丸不能下降", "C")],
    "p18-g2": [("断流术", "ACFGJOP"), ("分流术", "BEIN"), ("选择性分流术", "GM"), ("非选择性分流术", "HDKL")],
    "p18-g4": [("胰头癌", "BDFGH"), ("壶腹癌", "ADFGIK"), ("十二指肠癌", "BDFGJ"),
                ("上段胆管癌", "ACH"), ("中下段胆管癌", "ADFGH"), ("胆总管结石", "EI")],
    "p19-g1": [("纯胆固醇结石", "CFG"), ("混合性结石", "BDG"),
                ("黑色素结石", "AHIK"), ("棕色结石", "EHJK"),
                ("碳酸钙、磷酸钙、棕榈酸钙等", "B")],
    "p19-g2": [("原发性肝外胆管结石多为", "B"), ("继发性肝外胆管结石主要来自", "C"),
                ("继发性肝外胆管结石少数来自", "A")],
    "p19-g3": [("胆囊结石", "E"), ("急性胆囊炎", "B"), ("胆囊癌", "D"), ("胆管扩张", "C"), ("胆管蛔虫", "A")],
    "p19-g5": [("结石：首选", "A"), ("结石：最佳", "C"), ("感染：首选", "A"), ("感染：最佳", "C"),
                ("严重感染：首选", "A"), ("严重感染：最快", "B"), ("严重感染：最全面", "C"),
                ("肿瘤：首选", "A"), ("肿瘤：评估分期", "BC")],
    "p20-g1": [("PTC检查后引流", "B"), ("ERCP检查后引流", "A"), ("胆总管探查后引流", "C")],
    "p20-g3": [("胆囊结石", "AHJ"), ("有症状的胆囊结石", "O"), ("急性结石性胆囊炎", "BEI"),
                ("急性结石性胆囊炎≤3天", "N"), ("急性结石性胆囊炎>3天", "S"),
                ("肝内胆管结石及炎症", "CHK"), ("无症状、小的肝内胆管结石", "P"),
                ("有症状的肝内胆管结石", "R"), ("肝外胆管结石及炎症", "FL"),
                ("急性梗阻性化脓性胆管炎（AOSC）", "DGMQT")],
    "p21-g2": [("经十二指肠内镜取石", "C"), ("胆总管切开取石+T管引流", "E"),
                ("内镜下Oddi括约肌切开术（EST）+取石术+鼻胆管引流术（ENBD，治疗性ERCP）", "A"),
                ("胆管-空肠Roux-en-Y吻合术（胆汁内引流术）+切胆囊", "BDF")],
    "p21-g4": [("I型", "C"), ("II型", "B"), ("III型", "D"), ("IV型", "A")],
    "p22-g1": [("I型", "C"), ("II型", "B"), ("III型", "A"), ("最常见", "A")],
    "p22-g2": [("尚有部分肝外胆管通畅、胆囊大小正常", "B"), ("肝门部胆管闭锁、但肝内仍有胆管腔", "D"),
                ("肝移植的适应证", "ACE")],
    "p22-g3": [("I型", "D"), ("II型", "E"), ("III型", "A"), ("IV型", "B"),
                ("V型/Caroli病", "CF"), ("最常见", "D")],
    "p23-g1": [("胆囊结石", "CKP"), ("急性胆囊炎", "ANQ"), ("胆囊癌", "BLTa"),
                ("肝内胆管结石及炎症", "AJV"), ("肝外胆管结石及炎症", "EX"), ("胆管癌", "GU"),
                ("上段胆管癌", "M"), ("中下段胆管癌", "O"), ("胆管蛔虫", "ARd"),
                ("胆管闭锁", "FWZ"), ("先天性胆管扩张症", "DSe"), ("胰头癌", "GHOYb"),
                ("壶腹癌", "EOb"), ("十二指肠癌", "HIOb")],
    "p23-g2": [("AOSC", "F"), ("LC", "C"), ("PTGD", "I"), ("PTCD", "A"),
                ("MRCP", "E"), ("治疗性ERCP", "H"), ("Whipple术", "B"), ("Courvoisier征", "D")],
    "p24-g1": [("I期", "D"), ("II期", "B"), ("III期", "A"), ("IV期", "C")],
    "p24-g2": [("Rutherford 1级", "D"), ("Rutherford 2级", "F"), ("Rutherford 3级", "C"),
                ("Rutherford 4级", "B"), ("Rutherford 5级", "A"), ("Rutherford 6级", "E")],
    "p24-g4": [("周围型：局限在股静脉", "D"), ("周围型：局限在小腿深静脉", "AF"),
                ("中央型", "B"), ("混合型", "CEG")],
    "p25-g1": [("Buerger试验", "ADH"), ("Trendelenburg试验", "F"), ("Pratt试验", "B"),
                ("Perthes试验", "G"), ("Homans征", "CI")],
    "p26-g3": [("没有突破基底膜、也没有突出黏膜表面", "C"),
                ("非浸润性乳头状癌", "E"),
                ("侵犯固有层或黏膜下层", "A"), ("侵犯肌层", "D"),
                ("原位癌／非浸润癌", "CE"),
                ("非肌层浸润的膀胱移行细胞癌", "ACE"),
                ("肌层浸润的膀胱移行细胞癌", "BDF")],
    "p26-g5": [("泌尿外科感染", "G"), ("肾癌最佳检查", "DH"), ("泌尿外科肿瘤首选检查", "G"),
                ("膀胱癌最佳检查", "E"), ("怀疑前列腺癌骨转移（经椎旁静脉系统）首选", "A"),
                ("上尿路癌最佳检查", "DH"), ("决定肾结核治疗必不可少", "C"),
                ("前列腺癌最佳检查", "E"), ("分肾功能", "BCD")],
    "p27-g1": [("全程血尿", "AEG"), ("初始血尿", "C"), ("终末血尿", "BDFHI")],
    "p27-g3": [("膀胱癌", "CF"), ("Tis、Ta、T1", "O"), ("T2、T3、T4", "Q"),
                ("上尿路癌", "CHJN"), ("肾癌（肾腺癌）", "AGIM"), ("前列腺癌", "BDKL"),
                ("前列腺癌局限在前列腺", "P"), ("前列腺癌突破前列腺", "R")],
    "p28-g1": [("草酸钙", "BFILMO"), ("磷酸钙", "AEHLNO"),
                ("尿酸盐", "BCGJP"), ("胱氨酸", "BCDKP")],
    "p28-g2": [("尿路结石", "BFGI"), ("草酸钙", "D"), ("磷酸钙", "D"),
                ("尿酸盐", "J"), ("胱氨酸", "J"), ("胆系结石", "ACHK"),
                ("纯胆固醇结石", "J"), ("混合性结石", "D"), ("胆色素结石", "E")],
    "p28-g3": [("若肾功能极差", "E"), ("多发结石：双侧肾结石", "C"),
                ("多发结石：双侧输尿管结石", "A"), ("多发结石：一侧肾结石、一侧输尿管结石", "F"),
                ("结石<0.6cm", "G"), ("膀胱结石尤其<2cm", "B"), ("尿道结石", "D"),
                ("前尿道结石", "I"), ("后尿道结石", "H")],
    "p29-g2": [("腹膜外型膀胱破裂", "ACEGI"), ("腹膜内型膀胱破裂", "BDFH")],
    "p29-g3": [("肾挫伤", "B"), ("肾裂伤", "A"), ("肾蒂损伤", "C")],
    "p29-g4": [("持续性尿失禁", "CGJ"), ("充溢性尿失禁", "ABDH"),
                ("急迫性尿失禁", "EI"), ("压力性尿失禁", "FK")],
}

MANUAL_OPTIONS = {
    "p12-g2": [
        ("A", "腹膜返折以下/距肛缘<7cm/距齿状线<5cm"),
        ("B", "腹膜返折以下/距肛缘≤7cm/距齿状线≤5cm"),
        ("C", "腹膜返折以上/距肛缘≥7cm/距齿状线≥5cm"),
        ("D", "腹膜返折以上/距肛缘>7cm/距齿状线>5cm"),
        ("E", "急性肠梗阻不宜行Dixon术"),
        ("F", "不耐受Miles术"),
    ],
    "p12-g4": [
        ("A", "肛管"), ("B", "来源内胚层"), ("C", "皮肤，相对不易破裂"),
        ("D", "肛管动脉"), ("E", "直肠上静脉→门静脉"),
        ("F", "腹股沟浅淋巴结"), ("G", "直肠上动脉（主要）"),
        ("H", "内脏（交感、副交感），痛觉不敏感"), ("I", "鳞癌"),
        ("J", "直肠"), ("K", "来源于外胚层"), ("L", "黏膜，易破裂出血"),
        ("M", "骶正中动脉"), ("N", "直肠下静脉和肛管静脉→下腔静脉"),
        ("O", "肠系膜下动脉旁和髂内淋巴结"), ("P", "直肠下动脉"),
        ("Q", "躯体（阴部神经），痛觉敏感"), ("R", "腺癌"),
        ("S", "内痔"), ("T", "外痔"),
    ],
    "p14-g1": [
        ("A", "腔隙韧带（腹股沟韧带的延伸结构）"),
        ("B", "耻骨梳/Cooper韧带（腹股沟韧带的延伸结构）"),
        ("C", "腹股沟韧带"), ("D", "股血管"),
    ],
    "p14-g2": [
        ("A", "腹股沟镰（腹内斜肌和腹横肌腱膜构成的联合腱）"),
        ("B", "腹外斜肌腱膜（主要）"), ("C", "腹横筋膜"),
        ("D", "腹内斜肌"), ("F", "腹股沟韧带（腹外斜肌腱膜卷曲形成）"),
        ("G", "腹膜"), ("H", "腹横肌"), ("I", "腔隙韧带"),
    ],
    "p15-g1": [
        ("A", "嵌顿内容物为小肠憩室，如Meckel憩室"),
        ("B", "嵌顿内容物仅为部分肠管壁，局部肿块不明显，多无肠梗阻，易误诊"),
        ("C", "即使疝囊内肠管存活，也必须将腹腔内相关肠袢牵出检查，以防遗漏隐匿在腹腔内的坏死肠袢"),
        ("D", "嵌顿内容物为阑尾，常感染化脓（appendix）"),
        ("E", "嵌顿肠管包括几个肠袢，呈W形"),
    ],
    "p15-g2": [
        ("A", "＞1岁婴幼儿"), ("B", "＜1岁"), ("C", "＜2岁脐疝"),
        ("D", "绞窄疝"), ("E", "不耐受手术"),
    ],
    "p16-g1": [
        ("A", "中老年肥胖女性多见"), ("B", "好发老年男性"),
        ("C", "包块在腹股沟韧带上方"), ("D", "疝块小呈半球形"),
        ("E", "半球形、基底较宽"), ("F", "多进入阴囊/大阴唇"),
        ("G", "偶尔进入阴囊/大阴唇"), ("H", "绝对不进入阴囊/大阴唇"),
        ("I", "咳嗽冲击感不明显"), ("J", "回纳疝块后压住内口疝块不再突出"),
        ("K", "回纳疝块后压住内口疝块仍可突出"), ("L", "咳嗽冲击感多明显"),
        ("M", "易嵌顿"), ("N", "最易嵌顿"),
        ("O", "疝囊颈在腹壁下动脉外侧"), ("P", "疝囊颈在腹壁下动脉内侧"),
        ("Q", "精索/子宫圆韧带在疝囊后方"), ("R", "精索/子宫圆韧带在疝囊前外方"),
        ("S", "好发儿童、青年男性"), ("T", "包块在腹股沟韧带下方"),
        ("U", "椭圆或梨形、呈蒂柄状"), ("V", "不易嵌顿"),
    ],
    "p16-g2": [
        ("A", "短期用hCG"), ("B", "切除未降睾丸"),
        ("C", "睾丸自体移植术"), ("D", "自行下降"), ("E", "睾丸固定术"),
    ],
    "p19-g1": [
        ("A", "质地硬、杂质少"), ("B", "X线常显影"),
        ("C", "剖面呈放射状"), ("D", "剖面呈放射状、层状"),
        ("E", "质地软、杂质多"), ("F", "X线常不显影"),
        ("G", "胆固醇类结石"), ("H", "胆色素结石"),
        ("I", "几乎在胆囊"), ("J", "多在胆管"),
        ("K", "X线部分显影"),
    ],
    "p23-g2": [
        ("A", "经皮穿刺进入肝内胆管，置管减压并持续引流"),
        ("B", "联合切除胰头、十二指肠及相关胆道等组织的根治性术式"),
        ("C", "经腹腔镜切除胆囊"),
        ("D", "深吸气时触及无痛、光滑、肿大的胆囊：见于中下段胆管癌、胰头癌、壶腹癌、十二指肠癌"),
        ("E", "利用磁共振水成像无创显示胰胆管形态"),
        ("F", "胆管急性梗阻并发化脓性感染，典型可出现Reynolds五联征"),
        ("G", "经十二指肠镜逆行插管造影以观察胰胆管"),
        ("H", "内镜下切开Oddi括约肌并取石，术后留置鼻胆管引流"),
        ("I", "经皮穿刺进入胆囊，置管减压并持续引流"),
    ],
    "p28-g1": [
        ("A", "易碎"), ("B", "硬"), ("C", "光滑"), ("D", "蜡样"),
        ("E", "鹿角样"), ("F", "桑葚样"), ("G", "颗粒状"), ("H", "灰白色"),
        ("I", "棕褐色"), ("J", "红色"), ("K", "黄色"), ("L", "糙"),
        ("M", "最常见"), ("N", "酸化尿液+抗感染"),
        ("O", "X线高密度"), ("P", "X线不显影"),
    ],
    "p29-g4": [
        ("A", "尿液不连续从尿道口不自主流出、呈滴沥样、夜间多见"),
        ("B", "假性尿失禁"),
        ("C", "完全失去控制排尿的能力，任何时间、体位下尿液均会持续不自主从尿道口流出"),
        ("D", "患者每次排尿时尿液都难以排尽、膀胱内残余尿逐渐增多、膀胱过度充盈导致膀胱内压超过尿道阻力"),
        ("E", "多见于膀胱炎、神经源性膀胱、重度膀胱出口梗阻引起的膀胱不稳定收缩"),
        ("F", "平常控制排尿能力正常，但咳嗽、起立等腹内压增加时少量尿液不自主从尿道口流出"),
        ("G", "多见于外伤、手术、先天性疾病引起的膀胱颈和尿道括约肌损伤"),
        ("H", "多见于前列腺增生、肿瘤、尿道狭窄等下尿路慢性梗阻或神经系统疾病导致膀胱逼尿肌收缩无力"),
        ("I", "严重的尿频、尿急而膀胱不受意识控制就开始排尿"),
        ("J", "真性尿失禁"),
        ("K", "多见于多产妇、绝经后引起的阴道前壁支撑力下降和盆腔组织功能障碍或前列腺手术后引起的尿道外括约肌损伤"),
    ],
}

MANUAL_TITLES = {
    "p02-g3": "甲状腺手术神经损伤表现",
    "p03-g4": "乳腺癌T分期", "p04-g1": "乳腺癌N分期", "p04-g4": "乳腺癌皮肤表现",
    "p04-g6": "腋窝淋巴结分组", "p06-g2": "胃癌Borrmann分型", "p07-g1": "胃癌T分期",
    "p09-g3": "肠梗阻完全性", "p09-g4": "肠梗阻部位",
    "p11-g1": "急性阑尾炎分型", "p12-g2": "直肠癌术式与适应证",
    "p12-g3": "直肠癌术式与肛门括约肌", "p13-g1": "内痔分度",
    "p14-g1": "股管结构", "p14-g2": "腹股沟管结构",
    "p14-g3": "直疝三角/海氏三角/Hesselbach 三角", "p14-g4": "疝的组成",
    "p14-g5": "腹外疝临床分型", "p14-g6": "腹外疝类型与常见内容物",
    "p15-g1": "特殊类型嵌顿疝", "p15-g2": "腹外疝治疗方式",
    "p15-g3": "腹股沟疝修补术式", "p15-g4": "传统疝修补术特点",
    "p16-g1": "股疝、斜疝与直疝鉴别", "p16-g2": "隐睾（阴囊空虚感）治疗",
    "p18-g4": "胰头癌与胆道肿瘤鉴别", "p19-g5": "胆系疾病影像检查",
    "p20-g3": "胆石症与胆道感染", "p21-g4": "上段/肝门部胆管癌Bismuth-Corlette分型",
    "p23-g2": "胆系疾病英文缩写", "p24-g1": "周围动脉疾病分期",
    "p24-g2": "Rutherford分级", "p25-g1": "周围血管疾病检查",
    "p26-g3": "膀胱癌T分期", "p27-g1": "血尿出现时相与病变部位",
    "p27-g3": "泌尿系肿瘤", "p28-g1": "泌尿系结石成分与特点",
    "p28-g2": "尿路结石与胆系结石鉴别",
    "p29-g2": "膀胱破裂类型", "p29-g4": "尿失禁类型",
}

SKIP_GROUPS = {"p04-g2", "p04-g3", "p16-g3", "p16-g4", "p16-g5"}
SOURCE_VERIFIED_OPTION_GAPS = {"p06-g4", "p09-g1", "p14-g2", "p17-g1"}
SOURCE_VERIFIED_HERNIA_GROUPS = {
    "p14-g1", "p14-g2", "p14-g3", "p14-g4", "p14-g5", "p14-g6",
    "p15-g1", "p15-g2", "p15-g3", "p15-g4", "p16-g1", "p16-g2",
}


def clean_text(text: str) -> str:
    text = text.replace("ttsx", "").replace("天天师兄", "")
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"(?<=[A-Za-z])\s+(?=[A-Za-z])", "", text)
    text = re.sub(r"\s*([，。；：、！？）】》〉])\s*", r"\1", text)
    text = re.sub(r"\s*([（【《〈])\s*", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" |")
    return text


def load_ocr(path: Path) -> dict[int, list[dict]]:
    pages = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        scale = PAGE_WIDTH / float(data.get("width") or PAGE_WIDTH)
        rows = []
        for row in data.get("rows", []):
            box = row.get("box") or []
            if not box:
                continue
            text = clean_text(row.get("text", ""))
            if not text or any(item in text for item in NOISE):
                continue
            scaled_box = [
                [float(point[0]) * scale, float(point[1]) * scale]
                for point in box
            ]
            rows.append({
                "text": text,
                "x": scaled_box[0][0],
                "y": scaled_box[0][1],
                "box": scaled_box,
                "score": float(row.get("score", 0)),
            })
        pages[int(data["page"])] = sorted(rows, key=lambda row: (row["y"], row["x"]))
    return pages


def divider_rows(image_path: Path) -> list[int]:
    image = Image.open(image_path).convert("L")
    width, height = image.size
    dark_rows = []
    pixels = image.load()
    for y in range(height):
        count = sum(1 for x in range(5, width - 5) if pixels[x, y] < 80)
        if count > width * 0.65:
            dark_rows.append(y)
    runs: list[list[int]] = []
    for y in dark_rows:
        if not runs or y > runs[-1][-1] + 1:
            runs.append([y])
        else:
            runs[-1].append(y)
    return [round(sum(run) / len(run)) for run in runs]


def is_blue_row(row: dict, image: Image.Image) -> bool:
    """Separate blue prompts from black option-bank text on the source page."""
    box = row.get("box") or []
    if not box:
        return row["x"] >= RIGHT_X
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    x0 = max(0, int(min(xs)) - 1)
    y0 = max(0, int(min(ys)) - 1)
    x1 = min(image.width, int(max(xs)) + 2)
    y1 = min(image.height, int(max(ys)) + 2)
    if x1 <= x0 or y1 <= y0:
        return row["x"] >= RIGHT_X

    dark_count = 0
    blue_count = 0
    for red, green, blue in image.crop((x0, y0, x1, y1)).getdata():
        if (red + green + blue) / 3 >= 190:
            continue
        dark_count += 1
        if blue - red > 18 and blue - green > 6:
            blue_count += 1
    return dark_count >= 6 and blue_count / dark_count >= 0.20


def merge_rows_by_line(rows: list[dict], tolerance: float = 10.0) -> list[dict]:
    """Join OCR fragments that belong to the same visual text line."""
    clusters: list[list[dict]] = []
    for row in sorted(rows, key=lambda item: (item["y"], item["x"])):
        if not clusters or abs(row["y"] - sum(item["y"] for item in clusters[-1]) / len(clusters[-1])) > tolerance:
            clusters.append([row])
        else:
            clusters[-1].append(row)

    merged = []
    for cluster in clusters:
        cluster.sort(key=lambda item: item["x"])
        merged.append({
            "text": clean_text(" ".join(item["text"] for item in cluster)),
            "x": min(item["x"] for item in cluster),
            "y": sum(item["y"] for item in cluster) / len(cluster),
            "score": min(item.get("score", 1) for item in cluster),
        })
    return merged


def option_parts(text: str, expected: str | None = None) -> tuple[str, str] | None:
    match = re.match(r"^\s*([A-Za-z01])\s*[.。．、,，:：]?\s*(.+)$", text)
    if not match:
        return None
    key, label = match.groups()
    if key == "1" and (expected == "I" or expected is None):
        key = "I"
    elif key == "0" and (expected == "O" or expected is None):
        key = "O"
    elif key == "l" and expected == "I":
        key = "I"
    return key, clean_text(label).strip(" |")


def parse_options(rows: list[dict]) -> tuple[list[dict], list[str]]:
    options = []
    issues = []
    rows = merge_rows_by_line(rows)
    start_index = next((index for index, row in enumerate(rows)
                        if option_parts(row["text"], "A")
                        and option_parts(row["text"], "A")[0] == "A"), None)
    if start_index is None:
        return [], ["未稳定提取到共用选项"]

    expected_index = 0
    for row in rows[start_index:]:
        expected = KEY_SEQUENCE[expected_index] if expected_index < len(KEY_SEQUENCE) else None
        parts = option_parts(row["text"], expected)
        if parts is None:
            if options:
                options[-1]["label"] = clean_text(options[-1]["label"] + " " + row["text"])
                options[-1]["sourceText"] = clean_text(options[-1]["sourceText"] + " " + row["text"])
            continue
        key, label = parts
        if expected and key != expected:
            issues.append(f"选项字母不连续：期望 {expected}，识别为 {key}")
            if key in KEY_SEQUENCE:
                expected_index = KEY_SEQUENCE.index(key)
        options.append({
            "key": key,
            "label": label or "原题文字待核对",
            "sourceText": row["text"],
            "sourceY": row["y"],
            "ocrScore": round(row["score"], 3),
        })
        if key not in KEY_SEQUENCE or KEY_SEQUENCE.index(key) + 1 >= len(KEY_SEQUENCE):
            break
        expected_index = KEY_SEQUENCE.index(key) + 1

    if len(options) < 2:
        issues.append("未稳定提取到共用选项")
    keys = [item["key"] for item in options]
    if len(keys) != len(set(keys)):
        issues.append("存在重复选项字母")
    if any(item["label"] == "原题文字待核对" for item in options):
        issues.append("存在空选项文本")
    return options, issues


def normalize_answer_code(raw: str, option_keys: set[str]) -> list[str]:
    code = []
    for char in re.sub(r"[^A-Za-z0-9]", "", raw):
        if char == "1" and "I" in option_keys and "1" not in option_keys:
            char = "I"
        elif char == "0" and "O" in option_keys and "0" not in option_keys:
            char = "O"
        code.append(char)
    return list(dict.fromkeys(code))


def answer_candidate(text: str, option_keys: set[str]) -> tuple[str, list[str], list[str]]:
    value = clean_text(text)
    openings = [value.rfind(char) for char in "（([【<《〈"]
    start = max(openings)
    if start >= 0:
        raw = value[start + 1:]
        raw = re.split(r"[）)\]】>》〉]", raw, maxsplit=1)[0]
        code = normalize_answer_code(raw, option_keys)
        if 1 <= len(code) <= 32:
            invalid = [key for key in code if key not in option_keys]
            return value[:start].rstrip(" :：,，"), code, invalid

    # Prefer an explicitly separated trailing token.
    separated = re.match(r"^(.+?)\s+([A-Za-z0-9](?:[/+,_-]?[A-Za-z0-9]){0,31})$", value)
    if separated:
        prefix, raw = separated.groups()
        code = normalize_answer_code(raw, option_keys)
        if code and all(key in option_keys for key in code):
            return prefix.rstrip(" :：,，([{<《〈"), code, []

    # OCR often joins the answer bubble directly to the prompt. Walk backward
    # only across valid option keys so English abbreviations such as CT/MRI E
    # retain their wording while the final answer is recovered.
    run = re.search(r"([A-Za-z]+)$", value)
    if run:
        raw = run.group(1)
        split = len(raw)
        while split > 0 and raw[split - 1] in option_keys:
            split -= 1
        suffix = raw[split:]
        prefix = value[:run.start()] + raw[:split]
        if suffix and prefix:
            # If the whole terminal word consists only of answer-key letters,
            # it is more likely an English heading than an answer bubble.
            if split == 0 and prefix == value[:run.start()] and not re.search(r"[\u3400-\u9fff]", prefix):
                return value, [], []
            return prefix.rstrip(" :：,，([{<《〈"), list(dict.fromkeys(suffix)), []
    return value, [], []


def parse_stems(rows: list[dict], option_keys: set[str]) -> tuple[str | None, list[dict], list[str]]:
    rows = merge_rows_by_line(rows)
    stems = []
    pending = []
    issues = []
    heading = None
    for row in rows:
        prompt, raw_answer, invalid = answer_candidate(row["text"], option_keys)
        if not raw_answer:
            if heading is None and not stems and not pending:
                heading = row["text"].strip("：: ")
                continue
            pending.append(row["text"])
            continue
        text_parts = [part for part in pending if part]
        if prompt and prompt not in text_parts:
            text_parts.append(prompt)
        text = clean_text(" ".join(text_parts)).strip("； ")
        pending = []
        answer = [] if invalid else raw_answer
        stem = {
            "text": text or "请结合原题页完成本小题",
            "answer": answer,
            "answerMode": "多选" if len(answer) > 1 else "单选",
            "sourceText": row["text"],
            "sourceY": row["y"],
            "ocrScore": round(row["score"], 3),
        }
        if invalid or not answer:
            stem["answerState"] = "待原题页核对"
            stem["answerMode"] = "待核对"
            stem["rawAnswer"] = "".join(raw_answer)
            if invalid:
                stem["unresolvedLetters"] = invalid
                issues.append(f"答案含选项池外字母：{''.join(invalid)}")
            else:
                issues.append("未提取到有效答案")
        stems.append(stem)

    if pending:
        for text in pending:
            text = clean_text(text).strip("； ")
            if not text:
                continue
            stems.append({
                "text": text[:500],
                "answer": [],
                "answerMode": "待核对",
                "answerState": "待原题页核对",
                "sourceText": text,
                "sourceY": rows[-1]["y"] if rows else None,
            })
            issues.append("末尾题干未识别到答案")
    if not stems:
        issues.append("未提取到题干")
    return heading, stems, issues


def title_for(heading: str | None, stems: list[dict], options: list[dict], page: int, group_number: int) -> str:
    candidates = [heading] if heading else []
    candidates.extend(stem["text"] for stem in stems if stem.get("text"))
    if not candidates:
        candidates = [item["label"] for item in options if item.get("label")]
    title = candidates[0] if candidates else f"第 {page} 页第 {group_number} 题组"
    title = re.sub(r"^[一二三四五六七八九十0-9]+[.、．]\s*", "", title)
    return title if len(title) <= 42 else title[:42] + "…"


def segment_groups(page: int, rows: list[dict], image_path: Path) -> list[dict]:
    dividers = divider_rows(image_path)
    source_image = Image.open(image_path).convert("RGB")
    bounds = [0] + dividers + [source_image.height]
    groups = []
    for index, (start, end) in enumerate(zip(bounds, bounds[1:]), 1):
        segment_rows = [row for row in rows if start + 3 <= row["y"] < end - 3]
        option_row_ids = {
            id(row) for row in segment_rows
            if row["x"] < RIGHT_X
            and re.match(r"^\s*[A-Za-z01]\s*[.。．、,，:：]", row["text"])
        }
        blue_rows = {
            id(row) for row in segment_rows
            if id(row) not in option_row_ids and is_blue_row(row, source_image)
        }
        left_rows = [
            row for row in segment_rows
            if id(row) not in blue_rows and row["x"] < RIGHT_X
        ]
        right_rows = [row for row in segment_rows if id(row) in blue_rows]
        options, option_issues = parse_options(left_rows)
        option_keys = {item["key"] for item in options}
        heading, stems, stem_issues = parse_stems(right_rows, option_keys)

        # Source-only tables still stay visible and searchable.
        if not stems and segment_rows:
            source = clean_text(" | ".join(row["text"] for row in segment_rows))
            stems = [{
                "text": source[:500] or "请结合原题页完成本题组",
                "answer": [],
                "answerMode": "待核对",
                "answerState": "待原题页核对",
                "sourceText": source,
                "sourceY": start,
            }]

        if not options and not stems:
            continue
        topic = SEGMENT_TOPIC_OVERRIDES.get((page, index), PAGE_TOPIC[page])
        unresolved = any(stem.get("answerState") for stem in stems)
        issues = list(dict.fromkeys(option_issues + stem_issues))
        kind = "B" if len(options) >= 2 and len(stems) >= 2 else "matching"
        if not options:
            kind = "source"
        elif len(stems) == 1 and len(stems[0].get("answer", [])) > 1:
            kind = "multi"
        kind_label = {
            "B": "B型题",
            "matching": "匹配 / 归类",
            "source": "原题页核对",
            "multi": "多项选择",
        }[kind]
        source_text = clean_text(" | ".join(row["text"] for row in segment_rows))[:5000]
        groups.append({
            "id": f"p{page:02d}-g{index}",
            "page": page,
            "title": title_for(heading, stems, options, page, index),
            "kind": kind,
            "kindLabel": kind_label,
            "options": [{k: v for k, v in item.items() if k != "sourceY"} for item in options],
            "stems": stems,
            "sourceText": source_text,
            "reviewState": "待原题页核对" if unresolved or issues else "已完成结构校对",
            "reviewIssues": issues,
            "topic": topic,
            "lectureIds": LECTURE_IDS[topic],
        })
    return groups


def make_manual_options(items: list[tuple[str, str]]) -> list[dict]:
    return [
        {"key": key, "label": label, "sourceText": f"{key}.{label}", "ocrScore": 1.0}
        for key, label in items
    ]


def make_manual_stems(items: list[tuple[str, str]]) -> list[dict]:
    stems = []
    for text, answer_code in items:
        answer = list(dict.fromkeys(answer_code))
        stems.append({
            "text": text,
            "answer": answer,
            "answerMode": "多选" if len(answer) > 1 else "单选",
            "sourceText": f"{text}（{answer_code}）",
            "ocrScore": 1.0,
            "reviewMethod": "300dpi原题页人工复核",
        })
    return stems


def finalize_group(group: dict) -> dict:
    group["reviewIssues"] = []
    group["reviewState"] = "已按原题页人工复核"
    group["kind"] = "B" if len(group.get("options", [])) >= 2 and len(group["stems"]) >= 2 else "matching"
    if len(group["stems"]) == 1 and len(group["stems"][0]["answer"]) > 1:
        group["kind"] = "multi"
    group["kindLabel"] = {
        "B": "B型题",
        "matching": "匹配 / 归类",
        "multi": "多项选择",
    }[group["kind"]]
    return group


def apply_manual_repairs(groups: list[dict]) -> list[dict]:
    repaired = []
    for group in groups:
        if group["id"] in SKIP_GROUPS:
            continue
        group_id = group["id"]
        if group_id in MANUAL_STEMS:
            group["stems"] = make_manual_stems(MANUAL_STEMS[group_id])
            group["title"] = MANUAL_TITLES.get(group_id, group["title"])
            finalize_group(group)

        if group_id in MANUAL_OPTIONS:
            group["options"] = make_manual_options(MANUAL_OPTIONS[group_id])
            group["title"] = MANUAL_TITLES.get(group_id, group["title"])
            group["sourceText"] = " | ".join(
                [option["sourceText"] for option in group["options"]]
                + [stem["sourceText"] for stem in group["stems"]]
            )
            finalize_group(group)

        if group_id == "p21-g4":
            group["options"] = make_manual_options([
                ("A", "同时侵犯右、左肝管"),
                ("B", "肿瘤侵犯左右肝管汇合部"),
                ("C", "肿瘤在肝总管"),
                ("D", "侵犯右肝管IIIa或左肝管IIIb"),
            ])
            finalize_group(group)

        option_label_fixes = {
            "p03-g4": {"C": "长径≤2cm"},
            "p05-g1": {"B": "I、II期"},
            "p06-g4": {"D": "CD117/KIT"},
            "p15-g1": {
                "A": "嵌顿内容物为小肠憩室，如 Meckel 憩室",
                "B": "嵌顿内容物仅为部分肠管壁，局部肿块不明显，多无肠梗阻，易误诊",
                "C": "即使疝囊内肠管存活，也必须将腹腔内相关肠袢牵出检查，以防遗漏隐匿在腹腔内的坏死肠袢",
                "D": "嵌顿内容物为阑尾，常感染化脓（appendix）",
                "E": "嵌顿肠管包括几个肠袢，呈W形",
            },
            "p20-g3": {
                "D": "WBC明显↑，常>20×10⁹/L（以中性粒细胞为主），Plt可↓",
                "L": "好发于肝总管、胆总管下段（汇合部位）",
            },
            "p22-g2": {"D": "Kasai肝门-空肠Roux-en-Y吻合术"},
        }
        for option in group.get("options", []):
            fixed = option_label_fixes.get(group_id, {}).get(option["key"])
            if fixed:
                option["label"] = fixed
                option["sourceText"] = f"{option['key']}.{fixed}"

        if group_id == "p01-g4":
            for stem in group["stems"]:
                stem["text"] = stem["text"].replace("近全圾", "近全切")
        if group_id == "p28-g1":
            group["lectureEvidence"] = {
                "lectureId": "lecture-19",
                "page": 1,
                "image": "surgery/lecture-pages/lecture-19-page-01.webp",
                "title": "第19讲第1页 · 泌尿系结石",
                "description": "讲义在“磷酸钙”条目下明确列出“酸化尿液+抗感染”，因此本题答案包含 N。",
            }
            group["reviewNotes"] = [{
                "title": "磷酸钙答案补充 N",
                "body": "已按第19讲第1页校对：磷酸钙对应“酸化尿液+抗感染”，答案由 AEHLO 修正为 AEHLNO。",
            }]
        if group_id == "p26-g3":
            group["lectureEvidence"] = {
                "lectureId": "lecture-18",
                "page": 2,
                "image": "surgery/lecture-pages/lecture-18-page-02.webp",
                "title": "第18讲第2页 · 膀胱癌T分期",
                "description": "讲义明确区分Tis、Ta、T1及T2-T4：T1侵犯固有层或黏膜下层，T2侵犯肌层。",
            }
            group["reviewNotes"] = [{
                "title": "第三组拆分误合并题干",
                "body": "原题页的“侵犯固有层或黏膜下层（A）”与“达肌层（D）”是两道独立题干，先前被错误拼成一题。现已拆回两题，并按第18讲第2页复核本组全部答案。",
            }]
        if group_id == "p27-g1":
            group["lectureEvidence"] = {
                "lectureId": "lecture-18",
                "page": 3,
                "image": "surgery/lecture-pages/lecture-18-page-03.webp",
                "title": "第18讲第3页 · 尿三杯与血尿时相",
                "description": "讲义明确：终末血尿可见于肾和膀胱结核、膀胱炎、膀胱结石及膀胱癌。",
            }
            group["reviewNotes"] = [{
                "title": "第六组终末血尿补充 I",
                "body": "原题页选项I为“多数肾结核”，但终末血尿圈选答案漏写I。按第18讲第3页，肾和膀胱结核均可出现终末血尿，答案由BDFH修正为BDFHI。",
            }]
        if group_id == "p28-g2":
            group["lectureEvidence"] = {
                "lectureId": "lecture-19",
                "page": 2,
                "image": "surgery/lecture-pages/lecture-19-page-02.webp",
                "title": "第19讲第2页 · 尿路结石与胆系结石鉴别",
                "description": "讲义表格逐项对照地区、钙代谢、主要成分、X线表现和治疗方式。",
            }
            group["reviewNotes"] = [{
                "title": "第十组拆分横向题干",
                "body": "先前把原题左右两列及上下行误拼为“胱氨酸胆系结石”等错误题干。现已恢复为尿路结石5题、胆系结石4题，共9道独立题干，并按第19讲第2页逐项复核答案。",
            }]
        if group_id == "p14-g2":
            group["reviewNotes"] = [{
                "title": "腹股沟管下壁答案删除 C",
                "body": "已对照原题第14页和第12讲第1页：下壁由腹股沟韧带、腔隙韧带构成，答案由 CFI 修正为 FI。",
            }]
        if group_id in SOURCE_VERIFIED_HERNIA_GROUPS:
            group["title"] = MANUAL_TITLES[group_id]
            group["sourceText"] = " | ".join(
                [option["sourceText"] for option in group["options"]]
                + [stem["sourceText"] for stem in group["stems"]]
            )
            finalize_group(group)
        if group_id in SOURCE_VERIFIED_OPTION_GAPS:
            finalize_group(group)

        repaired.append(group)
        if group_id == "p21-g4":
            extra = {
                **{key: value for key, value in group.items() if key not in {"id", "title", "options", "stems", "sourceText"}},
                "id": "p21-g5",
                "title": "胆管癌根治术",
                "options": make_manual_options([
                    ("A", "切胆囊+肝外胆管，作胆肠Roux-en-Y吻合"),
                    ("B", "切肿瘤及距肿瘤边缘1cm的胆管，作肝管-空肠Roux-en-Y吻合"),
                    ("C", "多姑息治疗"),
                    ("D", "切胆囊+肝外胆管+部分肝，作胆肠Roux-en-Y吻合"),
                    ("E", "胰头十二指肠切除术（Whipple术），或联合切除受累肝组织"),
                ]),
                "stems": make_manual_stems([
                    ("下段胆管癌", "E"), ("中段胆管癌", "B"),
                    ("上段/肝门部胆管癌I型", "A"), ("上段/肝门部胆管癌II型", "A"),
                    ("上段/肝门部胆管癌III型", "D"), ("上段/肝门部胆管癌IV型", "C"),
                ]),
                "sourceText": "第21页下方胆管癌根治术题组",
            }
            repaired.append(finalize_group(extra))
    return repaired


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--lecture-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    pages = load_ocr(args.ocr)
    lectures = shared.build_lectures(args.lecture_dir)
    page_records = []
    groups = []
    for page in sorted(pages):
        rows = pages[page]
        page_records.append({
            "page": page,
            "image": "",
            "topic": PAGE_TOPIC[page],
            "searchText": clean_text(" ".join(row["text"] for row in rows))[:7000],
        })
        groups.extend(segment_groups(page, rows, args.image_dir / f"page-{page:02d}.webp"))
    groups = apply_manual_repairs(groups)

    payload = {
        "meta": {
            "title": "外科学题库",
            "sourcePdf": "外科各论除骨科(去胶带版).pdf",
            "sourcePages": len(page_records),
            "sourcePdfPages": len(pages),
            "lectureCount": len(lectures),
            "generatedBy": "scripts/build_surgery_content.py",
            "siteIntegrated": True,
            "answerNote": "按原题页横向题组提取；答案与选项池不一致或识别不清的题干不自动判分，保留原题页供继续校对。",
        },
        "topics": ["全部", *TOPICS, "综合"],
        "pages": page_records,
        "groups": groups,
        "lectures": lectures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pages": len(page_records),
        "lectures": len(lectures),
        "groups": len(groups),
        "stems": sum(len(group["stems"]) for group in groups),
        "unresolvedStems": sum(
            1 for group in groups for stem in group["stems"] if stem.get("answerState")
        ),
        "types": dict(Counter(group["kind"] for group in groups)),
        "topics": dict(Counter(group["topic"] for group in groups)),
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
