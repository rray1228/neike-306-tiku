"""Import the 25-question exam and the explicitly user-authorized draft key.

The PDF has no official key. Draft answers are separately attributed and retain
the source X-type markers, including Q10's single defensible choice. Default
output is apply_patch; --check verifies the data;
--images converts original page renders for the website source viewer.
"""
import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '【生化】阶段考试 天天师兄27考研 再相逢！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
TARGET = ROOT / 'src/data/biochemistry-stage-exam-data.json'
KEY = 'biochemistry-stage-exam-2026-10'
MULTIPLE = {3, 4, 6, 10, 11, 13, 18, 21, 22}
# Classify by the tested knowledge, never by a distractor's organ or molecule.
LECTURES = [8, 3, 3, 3, 6, 6, 2, 7, 7, 9, 10, 10, 20, 20, 16, 16,
            17, 18, 19, 19, 14, 14, 14, 14, 14]
TOPICS = {2: '生物氧化', 3: '糖代谢', 6: '脂代谢',
          7: '氨基酸与蛋白质', 8: '氨基酸与蛋白质',
          9: '核苷酸代谢', 10: '胆色素代谢与生物转化', 14: '小基因',
          16: '核酸', 17: '核酸', 18: '核酸', 19: '核酸', 20: '核酸'}

# Requested by the user on 2026-10-17, not transcribed from an official key.
DRAFT_ANSWERS = ['B', 'D', 'BC', 'ABC', 'D', 'AB', 'C', 'B', 'A', 'A',
                 'ABCD', 'D', 'ABD', 'B', 'B', 'B', 'B', 'AC', 'D', 'B',
                 'ABD', 'ACD', 'C', 'B', 'D']
