import { useEffect, useMemo, useState } from 'react'
import content from './data/med-data.json'

const TOPIC_ICONS = {
  呼吸: 'lungs',
  消化: 'stomach',
  肾脏: 'kidney',
  循环: 'heart',
  血液: 'drop',
  内分泌: 'spark',
  风湿: 'joint',
  中毒: 'skull',
  综合: 'grid',
}

const CORRECTIONS = {
  'p02-g1:12': {
    title: '讲义校对 · 规范化识别',
    body: 'COPD 在长效支气管扩张剂基础上加用 ICS 的指征，讲义列为：急性加重住院史、每年 ≥2 次中度急性加重、血嗜酸性粒细胞 ≥300/μl、哮喘史或伴哮喘特征。原图中的 “1” 按选项序号应规范为 “I”。',
  },
  'p03-g1:0': {
    title: '讲义校对 · AECOPD 分级',
    body: '原图 OCR 将罗马数字和答案泡连在一起，已按页面视觉内容恢复为 I 级 = A、C、D；II 级 = B、D、E；III 级 = B、E、F。',
  },
  'p11-g2:3': {
    title: '讲义校对 · 首选药物',
    body: '支气管哮喘长期控制炎症的首选是吸入型糖皮质激素（ICS）；急性发作的迅速缓解首选 SABA。这里保留原题的药物共用选项组，不改成普通单选题。',
  },
  'p79-g1:8': {
    title: '讲义校对 · 高血压急症',
    body: '高血压急症降压节奏：1 小时内降幅不超过 25%，2–6 小时降至约 160/100 mmHg，24–48 小时逐步降至正常；不应一次性快速降到正常。',
  },
}

function Icon({ name, size = 20, stroke = 'currentColor' }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }
  const paths = {
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H19v16H6.5A2.5 2.5 0 0 0 4 21.5z" /><path d="M4 5.5v16M8 7h7M8 11h7" /></>,
    search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
    sliders: <><path d="M4 6h16M4 12h16M4 18h16" /><circle cx="9" cy="6" r="2" fill="white" /><circle cx="15" cy="12" r="2" fill="white" /><circle cx="11" cy="18" r="2" fill="white" /></>,
    settings: <><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" /><circle cx="12" cy="12" r="4" /></>,
    arrow: <><path d="M5 12h13" /><path d="m13 6 6 6-6 6" /></>,
    chevron: <path d="m7 9 5 5 5-5" />,
    left: <><path d="M19 12H5" /><path d="m11 18-6-6 6-6" /></>,
    right: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    bookmark: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.5L6 21z" />,
    bookmarkFill: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.5L6 21z" fill="currentColor" />,
    note: <><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></>,
    file: <><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v5h4M8 12h8M8 16h6" /></>,
    eye: <><path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z" /><circle cx="12" cy="12" r="2.2" /></>,
    check: <path d="m5 12 4.2 4.2L19 6.5" />,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    lungs: <><path d="M12 5v14M12 10c-2.5-3.8-4.3-5.3-5.5-5.3C5.2 4.7 4 8 4 12.5 4 16 6 18 9 18c1.8 0 3-1.4 3-3.2M12 10c2.5-3.8 4.3-5.3 5.5-5.3C18.8 4.7 20 8 20 12.5 20 16 18 18 15 18c-1.8 0-3-1.4-3-3.2" /></>,
    stomach: <><path d="M8 4c0 3 1 4.5 3.5 5.5 2.5 1 4.5 2.8 4.5 5.5a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8c0-2.5 1.5-4 4-4z" /><path d="M8 4c1 2.5 2.5 3 4 3M16 13c2.5 0 3.5-1 4-3" /></>,
    kidney: <><path d="M9 4C5 3.7 3 7 3 11c0 4 2.2 7 5.3 7 2.2 0 3.7-1.6 3.7-4V8.5C12 5.7 10.8 4 9 4Z" /><path d="M15 4c4-.3 6 3 6 7 0 4-2.2 7-5.3 7-2.2 0-3.7-1.6-3.7-4V8.5C12 5.7 13.2 4 15 4Z" /><path d="M9 14c.5-1 1.3-1.5 3-1.5M15 14c-.5-1-1.3-1.5-3-1.5" /></>,
    heart: <><path d="M20.8 8.8c0 5-8.8 10.2-8.8 10.2S3.2 13.8 3.2 8.8A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 8.8 2.8Z" /><path d="M5 11h3l1.2-2.2 2.1 5 1.4-2.8H19" /></>,
    drop: <><path d="M12 3.5s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11Z" /><path d="M9 16.5a3.5 3.5 0 0 0 3 1.5" /></>,
    spark: <><path d="m12 3 1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z" /></>,
    joint: <><circle cx="8" cy="8" r="3" /><circle cx="16" cy="16" r="3" /><path d="m10 10 4 4M5 12l3-1M19 12l-3 1" /></>,
    skull: <><circle cx="12" cy="10" r="7" /><path d="M9 16v3h6v-3M8.5 10h.1M15.4 10h.1M9 13c1.7 1.2 2.3 1.2 3 0 .7 1.2 1.3 1.2 3 0" /></>,
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    alert: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5M12 16h.01" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  }
  return <svg {...common}>{paths[name] || paths.grid}</svg>
}

