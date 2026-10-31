"""Import 197 supplied practitioner questions, preserving screenshot answers.

The PDF has no printed question numbers: sourceQuestion follows reading order.
Clinical commentary is authored in practitioner_upper_notes.tsv, not official
publisher explanations. --check is read-only; --images converts rendered pages.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re
from pypdf import PdfReader
from practitioner_upper_lectures import attach_lectures

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = '精选执业医师内、外科真题（上） 天天师兄27考研 个性化复习！.pdf'
SOURCE = Path('/Users/ray/Downloads') / SOURCE_NAME
KEY = 'practitioner-upper-20261019'
ANSWER_ROWS = [
    'CACDC', 'CCCBA', 'CABCA', 'BEDAD', 'CCACD',
    'BCDDE', 'CABEB', 'EDEEE', 'ADDCE', 'AABED',
    'ACCED', 'ADBDE', 'DBACE', 'BCCCC', 'EEADB',
    'ABADD', 'DBEEE', 'DEDCC', 'ABAEE', 'BDDEC',
    'BDECD', 'EBDAE', 'AAEBC', 'EBACA', 'BDAAE',
    'EDBBC', 'DEBBE', 'BBDAA', 'BCACE', 'DDBEA',
    'DCEDA', 'EDCAC', 'CBEDB', 'ECBBD', 'ECDCC',
    'ECDCE', 'CCBDA', 'EDADC', 'ECBDB', 'AA',
]
ANSWERS = ''.join(ANSWER_ROWS)
PENDING = {89, 90}
# First subquestion -> (last, beginning of the first actual question).
SHARED = {
    5: (6, '该患者此时'), 11: (12, '该患者呼吸困难'),
    26: (27, '若需使用'), 30: (32, '该患者突发'),
    36: (37, '该患者最可能'), 63: (64, '该患者的结肠镜'),
    73: (74, '该患者最有'), 94: (96, '为判断该患者'),
    100: (101, '为明确下肢'), 102: (104, '该患者目前'),
    105: (107, '该患者的视网膜'), 108: (109, '该患者最可能'),
    121: (122, '该患者的主要'), 125: (126, '该患者最可能'),
    131: (132, '首选的治疗'), 141: (143, '首先考虑'),
    144: (146, '该患者最可能'), 158: (159, '该患者最可能'),
    160: (162, '该患者诊断'), 163: (164, '该患者最可能'),
    186: (187, '该患者最可能'), 191: (192, '该患者最可能'),
    195: (197, '该患者最可能'),
}
COMMON_OPTIONS = {170: 172, 183: 184}
LARGE_CASES = {start: value for start, value in SHARED.items() if value[0]-start+1 >= 3}
MED_RANGES = [
    (1,2,1),(3,6,9),(7,7,5),(8,8,6),(9,10,8),(11,12,3),
    (13,14,4),(15,17,7),(18,18,5),(19,19,12),(20,21,2),
    (22,23,13),(24,24,10),(25,25,11),(26,26,1),(27,28,11),
    (29,30,55),(31,31,56),(32,33,55),(34,40,56),(41,43,52),
    (44,47,54),(48,51,53),(52,53,49),(54,54,50),(55,55,51),
    (56,56,57),(57,58,14),(59,60,15),(61,61,16),(62,64,18),
    (65,65,17),(66,66,19),(67,69,22),(70,71,20),(72,72,21),
    (73,74,23),(75,75,24),(76,80,27),(81,82,26),(83,83,25),
    (84,85,28),(86,87,30),(88,88,29),(89,89,33),(90,92,34),
    (93,96,35),(97,97,32),(98,99,31),(100,101,36),(102,107,38),
    (108,109,39),(110,110,41),(111,111,40),(112,112,44),
    (113,113,45),(114,115,48),
]
SURGERY_RANGES = [
    (116,117,30),(118,118,35),(119,119,37),(120,120,32),
    (121,122,34),(123,123,33),(124,124,2),(125,126,1),(127,127,4),
    (128,132,3),(133,133,4),(134,134,5),(135,135,6),(136,136,7),
    (137,138,12),(139,146,8),(147,148,9),(149,149,10),
    (150,151,16),(152,152,15),(153,153,16),(154,155,15),(156,156,6),
    (157,157,17),(158,166,19),(167,168,18),(169,169,12),
    (170,172,18),(173,173,28),(174,175,29),(176,176,28),
    (177,177,29),(178,180,26),(181,184,28),(185,185,22),
    (186,188,27),(189,189,21),(190,193,24),(194,197,25),
]
SURGERY_TOPICS = {
    1:'颈部疾病',2:'胸部疾病',3:'乳房疾病',4:'胸部疾病',
    5:'胃十二指肠疾病',6:'腹部损伤与感染',7:'腹部损伤与感染',
    8:'小肠与阑尾疾病',9:'小肠与阑尾疾病',10:'结直肠与肛管疾病',
    12:'腹外疝',15:'肝胆胰疾病',16:'肝胆胰疾病',17:'周围血管疾病',
    18:'泌尿外科',19:'泌尿外科',
}
REFERENCES = {
    'ards': ('ARDS全球定义原文：排除心源性肺水肿', 'https://doi.org/10.1164/rccm.202303-0558WS'),
    'hcc': ('AASLD肝癌指南：增强CT/MRI及无创诊断', 'https://www.aasld.org/sites/default/files/2022-06/HCC-Guideline-2018.pdf'),
    'pancreatitis': ('NICE NG104：胰腺炎营养与抗菌药', 'https://www.nice.org.uk/guidance/ng104/chapter/Recommendations'),
    'pancreatitis-diagnosis': ('ACG急性胰腺炎指南：诊断与胰酶检查', 'https://gi.org/guidelines/acute-pancreatitis/'),
    'mds': ('WHO第5版髓系肿瘤分类原文', 'https://www.nature.com/articles/s41375-022-01613-1'),
    'retina': ('NICE NG242：增殖性视网膜病变治疗', 'https://www.nice.org.uk/guidance/ng242/chapter/Recommendations'),
    'intussusception': ('RCH肠套叠指南：超声与灌肠', 'https://www.rch.org.au/clinicalguide/guideline_index/Intussusception/'),
    'trauma': ('EAU泌尿创伤指南：按稳定性选择治疗', 'https://uroweb.org/guidelines/urological-trauma/chapter/urogenital-trauma-guidelines'),
    'testis': ('EAU隐睾指南：手术完成时间', 'https://uroweb.org/guidelines/paediatric-urology/chapter/management-of-undescended-testes'),
    'infection': ('EAU泌尿感染指南：泌尿生殖结核', 'https://uroweb.org/guidelines/urological-infections/chapter/the-guideline'),
    'dapt': ('AHA/ACC慢性冠脉病指南：抗血小板疗程', 'https://www.ahajournals.org/doi/10.1161/CIR.0000000000001168'),
    'dka': ('ADA/EASD高血糖危象共识：补液与酸中毒处理', 'https://doi.org/10.2337/dci24-0032'),
    'bph': ('EAU男性下尿路症状指南：TURP手术治疗', 'https://uroweb.org/guidelines/management-of-non-neurogenic-male-luts/chapter/disease-management'),
    'corticosteroids': ('SCCM 2024糖皮质激素使用指南', 'https://sccm.org/clinical-resources/guidelines/guidelines/use-of-corticosteroids-in-sepsis-ards-cap'),
}
QUESTION_REFS = {24:['ards'],46:['dapt'],72:['hcc'],73:['pancreatitis-diagnosis'],74:['pancreatitis'],
    89:['mds'],90:['mds'],106:['retina'],139:['intussusception'],
    161:['trauma'],162:['trauma'],169:['testis'],170:['infection'],
    171:['infection'],172:['infection'],103:['dka'],166:['bph'],122:['corticosteroids']}


def clean(text):
    text = text.replace('ttsx', '')
    text = re.sub(r'\s+', ' ', text).strip()
    # Join Chinese words split solely by the PDF's line wrapping.
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    text = re.sub(r'\s*([，。：；、])\s*', r'\1', text)
    text = re.sub(r'(?<=\d)- (?=\d)', '-', text)
    text = re.sub(r'×\s*10\s*(9|12|6)(?=/L)', lambda m:'×10'+{'9':'⁹','12':'¹²','6':'⁶'}[m[1]], text)
    return text


def extract():
    records, buffer = [], []
    current, common, remaining, is_common = None, None, 0, False
    pdf = PdfReader(SOURCE)
    assert len(pdf.pages) == 39
    for page_no, page in enumerate(pdf.pages, 1):
        for raw in page.extract_text().splitlines():
            line = raw.strip()
            if not line or line.startswith(('每日计划','- ','天天师兄','★','（请结合',
                '恭喜','缺氧训练','巩固考点','加油鸭')) or line in ['内科','外科']:
                continue
            if remaining:
                records.append({'number':len(records)+1,'text':line,
                    'options':copy.deepcopy(common),'pages':[page_no],'commonOptions':True})
                remaining -= 1
                continue
            match = re.match(r'^([A-E])\.(.*)', line)
            if match:
                if match[1] == 'A':
                    current = {'number':len(records)+1,'text':' '.join(t for _,t in buffer),
                        'options':{},'pages':sorted(set([page_no]+[p for p,_ in buffer]))}
                    buffer = []
                    is_common = match[2] in ['抗结核治疗','膝关节脱位']
                    if not is_common:
                        records.append(current)
                assert match[1] not in current['options'], current
                current['options'][match[1]] = match[2]
                current['pages'] = sorted(set(current['pages']+[page_no]))
                if match[1] == 'E' and is_common:
                    remaining = 3 if current['options']['A']=='抗结核治疗' else 2
                    common = current['options']
                continue
            if current and len(current['options']) < 5:
                current['options'][list(current['options'])[-1]] += ' '+line
                current['pages'] = sorted(set(current['pages']+[page_no]))
                continue
            buffer.append((page_no,line))
    assert len(records) == 197 and not buffer and not remaining
    for q in records:
        q['text'] = clean(q['text'])
        q['options'] = {k:clean(v) for k,v in q['options'].items()}
        assert q['text'] and list(q['options']) == list('ABCDE')
    return records


def topic(subject, lecture):
    if subject == 'surgery':
        return SURGERY_TOPICS.get(lecture, '骨科' if 20 <= lecture <= 29 else '外科总论')
    for low,high,name in [(1,13,'呼吸'),(14,23,'消化'),(24,27,'肾脏'),
        (28,35,'血液'),(36,42,'内分泌'),(43,47,'风湿'),(48,48,'中毒'),(49,57,'循环')]:
        if low <= lecture <= high:
            return name
    raise ValueError(lecture)


def build():
    assert len(ANSWERS) == 197
    records = extract()
    # Two-question vignettes each get a separate page with the full context.
    # Only three-or-more-question cases remain together. B-type shared-option
    # questions also get independent pages, retaining the original option pool.
    for start, (end, marker) in SHARED.items():
        if start in LARGE_CASES:
            continue
        first = records[start-1]
        context = first['text'][:first['text'].index(marker)].strip()
        for q in records[start:end]:
            q['text'] = context+' '+q['text']
            q['pages'] = sorted(set(first['pages']+q['pages']))
    notes = {}
    for line in Path(__file__).with_name('practitioner_upper_notes.tsv').read_text().splitlines():
        n, focus, explanation, connection = line.split('|')
        assert int(n) not in notes
        notes[int(n)] = (focus, explanation, connection)
    assert set(notes) == set(range(1,198))
    result = {}
    for subject,ranges in [('med',MED_RANGES),('surgery',SURGERY_RANGES)]:
        assignment = {}
        for start,end,l in ranges:
            for n in range(start,end+1):
                assert n not in assignment
                assignment[n] = l
        groups, n = [], min(assignment)
        while n <= max(assignment):
            end = LARGE_CASES[n][0] if n in LARGE_CASES else n
            qq = copy.deepcopy(records[n-1:end])
            shared_stem = None
            if n in LARGE_CASES:
                marker = LARGE_CASES[n][1]
                pos = qq[0]['text'].index(marker)
                shared_stem, qq[0]['text'] = qq[0]['text'][:pos].strip(), qq[0]['text'][pos:]
                assert shared_stem
            common = bool(qq[0].get('commonOptions'))
            label = str(n) if n == end else f'{n}–{end}'
            def chapter_id(number):
                return 'med-lecture-12' if number == 133 else f'lecture-{assignment[number]:02d}'
            lectures = list(dict.fromkeys(chapter_id(q['number']) for q in qq))
            topics = {topic(subject,assignment[q['number']]) for q in qq}
            assert len(topics) == 1
            g = {'id':f'{KEY}-q{n:03d}', 'page':qq[0]['pages'][0],
                'sourceKey':KEY, 'sourceName':SOURCE_NAME, 'sourceSection':'内科' if subject=='med' else '外科',
                'sourceQuestion':label, 'sourceLabel':'精选执医（上）',
                'sourcePages':sorted({p for q in qq for p in q['pages']}),
                'title':f'精选执医（上） · 第{label}题 · {notes[n][0]}',
                'kind':'B' if common else 'A', 'kindLabel':'B型题' if common else '单项选择',
                'answerLayout':'rows', 'topic':topics.pop(), 'lectureIds':lectures,
                'diseaseTags':['精选执医','执业医师真题（上）']+[notes[q['number']][0] for q in qq],
                'supplement':True,
                'supplementNotice':'答案依所给截图（139题依评论更正）；解析为整理补充，非官方解析。争议题暂不自动判分。',
                'answerSourceLabel':'截图参考答案', 'answerSourceName':'2026-10-19用户提供的答案及更正截图',
                'answerRevision':'20261019-v2', 'options':[], 'stems':[]}
            if n == 24:
                g.update(answerRevision='20261019-q24-A-v3',
                    answerSourceLabel='用户确认答案',
                    supplementNotice='第24题按用户确认更正为A；解析为复习整理。')
            if n == 102:
                g.update(answerRevision='20261020-q103-A-v3',
                    answerSourceLabel='截图及用户更正',
                    answerSourceName='2026-10-19答案截图及2026-10-20用户明确更正',
                    supplementNotice='第103题按用户确认更正为A，其余答案依所给截图；解析为复习整理。')
            if n == 105:
                g.update(answerRevision='20261020-q106-E-confirmed-v3',
                    answerSourceLabel='截图及用户确认',
                    answerSourceName='2026-10-19答案截图及2026-10-20用户明确确认',
                    supplementNotice='第106题已由用户确认答案E，恢复正常判分；其余答案依所给截图，解析为复习整理。')
            if n == 194:
                g.update(answerRevision='20261020-q194-C-v3',
                    answerSourceLabel='用户确认答案',
                    answerSourceName='2026-10-20用户明确更正：第194题选C',
                    supplementNotice='第194题按用户确认更正为C（右髋关节MRI）；解析为复习整理。')
            if n == 172:
                g.update(answerRevision='20261023-q172-A-v3',
                    answerSourceLabel='用户确认答案',
                    answerSourceName='2026-10-23用户明确更正：第172题选A',
                    supplementNotice='第172题按用户确认更正为A（抗结核治疗），恢复正常判分；解析为复习整理。')
            if n == 160:
                g.update(answerRevision='20261023-q162-B-confirmed-v3',
                    answerSourceLabel='截图及用户确认',
                    answerSourceName='2026-10-19答案截图及2026-10-23用户明确确认',
                    supplementNotice='第162题已由用户确认答案B（手术探查），恢复正常判分；其余答案依所给截图，解析为复习整理。')
            if n == 166:
                g.update(answerRevision='20261023-q166-C-v3',
                    answerSourceLabel='用户转述教师答案',
                    answerSourceName='2026-10-23用户转述老师确认：第166题选C',
                    supplementNotice='第166题按用户转述的老师讲解更正为C（经尿道前列腺切除术）；解析为复习整理。')
            if n in {72, 73, 74}:
                confirmed = {72:'E', 73:'B', 74:'D'}[n]
                g.update(answerRevision=f'20261031-q{n}-{confirmed}-v3',
                    answerSourceLabel='用户确认答案',
                    answerSourceName=f'2026-10-31用户提供的作答截图：第{n}题选{confirmed}',
                    supplementNotice=f'第{n}题按用户作答截图确认为{confirmed}，正常判分；解析为复习整理。')
            if shared_stem:
                g.update(sharedStem=shared_stem,sharedQuestionCount=len(qq))
            if common:
                g['options'] = [{'key':k,'displayKey':k,'label':v} for k,v in qq[0]['options'].items()]
                assert all(q['options']==qq[0]['options'] for q in qq)
            for q in qq:
                num = q['number']
                separate = len(qq)>1 and not common
                key_for = lambda k: f'q{num}-{k}' if separate else k
                category = f'第{num}题选项'
                if not common:
                    for k,v in q['options'].items():
                        o = {'key':key_for(k),'displayKey':k,'label':v}
                        if separate:
                            o['category'] = category
                        g['options'].append(o)
                raw = ANSWERS[num-1]
                adopted = {24:'A',73:'B',103:'A',139:'B',166:'C',172:'A',194:'C'}.get(num,raw)
                s = {'number':num,'sourceQuestion':num,'sourcePage':q['pages'][0],
                    'text':f'第{num}题：{q["text"]}', 'answerRaw':raw,
                    'answer':[key_for(adopted)], 'answerDisplay':adopted,
                    'answerMode':'单选',
                    'answerState':'待原题页核对' if num in PENDING else '按截图及明确更正录入',
                    'lectureId':chapter_id(num), 'knowledgePoint':notes[num][0],
                    'explanation':notes[num][1], 'knowledgeConnections':[notes[num][2]],
                    'explanationOrigin':'复习整理，非出版方官方解析'}
                if separate:
                    s['optionCategory'] = category
                if num in PENDING:
                    s['reviewReason'] = '截图评论列为争议题'
                if num==139:
                    s['answerCorrection'] = {'from':'A','to':'B','source':'用户截图中的作者评论：139选B，气钡灌肠'}
                if num==24:
                    s['answerCorrection'] = {'from':'C','to':'A','source':'用户于2026-10-19明确确认：这道题选A'}
                if num==103:
                    s['answerCorrection'] = {'from':'E','to':'A','source':'用户于2026-10-20明确确认：第102～104题题组的第二小题选A'}
                if num==106:
                    s['answerConfirmation'] = {'answer':'E','source':'用户于2026-10-20明确确认：第105～107题题组的第二小题选E'}
                if num==194:
                    s['answerCorrection'] = {'from':'D','to':'C','source':'用户于2026-10-20明确确认：X线已定位右股骨颈及转子区域病灶，第194题选C'}
                if num==172:
                    s['answerCorrection'] = {'from':'C','to':'A','source':'用户于2026-10-23明确确认：第172题选A（抗结核治疗）'}
                if num==162:
                    s['answerConfirmation'] = {'answer':'B','source':'用户于2026-10-23明确确认：第162题选B（手术探查）'}
                if num==166:
                    s['answerCorrection'] = {'from':'E','to':'C','source':'用户于2026-10-23转述老师确认：第166题选C（经尿道前列腺切除术）'}
                if num in {72, 74}:
                    s['answerConfirmation'] = {'answer':adopted,'source':f'用户于2026-10-31提供作答截图并要求按所选答案更新：第{num}题选{adopted}'}
                if num==73:
                    s['answerCorrection'] = {'from':'A','to':'B','source':'用户于2026-10-31提供作答截图并要求按所选答案更新：第73题选B（血清淀粉酶）'}
                if num in QUESTION_REFS:
                    s['explanationReferences'] = [{'title':REFERENCES[k][0],'url':REFERENCES[k][1]} for k in QUESTION_REFS[num]]
                g['stems'].append(s)
            groups.append(g)
            n = end+1
        assert set(assignment) == {s['number'] for g in groups for s in g['stems']}
        result[subject] = {'meta':{'title':'精选执业医师内、外科真题（上）',
            'sourceName':SOURCE_NAME,'sourcePages':39,'sourceKey':KEY,
            'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'numberingNote':'原PDF未印题号，按原卷阅读顺序对应答案图第1～197题。',
            'groupCount':len(groups),'stemCount':len(assignment),'answerRows':ANSWER_ROWS,
            'pendingQuestions':sorted(PENDING & assignment.keys()),
            'explanationNote':'逐题复习解析及易混点为补充整理，非原卷官方解析；部分争议及版本差异附外部依据。'},
            'groups':groups,'pages':[{'page':p,'sourceKey':KEY,
                'image':f'shared/{KEY}/page-{p:02d}.webp'} for p in range(1,40)]}
    attach_lectures(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--images',type=Path)
    args = parser.parse_args()
    data = build()
    if args.images:
        from PIL import Image
        dest = ROOT/'public/shared'/KEY
        dest.mkdir(parents=True,exist_ok=True)
        for p in range(1,40):
            with Image.open(args.images/f'page-{p:02d}.png') as im:
                im.convert('RGB').save(dest/f'page-{p:02d}.webp',quality=88)
    for subject,content in data.items():
        target = ROOT/f'src/data/{subject}-practitioner-upper-data.json'
        if args.check:
            assert json.loads(target.read_text()) == content
        else:
            target.write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
        print(subject,content['meta']['stemCount'],'questions;',len(content['groups']),'groups')


if __name__ == '__main__':
    main()
