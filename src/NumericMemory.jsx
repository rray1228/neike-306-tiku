import Highlight from './SearchHighlight.jsx'
import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import data from './data/numeric-memory-data.json'
import { filterNumericItems, numericAnswerCorrect, numericRangeParts, numericProseRanges, NUMERIC_SUBJECTS } from './numeric-memory.js'
import { useNumericShortcuts } from './useNumericShortcuts.js'
import './numeric-memory.css'

const STORAGE = 'study-numeric-memory-v1'
const OVERVIEW_STORAGE = 'study-numeric-overview-collapsed-v1'
const EMPTY = {}
const asset = path => `${path.startsWith('shared/numeric-memory/') ? (import.meta.env.BASE_URL || '/') : (import.meta.env.VITE_ASSET_BASE || import.meta.env.BASE_URL || '/')}${path}`

function Source({ item, expanded = false }) {
  return <details className="numeric-source" open={expanded || undefined}><summary>讲义出处 · 第 {item.source.pages.join('、')} 页</summary><p>{item.source.file}</p><p>{item.section} · 以本讲义的条件和表述为准</p>{item.source.images?.map((path, index) => <a key={path} href={asset(path)} target="_blank" rel="noreferrer"><img src={asset(path)} alt={`${item.chapter}讲义第${item.source.pages[index]}页，点击放大`} loading="lazy" /></a>)}</details>
}

function SourceDialog({ item, onClose }) {
  const dialogRef = useRef(null)
  useEffect(() => {
    const previous = document.activeElement
    const dialog = dialogRef.current
    dialog.showModal()
    return () => { dialog.close(); if (previous?.isConnected && !previous.disabled) previous.focus({ preventScroll: true }) }
  }, [])
  return <dialog ref={dialogRef} className="numeric-source-dialog" aria-labelledby="numeric-source-title" onCancel={event => { event.preventDefault(); onClose() }}><div className="numeric-source-dialog-heading"><h2 id="numeric-source-title">{item.chapter} · 讲义原页</h2><button className="ghost-button" onClick={onClose}>关闭（Shift / Esc）</button></div><Source item={item} expanded /></dialog>
}

function FactParts({ item, ranges, practice, values, submitted, onChange, query }) {
  return ranges.flatMap(([start, end]) => numericRangeParts(item, start, end)).map((part, i) => part.index === undefined
    ? <Highlight key={i} text={part.text.replace(/\n(?=多有突眼|TRAb|慢性淋巴细胞性|有手术指征)/g, '；').replace(/([A-Za-z])\n(?=[A-Za-z])/g, '$1 ').replace(/\s*\n\s*/g, '')} query={query} />
    : practice ? <label className={`numeric-blank ${submitted ? numericAnswerCorrect(values[part.index] || '', part.answer) ? 'correct' : 'wrong' : ''}`} key={i}><span className="sr-only">第{part.index + 1}空</span><input aria-label={`第${part.index + 1}空`} autoComplete="off" value={values[part.index] || ''} disabled={submitted} onChange={e => onChange(part.index, e.target.value)} style={{ width: `${Math.max(4, Math.min(12, part.answer.length + 2))}ch` }} />{submitted ? <small>{numericAnswerCorrect(values[part.index] || '', part.answer) ? '✓' : `正确：${part.answer}`}</small> : <small>{part.index + 1}</small>}</label>
    : <mark key={i}><Highlight text={part.answer} query={query} /></mark>)
}

function FactTable({ block, item, ...props }) {
  const headerBlanks = block.headerIncluded && block.rows[0].some(cell => cell.ranges.some(([start,end]) => item.blanks.some(blank => blank.start >= start && blank.end <= end)))
  const headers = block.headers.map((text, index) => {
    if (headerBlanks && props.practice && block.rows[0][index]?.ranges.length) {
      text = block.rows[0][index].ranges.flatMap(([start,end]) => numericRangeParts(item,start,end)).map(part => part.index === undefined ? part.text : '____').join('').replace(/\s+/g,'')
    }
    return text === '天天师兄提示' ? '要点' : text || (index ? '对应内容' : '疾病 / 项目')
  })
  const body = block.headerIncluded ? block.rows.slice(1) : block.rows
  return <>{headerBlanks ? <p className="numeric-row numeric-table-definition"><strong>指标定义：</strong>{block.rows[0].map((cell,index) => <span key={index}><FactParts item={item} ranges={cell.ranges} {...props} /> </span>)}</p> : null}<div className={`numeric-table-wrap ${block.columns > 4 ? 'numeric-wide-table' : ''}`}><table className="numeric-table"><thead><tr>{headers.map((header,index) => <th key={index} scope="col"><Highlight text={header} query={props.query} /></th>)}</tr></thead><tbody>{body.map((row,index) => <tr className="numeric-row" key={index}>{row.map((cell,column) => {
    const empty = !cell.context && !cell.ranges.some(([start,end]) => item.text.slice(start,end).trim())
    const rowHeader = column === 0 && block.rowHeader !== false
    const Cell = rowHeader ? 'th' : 'td'
    return <Cell key={column} scope={rowHeader ? 'row' : undefined} data-label={headers[column]} className={empty ? 'numeric-empty-cell' : ''}><span className="numeric-cell-content">{empty ? '—' : cell.context ? <Highlight text={cell.context} query={props.query} /> : <FactParts item={item} ranges={cell.ranges} {...props} />}</span></Cell>
  })}</tr>)}</tbody></table></div></>
}