EXPLANATIONS = {
    1: '拟答B。接近生理pH时，pI低于环境pH的蛋白质带负电、向正极迁移。按本题以pI比较的条件，自正极侧依次为B（2.77）、A（6.01）、D（7.80）、C（9.64）。',
    2: '拟答D。肌肉缺乏葡糖-6-磷酸酶，不能将葡糖-6-磷酸水解为可释放入血的游离葡萄糖；不要与磷酸戊糖途径中的葡糖-6-磷酸脱氢酶混淆。',
    3: '拟答BC。磷酸戊糖途径提供5-磷酸核糖和NADPH，分别满足核酸合成和脂肪酸等还原性合成的需要。糖异生或尿素合成增强本身并不必然要求该途径增强。',
    4: '暂拟ABC。肌糖原经糖酵解形成乳酸，乳酸到肝经糖异生形成葡萄糖；按题目“可经过”的宽口径，也包括乳酸经三碳途径形成肝糖原。若只考经典乳酸—葡萄糖闭合循环，AB同样有依据，本题暂同时接受AB；肝糖原合成是可能去路，不是每轮必经步骤。D不是乳酸循环的必要途径。',
    5: '拟答D。胞质脂肪酸合成中，延长中的酰基由ACP（酰基载体蛋白）的磷酸泛酰巯基乙胺臂携带。生物素主要参与羧化反应，不能据此选作延长酰基的载体。',
    6: '讲义第45页写明，正常进食时肝主要通过氧化脂肪酸获得能量，成人心肌也主要消耗脂肪酸。本题选A、B。',
    7: '拟答C。P/O约1.4接近通常所用的1.5，提示绕过复合体Ⅰ、在辅酶Q水平进入呼吸链；NADH经复合体Ⅰ进入时常按约2.5计算。',
    8: '拟答B。鸟氨酸脱羧酶催化鸟氨酸生成腐胺，是多胺合成的关键调节酶；注意是脱羧，不是脱氨。',
    9: '拟答A。蛋氨酸经SAM提供甲基，参与磷脂酰胆碱等代谢；缺乏可影响肝内脂质输出，促进脂肪肝形成。',
    10: '拟答仅A。按本题采用的哺乳动物CPSⅡ口径：其位于胞质、氮源为谷氨酰胺，受UTP而非UMP反馈抑制。讲义将细菌嘧啶合成的经典关键酶列为天冬氨酸氨基甲酰转移酶；CPSⅡ对应细胞增殖程度，肝细胞分化程度对应CPSⅠ。原卷标X，但现有四项仅A符合讲义，疑似题型或选项笔误，保留原卷多选操作。',
    11: '暂拟ABCD，按本题常见教材列举口径。磺胺、水杨酸及较高浓度游离脂肪酸可干扰胆红素—白蛋白结合，增加游离胆红素。胆汁酸项有表述争议：影响依具体分子及实验条件而异，原始研究也有增强胆红素结合的结果，不能泛化为所有胆汁酸均竞争置换；因此本题暂同时接受ABC，待你校正D项口径。',
    12: '拟答D，题目问错误项。讲义列出的睾酮诱导对象是ALA合酶，而非终末步骤的血红素合成酶（亚铁螯合酶）。甘氨酸、琥珀酰CoA和Fe²⁺为原料，起始与终末阶段在线粒体，ALA合酶需要磷酸吡哆醛。',
    13: '拟答ABD。真核基因组中编码序列占比较小，存在多基因家族及假基因，典型蛋白质编码mRNA为单顺反子。“断裂基因”指外显子被内含子隔开，不是说转录本身跳过内含子、断续进行。',
    14: '拟答B。遗传性乳腺癌的重要易感基因BRCA1/BRCA2参与同源重组修复；错配修复缺陷典型关联Lynch综合征，核苷酸切除修复缺陷典型关联着色性干皮病。',
    15: '拟答B。端粒酶延长染色体末端富G/T的端粒重复序列，从而补偿复制导致的末端缩短；polyA尾是典型真核mRNA加工特征。',
    16: '拟答B，题目问错误项。端粒酶以自身RNA为模板延长DNA的3′端，而不是向5′端添加端粒；其余项描述RNA模板、富G/T单链末端识别及线性染色体复制相关作用。',
    17: '拟答B。流产性起始指转录起始时RNA聚合酶反复合成并释放短RNA，未能进入稳定延长阶段，属于RNA合成的起始过程。',
    18: '拟答AC。一个mRNA可同时结合多个核糖体，形成多聚核糖体；C按各核糖体完成同一开放阅读框后所得最终多肽解释。瞬时新生肽链长度不同，合成单条完整肽链所需时间并未因此缩短，提高的是并行产量。',
    19: '拟答D。典型动物miRNA与靶mRNA多不完全互补。转录后调控、Dicer加工和RISC参与并不是miRNA相对于siRNA独有的特点。',
    20: '拟答B。按本讲义的经典原核/真核比较，miRNA调控属于真核机制；原核可通过反义RNA、调节蛋白结合mRNA及稀有密码子比例影响表达。本题不讨论非典型或工程化RNA系统。',
    21: '本题按书上列举范围选A、B、D：p21介导细胞周期阻滞，BAX参与细胞凋亡，GADD45参与DNA损伤应答。',
    22: '拟答ACD。化学合成、cDNA文库和PCR均可用于获得目的基因。基因芯片主要用于检测、分析序列或表达信息，不是本题所考的目的基因制备方法。',
    23: '拟答C。GATATC的反向互补序列仍为GATATC，符合本题所考常见Ⅱ类限制酶识别的回文结构；EcoRV即识别这一序列。并非所有Ⅱ类限制酶都只识别这种回文序列。',
    24: '暂拟B。按本讲义中用于蛋白质相互作用分析的GST pull-down考点，标签是GST；GST与固定化谷胱甘肽结合以捕获相互作用蛋白。“目前最常用”缺少统计范围，不能据此断言GST在所有标签技术中都最常用；His标签也能用于亲和纯化及pull-down，保留本题口径待复核。',
    25: '拟答D。ddNTP缺少继续延长所需的3′-OH，掺入后终止DNA链合成；Sanger链终止测序据终止片段确定序列。',
}
# Ambiguous wording is explained after submission, not silently treated as
# scientific certainty. Both defensible readings receive credit in Q4/Q11.
ACCEPTED_ALTERNATIVES = {4: [list('AB')], 11: [list('ABC')]}
REVIEW_QUESTIONS = [4, 10, 11, 18, 24]
USER_CORRECTIONS = {6: '用户按讲义校正（2026-11-12）', 21: '用户按书校正（2026-11-02）'}
REFERENCES = {
    4: ['https://pubmed.ncbi.nlm.nih.gov/1747116/'],
    10: ['https://pubmed.ncbi.nlm.nih.gov/14651476/'],
    11: ['https://www.jci.org/articles/view/107882', 'https://pubmed.ncbi.nlm.nih.gov/2444264/'],
    24: ['https://www.thermofisher.com/order/catalog/product/21516'],
}


