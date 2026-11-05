#!/usr/bin/env python3
"""Recover source table cells without changing canonical facts or answer indices."""
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/ray/Desktop/📚 考研备考/🩺 西综/306')

# These source tables put the compared diseases/types in the first row,
# rather than using an empty corner cell. Preserve them as column headings.
COMPARISON_HEADERS = {
    '动脉硬化闭塞症','强直性脊柱炎','低危','轻度','COPD','严重支气管哮喘',
    '毕Ⅰ式','急性肾炎','肾病综合征（肾病性水肿）','遗传球','温抗体型自免溶（多见）',
    '中枢白血病','急粒','急粒部分分化M2','器质性杂音','不稳定型心绞痛','男',
    '二度Ⅰ型房室阻滞',
}
HEADER_LABELS = {'热型','临床分型','心电图','LVEF','瓣膜病','房室阻滞','形成条件','急性阑尾炎','可能可能最可能'}

def normalized(text):
    chars, offsets = [], []
    for index, char in enumerate(text):
        for unit in unicodedata.normalize('NFKC', char):
            if not unit.isspace(): chars.append(unit); offsets.append(index)
    return ''.join(chars), offsets

def layout_table(item, rows):
    canonical, offsets = normalized(item['text'])
    cells, table_chars, owners = [], [], []
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            text = value or ''
            norm, _ = normalized(text)
            cell_id = len(cells)
            cells.append(dict(row=row_index, column=col_index, text=text))
            table_chars.extend(norm); owners.extend([cell_id]*len(norm))
    table_text = ''.join(table_chars)
    matches = SequenceMatcher(None, canonical, table_text, autojunk=False).get_matching_blocks()
    strong = [m for m in matches if m.size >= 8]
    if not strong or sum(m.size for m in strong) < min(25, len(canonical)*.65): return None
    low = strong[0].a; high = strong[-1].a + strong[-1].size
    table_low = strong[0].b; table_high = strong[-1].b + strong[-1].size
    # Include nearby short headers and tail cells, but never unrelated prose.
    changed = True
    while changed:
        changed = False
        for m in matches:
            if not m.size: continue
            if m.a < low and low-(m.a+m.size) <= 5 and table_low-(m.b+m.size) <= 5:
                low, table_low = m.a, m.b; changed = True
            if m.a+m.size > high and m.a-high <= 5 and m.b-table_high <= 5:
                high, table_high = m.a+m.size, m.b+m.size; changed = True
    mapping = {}
    for m in matches:
        for n in range(m.size):
            if low <= m.a+n < high: mapping[offsets[m.a+n]] = owners[m.b+n]
    start, end = offsets[low], offsets[high-1]+1
    if len(mapping) < (high-low)*.8: return None
    # Every original character in this interval belongs to one cell exactly once.
    # Fill PDF typography gaps from adjacent aligned characters in the same row.
    assigned = []
    mapped_positions = sorted(mapping)
    pointer = 0
    for pos in range(start,end):
        while pointer+1<len(mapped_positions) and mapped_positions[pointer+1]<=pos: pointer+=1
        before = mapped_positions[pointer]
        after = mapped_positions[min(pointer+1,len(mapped_positions)-1)]
        nearest = before if abs(pos-before)<=abs(after-pos) else after
        assigned.append(mapping.get(pos,mapping[nearest]))
    for blank in item['blanks']:
        if start <= blank['start'] and blank['end'] <= end:
            counts = defaultdict(int)
            for owner in assigned[blank['start']-start:blank['end']-start]: counts[owner]+=1
            owner=max(counts,key=counts.get)
            assigned[blank['start']-start:blank['end']-start]=[owner]*(blank['end']-blank['start'])
    spans = defaultdict(list)
    previous = None
    for pos, cell_id in zip(range(start,end),assigned):
        if previous == cell_id: spans[cell_id][-1][1] = pos+1
        else: spans[cell_id].append([pos,pos+1])
        previous = cell_id
    selected_rows = sorted({cells[c]['row'] for c in spans})
    # Do not use generic two-word coincidences as a reconstructed source table.
    if not selected_rows: return None
    columns = max(len(row) for row in rows)
    output = []
    for row_index in selected_rows:
        row = [dict(ranges=spans.get(next((j for j,c in enumerate(cells) if c['row']==row_index and c['column']==col),-1),[])) for col in range(columns)]
        if not any(item['text'][a:b].strip() for a,b in row[0]['ranges']):
            for previous in range(row_index,-1,-1):
                label=rows[previous][0]
                if label:
                    row[0]['context']=re.sub(r'\s+','',label); break
                if label is not None: break
        output.append(row)
    first = [re.sub(r'\s+','', value or '') for value in rows[0]]
    comparison = (first[0] in COMPARISON_HEADERS or first[0].startswith(('酯类（','早期（进食后','抓规律：'))) and max(map(len,first))<50
    has_header = (not first[0] or comparison or first[0] in HEADER_LABELS or (bool(re.fullmatch(r'切除范围|复发风险|分型|类型|病理类型|指标|项目|疾病|程度|药物|检查|治疗|病变|正常|异常|病因|分期|部位|时间|分类|类别|名称|表现',first[0])) and sum(map(len,first))<90)) and not re.search(r'[<>≤≥＜＞]\d',''.join(first))
    header_included = has_header and 0 in selected_rows
    headers = first if has_header else ['项目']+['对应内容' if columns==2 else f'要点{c}' for c in range(1,columns)]
    if not has_header and first[0]=='碘剂' and columns==3: headers=['药物类别','代表药物','作用与注意事项']
    if not has_header and first[0]=='阵发性房颤' and columns==3: headers=['类型','持续时间与特点','记忆提示']
    return dict(type='table', start=start, end=end, rows=output,
        headers=headers, headerIncluded=header_included, rowHeader=not comparison, columns=columns)

