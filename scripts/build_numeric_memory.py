#!/usr/bin/env python3
"""Import numeric study facts from the core teaching sections, never exam options.

Keep complete numbered paragraphs (including their qualifiers) as the canonical
record. Both reading and cloze practice consume that same record.
"""
import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pypdf import PdfReader
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path('/Users/ray/Desktop/📚 考研备考/🩺 西综/306')
NUMBER = r'\d+(?:\.\d+)?(?:\s*[/~～—–－-]\s*\d+(?:\.\d+)?)*'
UNITS = r'(?:mmHg|cmH2O|mmH2O|mmol|μmol|umol|nmol|pmol|mEq|mIU|IU|mU|μg|ug|mg|kg|ng|pg|ml|mL|mm|cm|kPa|bpm|肋间|g|L|l|m|h|d|s|J|%|％|‰|℃|°C|°|岁|个月|月|小时|分钟|秒钟|秒|天|日|周|年|厘米|毫米|毫升|毫克|克|次|个|枚|倍|片|粒|单位|万|亿|组|种|级|行|度|期|分)'
VALUE = re.compile(r'(?<![A-Za-z\d.])(' + NUMBER + r')\s*(?=' + UNITS + r')')
COMPARE = re.compile(r'[<>≤≥＜＞]\s*([-−]?' + NUMBER + r')')
RATIO = re.compile(r'(?<![A-Za-z\d.])(' + r'\d+\s*[/：:]\s*\d+' + r')(?![\d.])')
RANGE = re.compile(r'(?<![A-Za-z\d.^])(' + r'\d+(?:\.\d+)?\s*[-～–—]\s*\d+(?:\.\d+)?' + r')(?![\d.^])')
POWER = re.compile(r'(10\^\d+(?:\s*[-～–—]\s*10\^\d+)?)')
SPINAL = re.compile(r'(?<![A-Za-z])([CTLS]\d{1,2}(?:\s*[-–—]\s*[CTLS]?\d{1,2})?)(?![A-Za-z\d])')
HINT_PATTERNS = [r'小时候\s*100\s*分、长大\s*60\s*分就是幸福', r'（2\s*岁弹杯子装的果酱）', r'nong-4\s*个字母', r'su-2\s*个字母', r'（最多等你到\s*2\s*岁）', r'（D\s*第\s*4\s*个、G\s*第\s*7\s*个字母）', r'（L4L5S1[^）]*）']
HINT_PATTERNS += [r'（和李医师钉死吧[^）]*）', r'（一山无二虎[^）]*）', r'（5÷2[^）]*）', r'（150\+450[^）]*）', r'（2\+3=5[^）]*）']

def blank_spans(text, chapter):
    spans=set()
    patterns=[VALUE,COMPARE,RATIO,RANGE,POWER]
    if re.search(r'脊|椎|神经损伤|麻醉',chapter): patterns.append(SPINAL)
    patterns += [re.compile(r'(?:血糖降至|休克指数=脉率/收缩压：)\s*(\d+(?:\.\d+)?)'), re.compile(r'心室率=\s*(300)'), re.compile(r'氮和热量比\s*(1):')]
    if '一次限量小结 mg' in text:
        patterns.append(re.compile(r'(?:表面麻醉|局部浸润麻醉|神经阻滞|布比卡因|普鲁卡因)\s*(\d+)'))
    hints=[m.span() for pattern in HINT_PATTERNS for m in re.finditer(pattern,text)]
    for pattern in patterns:
        for m in pattern.finditer(text):
            if not any(a<=m.start(1) and m.end(1)<=b for a,b in hints):spans.add((m.start(1),m.end(1)))
    merged=[]
    for a,b in sorted(spans):
        if merged and a<merged[-1][1]: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else: merged.append((a,b))
    return merged,hints
TOP = re.compile(r'^\d{1,2}[.．、](?!\d)')
SECTION = re.compile(r'^[一二三四五六七八九十]+[、．]')

def category(text):
    if re.search(r'切缘|切除|清扫|距肛|距齿|手术范围', text): return '手术范围'
    if re.search(r'疗程|停药|维持|治疗.*[天周月年]|术后|术前|拆线|随访|复查|拔管', text): return '治疗与随访时间'
    if re.search(r'剂量|mg|μg|ug|ml|mL|滴|口服|注射|输液', text): return '用药与补液'
    if re.search(r'指征|手术|引流|穿刺|急诊|溶栓', text): return '干预条件'
    return '诊断与其他数字'