def display_explanation(number):
    text = re.sub(r'^(?:拟答(?:仅)?|暂拟)[A-D]+[。，]', '', EXPLANATIONS[number])
    text = text.replace('按本题常见教材列举口径。', '')
    text = text.replace('本题暂同时接受AB；', '')
    text = text.replace('；因此本题暂同时接受ABC，待你校正D项口径。', '。')
    text = text.replace('原卷标X，但现有四项仅A符合讲义，疑似题型或选项笔误，保留原卷多选操作。', '本题仅A符合上述条件。')
    return text.replace('，保留本题口径待复核。', '。')


def clean(text):
    # The printed source contains these watermark fragments within sentences.
    text = text.replace('uusx', '')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'\s*([，。：；、])\s*', r'\1', text)
    return text


def extract():
    records = {}
    current = field = None
    pages = PdfReader(SOURCE).pages
    assert len(pages) == 5
    for page_no, page in enumerate(pages, 1):
        for raw in page.extract_text().splitlines():
            line = clean(raw)
            if not line or '每日计划' in line or re.fullmatch(r'- \d+ -', line):
                continue
            match = re.match(r'^(\d{1,2})\.(?!\d)(.*)', line)
            if match:
                number = int(match[1])
                assert number == len(records) + 1, (number, len(records))
                text = match[2].strip()
                multi = text.startswith('（X）')
                if multi:
                    text = text.removeprefix('（X）').strip()
                current = {'number': number, 'page': page_no, 'pages': {page_no},
                           'text': [text], 'options': {}, 'multiple': multi}
                records[number] = current
                field = current['text']
                continue
            if current is None:
                continue
            current['pages'].add(page_no)
            option = re.match(r'^([A-D])\.(.*)', line)
            if option:
                assert option[1] not in current['options'], current
                current['options'][option[1]] = [option[2]]
                field = current['options'][option[1]]
            else:
                field.append(line)
    assert list(records) == list(range(1, 26))
    assert {n for n, q in records.items() if q['multiple']} == MULTIPLE
    for q in records.values():
        assert list(q['options']) == list('ABCD'), q
        q['text'] = clean(' '.join(q['text']))
        q['options'] = {key: clean(' '.join(value)) for key, value in q['options'].items()}
        assert q['text'] and all(q['options'].values())
    # Visually checked typography: PDF extraction separates letters in Q23,
    # flattens Fe's superscript charge and B6's subscript numeral in Q12.
    records[12]['options']['A'] = records[12]['options']['A'].replace('Fe2+', 'Fe²⁺')
    records[12]['options']['C'] = records[12]['options']['C'].replace('B6', 'B₆')
    for key, value in records[23]['options'].items():
        assert re.fullmatch(r'[ACGT ]+', value), value
        records[23]['options'][key] = value.replace(' ', '')
    return records


