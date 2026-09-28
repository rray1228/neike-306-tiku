"""Targeted second-pass corrections: workbook 89, 93–95, 97; lectures 54/56.

Keep shared parent-level answers when flattening source tables into B-type rows.
Run after older manual replacements so an OCR rebuild cannot undo these fixes.
"""


def repair_cardiac_followup(payload):
    groups = {g['id']: g for g in payload['groups']}
    repairs = {
        'p93-g4': {'B': '一度房室阻滞'},
        'p94-g3': {
            'A': 'P波消失、转而形成f波（比F波幅度小、频率快、形态不一致，V1导联最明显）',
            'G': '心室率、心律与下传情况有关：如心房率250～350次/分，遵循2:1传导时心室率约150次/分',
        },
        'p94-g4': {'A': '逆行P′波或无P波', 'H': '窦性P波'},
        'p95-g2': {'E': 'PR间期恒定延长>0.2s'},
        'p97-g1': {
            'E': '几乎不减慢0期Vmax，缩短动作电位时程（缩短ERP<缩短APD）',
            'F': '显著减慢0期Vmax（显著减慢传导），轻微延长动作电位时程',
        },
    }
    for gid, labels in repairs.items():
        for o in groups[gid]['options']:
            if o['key'] in labels:
                o.update(label=labels[o['key']], sourceText=o['key']+'.'+labels[o['key']])

    groups['p94-g4']['title'] = '窦速、阵发性室上速与房扑鉴别'
    # C belongs to the parent I class, hence to IA, IB AND IC.
    for s in groups['p97-g1']['stems']:
        answer = {'IA类': 'CGJNW', 'IB类': 'CEQTU', 'IC类': 'CFHLV'}.get(s['text'])
        if answer:
            s.update(answer=list(answer), answerMode='多选', sourceText=s['text']+' '+answer)

    # Coronary localisation follows the lecturer's p16 diagram, not lecture56 p28.
    # Keep its source/lecture-consistent answers; do not infer a new key from OCR.
    for gid, lecture, page in [('p89-g2', 54, 16), ('p93-g4', 56, 4),
                               ('p94-g3', 56, 14), ('p94-g4', 56, 4),
                               ('p95-g2', 56, 18), ('p97-g1', 56, 25)]:
        g = groups[gid]
        lid = f'lecture-{lecture}'
        g['lectureIds'] = [lid]
        g['lectureEvidence'] = {
            'lectureId': lid, 'page': page,
            'image': f'med/lecture-pages/{lid}-page-{page:02d}.webp',
            'title': f'第{lecture}讲第{page}页：'+('冠心病心电图定位' if lecture == 54 else '心律失常'),
            'description': f'对应第{lecture}讲第{page}页讲义。',
        }