function unique(values) {
  return [...new Set(values)]
}

function answerLetters(stem) {
  return unique((stem.answer || []).map((item) => String(item)))
}

function isMultiStem(group, stem) {
  return group.kind !== 'B' || answerLetters(stem).length > 1
}

function normalizeSelection(selection) {
  return unique((selection || []).map((item) => String(item))).sort()
}

function isUnresolvedStem(stem) {
  return stem.answerState === '待原题页核对' || answerLetters(stem).length === 0
}

function sameAnswer(a, b) {
  return JSON.stringify(normalizeSelection(a)) === JSON.stringify(normalizeSelection(b))
}

function readLocalStorage(key, fallback) {
  if (typeof window === 'undefined') return fallback
  try {
    return JSON.parse(window.localStorage.getItem(key) || JSON.stringify(fallback))
  } catch {
    return fallback
  }
}

function topicCounts(groups) {
  const counts = {}
  for (const group of groups) counts[group.topic] = (counts[group.topic] || 0) + group.stems.length
  return counts
}

function App() {
  const counts = useMemo(() => topicCounts(content.groups), [])
  const [topic, setTopic] = useState('呼吸')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('全部题型')
  const [groupIndex, setGroupIndex] = useState(0)
  const [selections, setSelections] = useState(() => readLocalStorage('med-selections', {}))
  const [submitted, setSubmitted] = useState(() => readLocalStorage('med-submitted', {}))
  const [favorites, setFavorites] = useState(() => readLocalStorage('med-favorites', []))
  const [notes, setNotes] = useState(() => readLocalStorage('med-notes', {}))
  const [showSource, setShowSource] = useState(false)
  const [showNote, setShowNote] = useState(false)
  const [mobileEvidence, setMobileEvidence] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => readLocalStorage('med-sidebar-collapsed', false))

  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-selections', JSON.stringify(selections)) }, [selections])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-submitted', JSON.stringify(submitted)) }, [submitted])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-favorites', JSON.stringify(favorites)) }, [favorites])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-notes', JSON.stringify(notes)) }, [notes])
  useEffect(() => { if (typeof window !== 'undefined') window.localStorage.setItem('med-sidebar-collapsed', JSON.stringify(sidebarCollapsed)) }, [sidebarCollapsed])
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth <= 720 && window.localStorage.getItem('med-sidebar-collapsed') === null) setSidebarCollapsed(true)
  }, [])

  const filteredGroups = useMemo(() => {
    const query = search.trim().toLowerCase()
    return content.groups.filter((group) => {
      if (topic !== '全部' && group.topic !== topic) return false
      if (typeFilter !== '全部题型' && group.kindLabel !== typeFilter) return false
      if (!query) return true
      const haystack = [group.title, group.topic, group.sourceText, ...group.options.map((item) => item.label), ...group.stems.map((stem) => stem.text)].join(' ').toLowerCase()
      return haystack.includes(query)
    })
  }, [search, topic, typeFilter])

  useEffect(() => {
    if (groupIndex >= filteredGroups.length) setGroupIndex(0)
  }, [filteredGroups.length, groupIndex])

  const group = filteredGroups[groupIndex] || content.groups[0]
  const currentSelections = selections[group.id] || {}
  const isSubmitted = Boolean(submitted[group.id])
  const totalAnswered = Object.keys(submitted).length
  const currentPage = content.pages.find((item) => item.page === group.page)
  const favorite = favorites.includes(group.id)

  function updateSelection(stemIndex, key) {
    if (isSubmitted) return
    const stem = group.stems[stemIndex]
    setSelections((previous) => {
      const nextGroup = { ...(previous[group.id] || {}) }
      const current = normalizeSelection(nextGroup[stemIndex])
      const multi = isMultiStem(group, stem)
      if (multi) {
        nextGroup[stemIndex] = current.includes(key) ? current.filter((item) => item !== key) : [...current, key]
      } else {
        nextGroup[stemIndex] = [key]
      }
      return { ...previous, [group.id]: nextGroup }
    })
  }

  function submitGroup() {
    setSubmitted((previous) => ({ ...previous, [group.id]: true }))
  }

  function goTo(offset) {
    if (!filteredGroups.length) return
    setGroupIndex((previous) => (previous + offset + filteredGroups.length) % filteredGroups.length)
    setShowSource(false)
    setShowNote(false)
  }

  function jumpTo(index) {
    setGroupIndex(index)
    setShowSource(false)
    setShowNote(false)
  }

  function toggleFavorite() {
    setFavorites((previous) => previous.includes(group.id) ? previous.filter((id) => id !== group.id) : [...previous, group.id])
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Icon name="book" size={23} stroke="white" /></div>
          <div className="brand-copy"><strong>内科题库</strong><span>306 临床医学综合能力（内科）</span></div>
        </div>
        <div className="progress-strip">
          <span>本轮进度</span><strong>{filteredGroups.length ? `${Math.min(groupIndex + 1, filteredGroups.length)} / ${filteredGroups.length} 组` : '暂无匹配题组'}</strong>
          <div className="progress-bar"><i style={{ width: `${filteredGroups.length ? ((groupIndex + 1) / filteredGroups.length) * 100 : 0}%` }} /></div>
          <span>{filteredGroups.length ? Math.round(((groupIndex + 1) / filteredGroups.length) * 100) : 0}%</span>
        </div>
        <div className="top-actions">
          <label className="search-box"><Icon name="search" size={18} /><input value={search} onChange={(event) => { setSearch(event.target.value); setGroupIndex(0) }} placeholder="搜索题目 / 关键词" /><kbd>⌘ K</kbd></label>
          <label className="filter-box"><Icon name="sliders" size={17} /><select value={typeFilter} onChange={(event) => { setTypeFilter(event.target.value); setGroupIndex(0) }}><option>全部题型</option><option>B型题</option><option>多项选择</option><option>匹配 / 归类</option><option>原题页核对</option></select><Icon name="chevron" size={15} /></label>
          <button className="icon-button" aria-label="设置"><Icon name="settings" size={19} /></button>
        </div>
      </header>

      <div className={`workspace ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <aside className="sidebar">
          <div className="sidebar-heading"><div className="sidebar-title">内科章节</div><button className="sidebar-toggle" onClick={() => setSidebarCollapsed((value) => !value)} aria-label={sidebarCollapsed ? '展开章节目录' : '收起章节目录'}><Icon name={sidebarCollapsed ? 'right' : 'left'} size={17} /></button></div>
          <nav className="topic-nav">
            {content.topics.filter((item) => item !== '全部' && item !== '综合').map((item) => (
              <button key={item} className={`topic-link ${topic === item ? 'active' : ''}`} onClick={() => { setTopic(item); setGroupIndex(0) }}>
                <span className="topic-icon"><Icon name={TOPIC_ICONS[item]} size={22} /></span><span>{item}</span><em>{counts[item] || 0}</em>
              </button>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div className="source-stat"><span>题库来源</span><strong>学成选择题（PDF 扫描版）</strong><small>{content.meta.sourcePages} 页 · {content.groups.length} 个题组 · {content.groups.reduce((sum, item) => sum + item.stems.length, 0)} 个题干</small></div>
            <div className="lecture-stat"><span>讲义依据</span><strong>内科讲义 PDF 共 57 份</strong><Icon name="file" size={18} /></div>
          </div>
        </aside>

        <main className="main-content">
          <div className="mobile-topic-row">
            <button className="text-button directory-button" onClick={() => setSidebarCollapsed((value) => !value)}><Icon name={sidebarCollapsed ? 'right' : 'left'} size={16} />{sidebarCollapsed ? '章节' : '收起目录'}</button>
            <select value={topic} onChange={(event) => { setTopic(event.target.value); setGroupIndex(0) }}>{content.topics.map((item) => <option key={item}>{item}</option>)}</select>
            <button className="text-button" onClick={() => setMobileEvidence((value) => !value)}>{mobileEvidence ? '隐藏讲义' : '显示讲义'} <Icon name="file" size={16} /></button>
          </div>
          {!filteredGroups.length && <div className="empty-state"><div className="empty-state-icon"><Icon name="search" size={22} /></div><h1>当前筛选下没有题组</h1><p>“中毒”目前没有独立题组；房早等心律失常题已归入循环系统。</p><button className="primary-button" onClick={() => { setTopic('全部'); setSearch(''); setTypeFilter('全部题型'); setGroupIndex(0) }}>显示全部题库 <Icon name="arrow" size={17} /></button></div>}
          <div className="study-content">
          <div className="breadcrumb"><span>{group.topic || '综合'}</span><Icon name="chevron" size={13} /><span>{group.kindLabel}</span><Icon name="chevron" size={13} /><strong>原题第 {group.page} 页</strong></div>
          <div className="content-heading">
            <div><h1>{group.title || '题库原题'}</h1><p>共用选项组保留在本题组内；每个题干独立作答，提交后逐题反馈。</p></div>
            <div className="heading-actions"><button className={`ghost-button ${favorite ? 'selected' : ''}`} onClick={toggleFavorite}><Icon name={favorite ? 'bookmarkFill' : 'bookmark'} size={17} />{favorite ? '已收藏' : '收藏'}</button><button className="ghost-button" onClick={() => setShowNote((value) => !value)}><Icon name="note" size={17} />笔记</button></div>
          </div>

          {showNote && <div className="note-strip"><Icon name="note" size={17} /><input value={notes[group.id] || ''} onChange={(event) => setNotes((previous) => ({ ...previous, [group.id]: event.target.value }))} placeholder="写下你的易错点或记忆口诀…" /></div>}

          <div className={`study-grid ${group.options.length ? '' : 'no-options'}`}>
          {group.options.length > 0 && <aside className="option-bank option-rail"><div className="section-label"><span>共用选项</span><em>{group.kindLabel}</em></div><div className="option-grid">{group.options.map((option) => <div className="shared-option" key={option.key}><b>{option.key}</b><span>{option.label}</span></div>)}</div><p className="option-rail-hint">选项固定在左侧，右侧题干逐题作答。</p></aside>}
          <div className="question-side">
          <section className="question-card">
            <div className="question-card-top"><span className="question-type">{group.kindLabel}</span><span>题组 {groupIndex + 1} / {filteredGroups.length}</span><span>来源页 {group.page}</span></div>
            <div className="stem-list">
              {group.stems.map((stem, index) => <StemRow key={`${group.id}-${index}`} group={group} stem={stem} index={index} selection={currentSelections[index] || []} submitted={isSubmitted} onSelect={updateSelection} />)}
            </div>
            <div className="question-card-bottom">
              {isSubmitted ? <div className="submit-summary"><Icon name="check" size={18} /><span>已提交 · {group.stems.filter((stem, index) => !isUnresolvedStem(stem) && sameAnswer(currentSelections[index], answerLetters(stem))).length} / {group.stems.filter((stem) => !isUnresolvedStem(stem)).length} 个题干正确{group.stems.some(isUnresolvedStem) ? ` · ${group.stems.filter(isUnresolvedStem).length} 个待原题核对` : ''}</span></div> : <span className="hint-text">完成每个题干后提交；B 型题不会把共用选项拆成单选题。</span>}
              <button className="primary-button" onClick={submitGroup} disabled={isSubmitted}>{isSubmitted ? '已提交' : '提交本题组'}<Icon name="arrow" size={17} /></button>
            </div>
          </section>

          <div className="bottom-nav"><button className="pager-button" onClick={() => goTo(-1)}><Icon name="left" size={18} />上一组</button><span>{groupIndex + 1} / {filteredGroups.length}</span><button className="pager-button" onClick={() => goTo(1)}>下一组<Icon name="right" size={18} /></button></div>
          </div>
          </div>
          </div>
        </main>

        {filteredGroups.length ? <EvidencePanel group={group} page={currentPage} submitted={isSubmitted} showSource={showSource} setShowSource={setShowSource} mobileEvidence={mobileEvidence} setMobileEvidence={setMobileEvidence} /> : <EmptyEvidence />}
      </div>

      {showSource && <SourceModal group={group} page={currentPage} onClose={() => setShowSource(false)} />}
    </div>
  )
}

function StemRow({ group, stem, index, selection, submitted, onSelect }) {
  const answer = answerLetters(stem)
  const multi = isMultiStem(group, stem)
  const unresolved = isUnresolvedStem(stem)
  const correct = submitted && !unresolved && sameAnswer(selection, answer)
  const wrong = submitted && !unresolved && !correct
  const key = `${group.id}:${index}`
  const correction = CORRECTIONS[key]
  const keys = group.options.length ? group.options.map((option) => option.key) : answer
  const modeLabel = unresolved ? '待核对' : (multi ? '多选' : '单选')
  return (
    <div className={`stem-row ${submitted ? (correct ? 'is-correct' : 'is-wrong') : ''}`}>
      <div className="stem-main"><span className="stem-number">{String(index + 1).padStart(2, '0')}</span><div className="stem-copy"><div className="stem-heading"><p>{stem.text || '请结合原题页完成本小题'}</p><span className={`answer-mode ${multi ? 'is-multi' : ''}`}>{modeLabel}</span></div>{multi && !submitted && <small>可选择多个共用选项</small>}</div></div>
      <div className="answer-choices">{keys.map((item) => { const active = selection.includes(item); const isAnswer = submitted && answer.includes(item); return <button key={item} className={`answer-chip ${active ? 'active' : ''} ${submitted && isAnswer ? 'answer' : ''} ${submitted && active && !isAnswer ? 'wrong' : ''}`} onClick={() => onSelect(index, item)} disabled={submitted}>{item}</button> })}</div>
      {submitted && <div className={`result-line ${unresolved ? 'pending' : (correct ? 'ok' : 'bad')}`}><Icon name={unresolved ? 'file' : (correct ? 'check' : 'alert')} size={15} />{unresolved ? '原题页核对：暂不自动判分' : (correct ? '正确' : `讲义/原题答案：${answer.join('、')}`)}{correction && <span className="correction-dot">已校对</span>}</div>}
    </div>
  )
}

function knowledgeSnippets(group, lectures) {
  const raw = [group.title, ...group.stems.map((stem) => stem.text)].join(' ')
  const keywords = unique([
    ...(raw.match(/[\u4e00-\u9fff]{2,8}/g) || []),
    ...(raw.match(/[A-Z][A-Z0-9-]{1,}/g) || []),
  ]).filter((word) => !['内科', '表现', '治疗', '诊断', '患者', '疾病', '相关', '小结', '问'].includes(word))
  const candidates = []
  for (const lecture of lectures) {
    const lines = (lecture.text || '').split(/\n+/).map((line) => line.trim()).filter((line) => line.length >= 14 && line.length <= 320)
    for (const line of lines) {
      const score = keywords.reduce((total, keyword) => total + (line.includes(keyword) ? 1 : 0), 0)
      if (score > 0) candidates.push({ lecture, line, score })
    }
  }
  candidates.sort((a, b) => b.score - a.score || a.line.length - b.line.length)
  const picked = []
  for (const candidate of candidates) {
    if (picked.some((item) => item.line === candidate.line)) continue
    picked.push(candidate)
    if (picked.length >= 4) break
  }
  return picked.length ? picked : lectures.slice(0, 2).map((lecture) => ({ lecture, line: lecture.excerpt, score: 0 }))
}

function KnowledgePanel({ group, lectures }) {
  const snippets = useMemo(() => knowledgeSnippets(group, lectures), [group, lectures])
  const [copied, setCopied] = useState(false)
  const copyText = async () => {
    const text = snippets.map((item) => `${item.lecture.title}\n${item.line}`).join('\n\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }
  return <div className="evidence-section knowledge-section"><div className="evidence-title"><span className="knowledge-icon"><Icon name="file" size={18} /></span><div><h2>讲义知识点</h2><p>从对应PDF提取，可复制到笔记</p></div><button className="copy-button" onClick={copyText}>{copied ? '已复制' : '复制文字'}</button></div><div className="knowledge-body">{snippets.map((item, index) => <article className="knowledge-snippet" key={`${item.lecture.id}-${index}`}><span>{item.lecture.title}</span><p>{item.line}</p></article>)}</div></div>
}

function EvidencePanel({ group, page, submitted, showSource, setShowSource, mobileEvidence, setMobileEvidence }) {
  const lectureItems = group.lectureIds.map((id) => content.lectures.find((lecture) => lecture.id === id)).filter(Boolean)
  return (
    <aside className={`evidence-panel ${mobileEvidence ? 'mobile-visible' : ''}`}>
      <div className="evidence-section evidence-section-top"><div className="evidence-title"><span className="evidence-icon"><Icon name="check" size={18} /></span><div><h2>讲义依据</h2><p>{lectureItems.length ? `已关联 ${lectureItems.length} 份讲义` : '按章节关联讲义'}</p></div><span className="verified-dot"><Icon name="check" size={13} /></span><button className="panel-close" onClick={() => setMobileEvidence(false)} aria-label="关闭讲义"><Icon name="chevron" size={16} /></button></div>
        {lectureItems.slice(0, 4).map((lecture) => <div className="lecture-item" key={lecture.id}><Icon name="file" size={18} /><div><strong>{lecture.title}</strong><span>第 {lecture.number} 份 · {lecture.pageCount} 页</span></div><span className="relevance">相关</span></div>)}
        <div className="all-lectures">查看全部 57 份讲义 <Icon name="right" size={15} /></div>
      </div>
      <KnowledgePanel group={group} lectures={lectureItems} />
      <div className="evidence-section correction-section"><div className="evidence-title"><span className="correction-icon"><Icon name="alert" size={18} /></span><div><h2>勘误说明</h2><p>{submitted ? '已显示原题答案与讲义依据' : '提交后显示逐题核对'}</p></div><button className="panel-close" aria-label="展开勘误"><Icon name="chevron" size={16} /></button></div><div className="correction-body"><div className="source-line"><span>原题来源</span><strong>学成选择题（扫描版） · 第 {group.page} 页</strong></div><p>该题组的蓝色答案已从原图保存。没有强行改成普通单选题；需要看到原图中的共用选项和题干关系时，可打开原题页。</p>{group.stems.map((stem, index) => { const note = CORRECTIONS[`${group.id}:${index}`]; return note ? <div className="manual-note" key={index}><strong>{note.title}</strong><p>{note.body}</p></div> : null })}<button className="source-button" onClick={() => setShowSource(true)}><Icon name="eye" size={16} />查看原题页（第 {group.page} 页）</button></div></div>
      <div className="source-thumb"><img src={page?.image} alt={`题库原题第 ${group.page} 页`} /><button onClick={() => setShowSource(true)}><Icon name="eye" size={16} /></button></div>
    </aside>
  )
}

function EmptyEvidence() {
  return <aside className="evidence-panel empty-evidence"><div className="evidence-section"><div className="evidence-title"><span className="evidence-icon"><Icon name="file" size={18} /></span><div><h2>暂无讲义匹配</h2><p>当前筛选没有题组</p></div></div><div className="empty-evidence-body">切换章节或清除筛选后，这里会显示对应的 57 份内科讲义依据。</div></div></aside>
}

function SourceModal({ group, page, onClose }) {
  return <div className="modal-backdrop" onClick={onClose}><div className="source-modal" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><span>原题页</span><h2>{group.topic} · 第 {group.page} 页</h2></div><button className="icon-button" onClick={onClose} aria-label="关闭"><Icon name="close" size={20} /></button></div><div className="modal-image-wrap"><img src={page?.image} alt={`原题页 ${group.page}`} /></div><div className="modal-footer"><span>图片来自“西综-学成选择题（内科汇总去胶带版）.pdf”</span><button className="primary-button" onClick={onClose}>返回题组 <Icon name="arrow" size={16} /></button></div></div></div>
}

export default App