def build():
    assert len(DRAFT_ANSWERS) == 25 and set(EXPLANATIONS) == set(range(1, 26))
    groups = []
    for n, q in extract().items():
        lecture = LECTURES[n - 1]
        lid = f'lecture-{lecture:02d}'
        mode = '多选' if q['multiple'] else '单选'
        answer = DRAFT_ANSWERS[n - 1]
        assert set(answer) <= set(q['options'])
        assert q['multiple'] or len(answer) == 1
        groups.append({
            'id': f'{KEY}-q{n:03d}', 'page': q['page'],
            'sourceKey': KEY, 'sourceName': SOURCE_NAME, 'sourceSection': '生物化学',
            'sourceQuestion': str(n), 'sourceLabel': '阶段考试',
            'sourcePages': sorted(q['pages']), 'title': f'阶段考试 · 第{n}题',
            'kind': 'X' if q['multiple'] else 'A',
            'kindLabel': '多项选择' if q['multiple'] else '单项选择',
            'answerLayout': 'rows', 'topic': TOPICS[lecture], 'lectureIds': [lid],
            'supplement': True, 'supplementNotice': '', 'studyNotice': '生物化学',
            'answerSourceLabel': '答案',
            'answerSourceName': USER_CORRECTIONS.get(n, '用户授权拟答：讲义与补充资料核对（2026-10-17）'),
            'answerRevision': 'bio-stage-p53-20261102-v2' if n == 21 else 'bio-stage-draft-20261017-v1',
            'options': [{'key': key, 'displayKey': key, 'label': value}
                        for key, value in q['options'].items()],
            'stems': [{'number': n, 'sourceQuestion': n, 'sourcePage': q['page'],
                       'text': q['text'], 'answerRaw': answer, 'answer': list(answer),
                       'answerMode': mode, 'sourceAnswerMode': mode,
                       'answerState': '用户校正' if n in USER_CORRECTIONS else '讲义核对拟答（非官方）',
                       'answerProvenance': 'user-correction' if n in USER_CORRECTIONS else 'assistant-draft',
                       'explanation': display_explanation(n),
                       **({'acceptedAnswers': ACCEPTED_ALTERNATIVES[n]} if n in ACCEPTED_ALTERNATIVES else {}),
                       **({'answerReviewNote': '原题表述/题型口径需复核，详见答后解析'} if n in REVIEW_QUESTIONS else {}),
                       **({'answerReferences': REFERENCES[n]} if n in REFERENCES else {}),
                       'lectureId': lid}],
        })
    return {
        'meta': {'title': '生物化学·阶段考试', 'sourceName': SOURCE_NAME, 'sourcePages': 5,
                 'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 'groupCount': 25, 'stemCount': 25, 'multipleChoiceCount': 9,
                 'missingAnswerQuestions': [], 'hasOfficialAnswerKey': False,
                 'missingOfficialAnswerQuestions': list(range(1, 26)),
                 'draftAnswerQuestions': list(range(1, 26)), 'reviewQuestionNumbers': REVIEW_QUESTIONS,
                 'answerNote': '原卷无官方答案；经用户授权按讲义与补充资料逐题拟答并启用判分。第4、11题暂兼容两种有依据的口径，第10题保留原卷X型但拟答仅A；均可后续校正。'},
        'groups': groups,
        'pages': [{'page': n, 'sourceKey': KEY, 'image': f'biochemistry/{KEY}/page-{n:02d}.webp'}
                  for n in range(1, 6)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--images', type=Path)
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT / 'public/biochemistry' / KEY
        dest.mkdir(parents=True, exist_ok=True)
        for n in range(1, 6):
            with Image.open(args.images / f'page-{n}.png') as im:
                im.convert('RGB').save(dest / f'page-{n:02d}.webp', quality=92)
        print('5 original PDF pages converted.')
    elif args.check:
        assert json.loads(TARGET.read_text()) == data
        print('25 questions, 100 options, 9 source X-type questions, 25 attributed draft answers: PASS')
    else:
        new = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        print('*** Begin Patch')
        if TARGET.exists():
            print('*** Update File: src/data/biochemistry-stage-exam-data.json')
            for line in list(difflib.unified_diff(TARGET.read_text().splitlines(), new.splitlines(), n=3))[2:]:
                print('@@' if line.startswith('@@') else line)
        else:
            print('*** Add File: src/data/biochemistry-stage-exam-data.json')
            print('\n'.join('+' + line for line in new.splitlines()))
        print('*** End Patch')


if __name__ == '__main__':
    main()