def extract(path, subject):
    chapter = re.sub(r'^\d+\s+27考研[：:]\s*', '', path.stem).split(' 核心')[0]
    chapter = re.sub(r'^(?:内科|外科)(?:含诊断)?(?:\+病理|\+外科|\+内科)?\s*', '', chapter)
    started = False
    section = ''
    skip_case = False
    block = []
    pages = []
    records = []
    def flush():
        nonlocal block, pages
        text = '\n'.join(block).strip()
        text = re.sub(r'^\d{1,2}[.．、]\s*', '', text)
        text = text.replace('①发热（最常见）：术后 1.4 天吸收热、输血输液等；术后 2.7 天感染可能大', '①发热（最常见）：原讲义此处的时间表述有疑义，暂不作为数字考点。')
        matches,hints = blank_spans(text,chapter)
        if matches and len(text) >= 4:
            # A stable content key keeps saved attempts through import order changes.
            key = hashlib.sha256((subject + chapter + text).encode()).hexdigest()[:14]
            records.append(dict(id='numeric-' + key, subject=subject, chapter=chapter,
                section=section, title=text.split('\n')[0][:90], text=text,
                category=category(text), blanks=[dict(start=a, end=b, answer=text[a:b]) for a,b in matches],
                source=dict(file=path.name, pages=sorted(set(pages)), lecture=int(re.match(r'\d+',path.name)[0]))))
            if hints: records[-1]['hints']=[dict(start=a,end=b) for a,b in hints]
        block, pages = [], []
    for page_no, page in enumerate(PdfReader(path).pages, 1):
        raw = page.extract_text() or ''
        for line in raw.splitlines():
            line = line.strip()
            if re.match(r'^(?:真题解析|思维导图|阶段考试|精选答疑)[·•]',line):
                flush(); started = False; skip_case = False; continue
            if re.match(r'^(?:核心精讲|专题串联|易错小结|考点补充)[·•]',line):
                flush(); started = True; skip_case = False; section = line; continue
            if not started: continue
            if re.match(r'^20\d{2}N\d', line):
                flush(); skip_case = True; continue
            if skip_case:
                if TOP.match(line) or SECTION.match(line) or re.match(r'^（[一二三四五六七八九十]+）',line) or line.startswith(('专题串联·','核心精讲·')):
                    skip_case = False
                else: continue
            if (not line or re.match(r'^[-－]\s*\d+\s*[-－]$', line) or
                any(s in line for s in ['每日计划', '核心精讲很详细', '跨章节和学科', '通过考点分布', '（性感认识', '内科学含诊断学', '外科学 ']) or
                re.match(r'^\(?性感认识',line)):
                continue
            line = line.replace('ttsx', '').strip()
            line = re.sub(r'(?<=[×x])\s*10([369])(?=\s*/)', lambda m:'10'+{'3':'³','6':'⁶','9':'⁹'}[m[1]], line)
            if 'CR 后体内白血病细胞' in line:
                line=re.sub(r'10(10|12|8|9)',lambda m:'10^'+m[1],line)
            if SECTION.match(line) or re.match(r'^（[一二三四五六七八九十]+）',line) or line.startswith(('专题串联·','易错小结·','考点补充·')):
                flush(); section = line
                if blank_spans(line,chapter)[0] and '个维度' not in line:
                    before=len(records);block=[line];pages=[page_no];flush()
                    if len(records)>before:records[-1]['section']='本章数字界值'
                continue
            if TOP.match(line): flush()
            # Preserve source line breaks for tabular values and multi-line conditions.
            block.append(line); pages.append(page_no)
    flush()
    return records