function FactText({ item, ...props }) {
  const blocks = item.layout || [{ type: 'text', start: 0, end: item.text.length }]
  return <div className="numeric-fact">{blocks.map((block,index) => block.type === 'table'
    ? <FactTable key={index} item={item} block={block} {...props} />
    : <div className="numeric-prose" key={index}>{numericProseRanges(item, block.start, block.end).filter(([start,end]) => item.text.slice(start,end).trim()).map(([start,end]) => <p className="numeric-row" key={start}><FactParts item={item} ranges={[[start,end]]} {...props} /></p>)}</div>)}</div>
}

export default function NumericMemory({ mode = 'practice', targetId, onPractice, onRead, query = '', onQueryChange }) {
  const practice = mode === 'practice'
  const [subject, setSubject] = useState('all')
  const [chapter, setChapter] = useState('')
  const [category, setCategory] = useState('')
  const deferredQuery = useDeferredValue(query)
  const [filter, setFilter] = useState('all')
  const [records, setRecords] = useState(EMPTY)
  const [ready, setReady] = useState(false)
  const [storageError, setStorageError] = useState(false)
  const [currentId, setCurrentId] = useState(targetId || '')
  const [limit, setLimit] = useState(30)
  const [keepReviewId, setKeepReviewId] = useState('')
  const [sourceOpen, setSourceOpen] = useState(false)
  const [overviewCollapsed, setOverviewCollapsed] = useState(false)
  const cardRef = useRef(null)
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE) || '{}')
      if (saved && typeof saved === 'object' && !Array.isArray(saved)) setRecords(saved)
    } catch { setStorageError(true) }
    try { setOverviewCollapsed(localStorage.getItem(OVERVIEW_STORAGE) === 'true') } catch { /* Keep the overview open when preferences are unavailable. */ }
    setReady(true)
  }, [])
  function saveOverviewPreference(collapsed) {
    setOverviewCollapsed(collapsed)
    try { localStorage.setItem(OVERVIEW_STORAGE, String(collapsed)) } catch { /* Collapsing remains usable without storage. */ }
  }
  useEffect(() => {
    if (!ready) return
    try { localStorage.setItem(STORAGE, JSON.stringify(records)) } catch { setStorageError(true) }
  }, [ready, records])
  useEffect(() => {
    if (targetId) { setCurrentId(targetId); setSubject('all'); setChapter(''); setCategory(''); setFilter('all') }
  }, [targetId])
  useEffect(() => { setLimit(30); setKeepReviewId('') }, [subject, chapter, category, deferredQuery, filter])
  const results = useMemo(() => {
    const filterRecords = filter === 'wrong' && keepReviewId ? { ...records, [keepReviewId]: { ...records[keepReviewId], result: 'wrong' } } : records
    return filterNumericItems(data.items, { subject, chapter, category, query: deferredQuery, filter, records: filterRecords })
  }, [subject, chapter, category, deferredQuery, filter, records, keepReviewId])
  const readingItems = useMemo(() => !practice && targetId && results.some(i => i.id === targetId) ? [results.find(i => i.id === targetId), ...results.filter(i => i.id !== targetId)] : results, [practice, targetId, results])
  const chapters = useMemo(() => [...new Map(data.items.filter(i => subject === 'all' || i.subject === subject).map(i => [`${i.subject}:${i.chapter}`, `${NUMERIC_SUBJECTS[i.subject]} · ${i.chapter}`])).entries()], [subject])
  const categories = useMemo(() => [...new Set(data.items.map(i => i.category))], [])
  const index = Math.max(0, results.findIndex(i => i.id === currentId))
  const current = results[index]
  const record = current ? records[current.id] || EMPTY : EMPTY
  const values = record.values || []
  useEffect(() => { setSourceOpen(false) }, [current?.id, practice])
  const update = (id, change) => setRecords(previous => ({ ...previous, [id]: { ...previous[id], ...change } }))
  const favorite = item => update(item.id, { favorite: !records[item.id]?.favorite })
  const move = next => { setCurrentId(results[(next + results.length) % results.length]?.id || ''); setKeepReviewId(''); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  function submit(event) {
    event.preventDefault()
    if (!ready || !current || current.blanks.some((_, i) => !values[i]?.trim())) return
    if (filter === 'wrong') { setKeepReviewId(current.id); setCurrentId(current.id) }
    update(current.id, { submitted: true, result: current.blanks.every((blank, i) => numericAnswerCorrect(values[i], blank.answer)) ? 'correct' : 'wrong' })
  }
  function redo() {
    update(current.id, { values: [], submitted: false })
    window.requestAnimationFrame(() => cardRef.current?.querySelector('.numeric-blank input')?.focus())
  }
  useNumericShortcuts({ enabled: practice && ready && Boolean(current), cardRef, itemId: current?.id,
    submitted: Boolean(record.submitted), sourceOpen, onMove: offset => move(index + offset),
    onSubmit: submit, onRedo: redo, onFavorite: () => favorite(current), onToggleSource: () => setSourceOpen(open => !open) })
  const totals = Object.values(records)
  const filterSummary = [NUMERIC_SUBJECTS[subject] || '内科与外科', chapter.split(':').slice(1).join(':') || '全部章节', category,
    { favorites: '收藏', wrong: '错题重练', new: '未作答' }[filter], query.trim() ? `“${query.trim()}”` : '', `${results.length} 条`].filter(Boolean).join(' · ')
  return <main className="numeric-memory" aria-label={practice ? '数字填空' : '数字速记'}>
    <section className={`numeric-overview ${overviewCollapsed ? 'is-collapsed' : ''}`} aria-label="数字学习范围与筛选">
    <div className="numeric-overview-toolbar"><span title={filterSummary}>{overviewCollapsed ? `${practice ? '数字填空' : '数字速记'} · ${filterSummary}` : '学习范围与筛选'}</span><button type="button" aria-expanded={!overviewCollapsed} aria-controls="numeric-overview-content" onClick={() => saveOverviewPreference(!overviewCollapsed)}>{overviewCollapsed ? '展开筛选区' : '收起筛选区'} <span aria-hidden="true">{overviewCollapsed ? '⌄' : '⌃'}</span></button></div>
    <div id="numeric-overview-content" className="numeric-overview-content" hidden={overviewCollapsed}>
    <div className="numeric-heading"><div><div className="mnemonic-eyebrow">内科 × 外科 / 讲义数字</div><h1>{practice ? '把数字，自己想起来' : '数字与条件，一起记'}</h1><p>{data.items.length} 条知识点 · {data.items.reduce((n, i) => n + i.blanks.length, 0)} 个数字空 · {data.sources.length} 份分章讲义</p></div><button className="ghost-button" onClick={() => practice ? onRead(current?.id) : onPractice(current?.id)}>{practice ? '查阅数字速记' : '开始数字填空'} →</button></div>
    <p className="numeric-intro">覆盖内外科分章讲义的核心精讲、专题串联、易错小结与考点补充文字。保留适用条件和单位；范围用“-”连接，比较符号已在题干中给出。</p>
    <div className="numeric-controls"><label>科目<select aria-label="科目" value={subject} onChange={e => { setSubject(e.target.value); setChapter('') }}><option value="all">内科与外科</option>{Object.entries(NUMERIC_SUBJECTS).map(([id,label]) => <option key={id} value={id}>{label}</option>)}</select></label><label>章节<select aria-label="章节" value={chapter} onChange={e => setChapter(e.target.value)}><option value="">全部章节</option>{chapters.map(([id,label]) => <option key={id} value={id}>{label}</option>)}</select></label><label>类别<select aria-label="类别" value={category} onChange={e => setCategory(e.target.value)}><option value="">全部数字</option>{categories.map(c => <option key={c}>{c}</option>)}</select></label></div>
    <div className="numeric-filter" aria-label="数字练习筛选">{[['all','全部'],['favorites','收藏'],['wrong','错题重练'],['new','未作答']].map(([id,label]) => <button key={id} aria-pressed={filter === id} className={filter === id ? 'active' : ''} onClick={() => setFilter(id)}>{label}</button>)}<span role="status">{results.length} 条 · 已完成 {totals.filter(i => i.result).length} 条 · 待复习 {totals.filter(i => i.result === 'wrong').length} 条</span></div>
    </div>
    </section>
    {storageError ? <p role="alert">浏览器暂时无法保存记录，本次作答仍可继续。</p> : null}
    {!results.length ? <div className="mnemonic-empty"><h2>{filter === 'wrong' ? '当前没有待复习错题' : '没有符合条件的知识点'}</h2><button className="ghost-button" onClick={() => { setSubject('all'); setChapter(''); setCategory(''); onQueryChange(''); setFilter('all') }}>显示全部数字</button></div> : practice ? <>
      <form className="numeric-card" ref={cardRef} onSubmit={submit}><div className="numeric-card-meta"><span><Highlight text={`${NUMERIC_SUBJECTS[current.subject]} · ${current.chapter}`} query={deferredQuery} /></span><span><Highlight text={current.category} query={deferredQuery} /> · {index + 1} / {results.length}</span><button type="button" className="ghost-button" aria-pressed={Boolean(record.favorite)} onClick={() => favorite(current)}>{record.favorite ? '★ 已收藏' : '☆ 收藏'}</button></div><h2><Highlight text={current.section || current.chapter} query={deferredQuery} /></h2><FactText item={current} query={deferredQuery} practice values={values} submitted={record.submitted} onChange={(i,value) => { const next = [...values]; next[i] = value; update(current.id, { values: next }) }} />
      <div className="numeric-submit"><span role="status">{record.submitted ? record.result === 'correct' ? '全部正确' : '已标出需复习的数字，可对照完整知识点' : `请填写 ${current.blanks.length} 个空，单位无需重复填写`}</span>{record.submitted ? <button className="ghost-button" type="button" onClick={redo}>重新作答</button> : <button className="primary-button" disabled={!ready || current.blanks.some((_,i) => !values[i]?.trim())}>提交答案</button>}</div>
      {record.submitted ? <details className="numeric-answer" open><summary>完整知识点</summary><FactText item={current} query={deferredQuery} values={[]} /></details> : null}<Source item={current} /></form>
      <div className="numeric-pager"><button className="ghost-button" onClick={() => move(index - 1)}>← 上一条</button><label>跳转<select aria-label="跳转" value={current.id} onChange={e => setCurrentId(e.target.value)}>{results.map((i,n) => <option key={i.id} value={i.id}>{n+1}. {i.chapter} · {i.section.slice(0,25)}</option>)}</select></label><button className="ghost-button" onClick={() => move(index + 1)}>下一条 →</button></div>
    </> : <><div className="numeric-reading">{readingItems.slice(0,limit).map(item => <article className="numeric-card" key={item.id}><div className="numeric-card-meta"><span><Highlight text={`${NUMERIC_SUBJECTS[item.subject]} · ${item.chapter}`} query={deferredQuery} /></span><span><Highlight text={item.category} query={deferredQuery} /></span><button className="ghost-button" aria-pressed={Boolean(records[item.id]?.favorite)} onClick={() => favorite(item)}>{records[item.id]?.favorite ? '★ 已收藏' : '☆ 收藏'}</button></div><h2><Highlight text={item.section || item.chapter} query={deferredQuery} /></h2><FactText item={item} query={deferredQuery} values={[]} /><Source item={item} /><button className="numeric-practice-link" onClick={() => onPractice(item.id)}>练这一条 →</button></article>)}</div>{results.length > limit ? <button className="ghost-button" onClick={() => setLimit(n => n+30)}>显示更多（{Math.min(limit, results.length)} / {results.length}）</button> : null}</>}
    {practice ? <details className="numeric-shortcut-help"><summary>快捷键（沿用题库操作）</summary><p>A / D：上一空 / 下一空；W / E：上一行 / 下一行；↑ / ↓：切换作答行；← / →：上一条 / 下一条；Enter：提交 / 重新作答；单按 Shift：查看 / 关闭讲义；Esc：关闭讲义；单按 Option（Alt）：收藏 / 取消收藏；⌘ / Ctrl + K：搜索。</p><p>方向键在输入框内保留光标编辑功能；搜索和筛选时不会触发练习快捷键。</p></details> : null}
    {practice && sourceOpen && current ? <SourceDialog item={current} onClose={() => setSourceOpen(false)} /> : null}
    <p className="numeric-storage-note">作答、收藏和错题保存在当前浏览器；两个入口共用同一份知识点和记录。</p>
  </main>
}