def enrich(payload, source=SOURCE):
    cache = ROOT/'tmp/numeric-memory/table-cells.json'
    cache.parent.mkdir(parents=True,exist_ok=True)
    cached = json.loads(cache.read_text()) if cache.exists() else {}
    grouped = defaultdict(list)
    for item in payload['items']: grouped[(item['subject'],item['source']['file'])].append(item)
    count = 0
    for (subject, filename), items in grouped.items():
        path = source/('内科' if subject=='med' else '外科')/'讲义'/filename
        pages = sorted({p for i in items for p in i['source']['pages']})
        missing = [p for p in pages if f'{subject}:{filename}:{p}' not in cached]
        if missing:
            with pdfplumber.open(path) as pdf:
                for p in missing: cached[f'{subject}:{filename}:{p}'] = pdf.pages[p-1].extract_tables()
        for item in items:
            candidates=[]
            for p in item['source']['pages']:
                for table in cached[f'{subject}:{filename}:{p}']:
                    if len(table)<2 or max(map(len,table))<2: continue
                    candidate = layout_table(item,table)
                    if candidate: candidates.append(candidate)
            chosen=[]
            for candidate in sorted(candidates,key=lambda c:c['end']-c['start'],reverse=True):
                if not any(candidate['start']<c['end'] and candidate['end']>c['start'] for c in chosen): chosen.append(candidate)
            blocks=[]; cursor=0
            for table in sorted(chosen,key=lambda c:c['start']):
                if cursor<table['start']: blocks.append(dict(type='text',start=cursor,end=table['start']))
                blocks.append(table); cursor=table['end']
            if cursor<len(item['text']): blocks.append(dict(type='text',start=cursor,end=len(item['text'])))
            if chosen: item['layout']=blocks; count+=len(chosen)
            else: item.pop('layout',None)
    cache.write_text(json.dumps(cached,ensure_ascii=False))
    payload['layoutVersion']=1
    return count

if __name__=='__main__':
    path=ROOT/'src/data/numeric-memory-data.json'
    payload=json.loads(path.read_text())
    count=enrich(payload)
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(tables=count,items=sum('layout' in i for i in payload['items'])),ensure_ascii=False))