def reviewed_image_items(sources, source):
    """Only manually transcribed and visually verified image values, never raw OCR."""
    output=[]
    for entry in json.loads((ROOT/'scripts/numeric-memory-reviewed-images.json').read_text()):
        match=next(s for s in sources if s['subject']==entry['subject'] and int(re.match(r'\d+',s['file'])[0])==entry['lecture'])
        path=source/('内科' if entry['subject']=='med' else '外科')/'讲义'/match['file']
        chapter=re.sub(r'^\d+\s+27考研[：:]\s*(?:内科含诊断|内科|外科)\s*','',path.stem).split(' 核心')[0]
        text='';blanks=[];rows=[]
        for row in entry['rows']:
            cells=[]
            for cell in row:
                start=len(text)
                cursor=0
                for m in re.finditer(r'\[\[(.*?)\]\]',cell):
                    text+=cell[cursor:m.start()];a=len(text);text+=m[1];blanks.append(dict(start=a,end=len(text),answer=m[1]));cursor=m.end()
                text+=cell[cursor:]+'\n';cells.append(dict(ranges=[[start,len(text)]]))
            rows.append(cells)
        key=hashlib.sha256((entry['subject']+chapter+text).encode()).hexdigest()[:14]
        item=dict(id='numeric-'+key,subject=entry['subject'],chapter=chapter,section=entry['section'],title=entry['section'],text=text,category=category(text),blanks=blanks,
            source=dict(file=match['file'],pages=[entry['page']],lecture=entry['lecture']),reviewedImage=True)
        item['layout']=[dict(type='table',start=0,end=len(text),rows=rows,headers=entry['headers'],headerIncluded=False,rowHeader=True,columns=len(entry['headers']))]
        output.append(item);match['count']+=1
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=DEFAULT)
    parser.add_argument('--render', action='store_true', help='Render missing source pages for in-app verification')
    parser.add_argument('--previous', type=Path, help='Published bank to use as the saved-answer migration baseline')
    args = parser.parse_args()
    items, sources = [], []
    for subject, folder in [('surgery','外科'),('med','内科')]:
        paths = sorted((args.source/folder/'讲义').glob('*.pdf'), key=lambda p:int(re.match(r'\d+',p.name)[0]))
        for path in paths:
            records = extract(path, subject)
            items.extend(records)
            sources.append(dict(subject=subject, file=path.name, count=len(records)))
    items.extend(reviewed_image_items(sources,args.source))
    tasks = {}
    for item in items:
        images = []
        for page in item['source']['pages']:
            relative = f"{item['subject']}/lecture-pages/lecture-{item['source']['lecture']:02d}-page-{page:02d}.webp"
            if not (ROOT/'public'/relative).exists():
                relative = f"shared/numeric-memory/{item['subject']}-{item['source']['lecture']:02d}-page-{page:02d}.webp"
                tasks[relative] = (args.source/('内科' if item['subject']=='med' else '外科')/'讲义'/item['source']['file'], page)
            images.append(relative)
        item['source']['images'] = images
    if args.render:
        def render(task):
            relative, (pdf, page) = task
            target = ROOT/'public'/relative
            if target.exists(): return
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = ROOT/'tmp/numeric-memory'/target.stem
            temporary.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['/Users/ray/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdftoppm', '-f',str(page),'-l',str(page),'-singlefile','-scale-to','1600','-png',str(pdf),str(temporary)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            with Image.open(str(temporary)+'.png') as im: im.convert('RGB').save(target,'WEBP',quality=85)
            Path(str(temporary)+'.png').unlink()
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(render,tasks.items()))
    payload = dict(version=1, sourcePolicy='桌面2027分章讲义的核心精讲、专题串联、易错小结、考点补充文字及人工对照原页核实的图片表格；保留条件与单位；真题选项和思维导图不入库', sources=sources, items=items,
        reviewNotes=[dict(file='35 27考研：外科 围术期 核心-真题-串联-导图 天天师兄.pdf', page=2, issue='原文术后1.4天、2.7天含义有疑义，保留核验提示，不生成答案。'),dict(file='6 27考研：外科 腹腔感染 核心-真题-串联-导图 天天师兄.pdf',page=1,issue='腹膜面积原页仅写约1.5，缺少单位；不推测单位、不生成答案。')])
    previous_path=args.previous or ROOT/'src/data/numeric-memory-data.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else {'items':[]}
    previous_items={item['id']:item for item in previous['items']}
    for item in items:
        old=previous_items.get(item['id'])
        if not old:continue
        old_keys=[(b['start'],b['end'],b['answer']) for b in old['blanks']]
        new_keys=[(b['start'],b['end'],b['answer']) for b in item['blanks']]
        revision=old.get('answerRevision',1)
        migrations=old.get('answerMigrations',[])
        if old_keys!=new_keys:
            migrations=migrations+[dict(fromRevision=revision,toRevision=revision+1,indices=[old_keys.index(key) if key in old_keys else -1 for key in new_keys])]
            revision+=1
        if migrations:item.update(answerRevision=revision,answerMigrations=migrations)
    from layout_numeric_tables import enrich
    enrich(payload, args.source)
    (ROOT/'src/data/numeric-memory-data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    out = ROOT/'tmp/numeric-memory'; out.mkdir(parents=True, exist_ok=True)
    (out/'review.txt').write_text('\n\n'.join(f"{i['id']} {i['subject']} {i['chapter']} / {i['section']} / p{i['source']['pages']}\n{i['text']}\n答案："+' | '.join(b['answer'] for b in i['blanks']) for i in items))
    print(json.dumps(dict(sources=len(sources), items=len(items), blanks=sum(len(i['blanks']) for i in items), bySubject={s:sum(i['subject']==s for i in items) for s in ['surgery','med']}),ensure_ascii=False))

if __name__ == '__main__': main()
