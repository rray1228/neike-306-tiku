import { lazy, Suspense, useEffect, useState } from 'react'
import catalog from './data/supplement-tests-catalog.json'
import './supplement-tests.css'

const StudyApp = lazy(() => import('./App.jsx'))
const subjects = ['全部', ...new Set(catalog.map(paper => paper.subjectLabel))]

export default function SupplementTests() {
  const [selected, setSelected] = useState(null)
  const [subject, setSubject] = useState('全部')
  const [query, setQuery] = useState('')
  const [invalidPaper, setInvalidPaper] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    function readPaper() {
      const id = new URLSearchParams(window.location.search).get('paper')
      const paper = catalog.find(item => item.id === id)
      setSelected(paper || null)
      setInvalidPaper(Boolean(id && !paper))
    }
    readPaper()
    setReady(true)
    window.addEventListener('popstate', readPaper)
    return () => window.removeEventListener('popstate', readPaper)
  }, [])

  function openPaper(paper) {
    setSelected(paper)
    setInvalidPaper(false)
    const url = new URL(window.location.href)
    if (paper) url.searchParams.set('paper', paper.id)
    else url.searchParams.delete('paper')
    window.history.pushState(null, '', url)
    window.scrollTo({ top: 0 })
  }

  if (selected) return <Suspense fallback={<main className="supplement-tests"><p role="status">正在加载测试题…</p></main>}><StudyApp key={selected.id} testPaper={selected} onExitTest={() => openPaper(null)} /></Suspense>

  const visible = catalog.filter(paper => (subject === '全部' || paper.subjectLabel === subject) && `${paper.title} ${paper.category}`.includes(query.trim()))
  return <main className="supplement-tests">
    <header className="tests-page-header"><a href="/" className="tests-brand">西综题库</a><a href="/" className="tests-return">← 返回原题库</a></header>
    <section className="tests-intro"><p className="tests-eyebrow">补充测试</p><h1>补充的测试题，都在这里</h1><p>按试卷集中作答。原题库里的题目继续保留，两个入口共用作答记录。</p><span>{catalog.length} 份测试 · {catalog.reduce((sum, paper) => sum + paper.stemCount, 0)} 个小题</span></section>
    <div className="tests-toolbar"><nav aria-label="按科目筛选测试">{subjects.map(label => <button key={label} disabled={!ready} aria-pressed={subject === label} className={subject === label ? 'active' : ''} onClick={() => setSubject(label)}>{label}</button>)}</nav><label className="tests-search"><span className="tests-sr-only">搜索测试卷</span><input type="search" disabled={!ready} placeholder="搜索测试卷" value={query} onChange={event => setQuery(event.target.value)} /></label></div>
    {invalidPaper && <p role="status" className="tests-empty">这份测试暂未收录，请从下方选择。</p>}
    <section className="tests-grid" aria-label="测试卷列表">{visible.map(paper => <article className="test-paper-card" key={paper.id}><div className="test-paper-meta"><span>{paper.subjectLabel}</span><span>{paper.category}</span></div><h2>{paper.title}</h2><p>{paper.groupCount} 个题组 · {paper.stemCount} 个小题</p><button disabled={!ready} onClick={() => openPaper(paper)} aria-label={`进入${paper.title}作答`}>进入作答 <span aria-hidden="true">→</span></button></article>)}</section>
    {!visible.length && <div className="tests-empty"><p>没有找到匹配的测试卷</p><button onClick={() => { setSubject('全部'); setQuery('') }}>显示全部测试</button></div>}
    <footer className="tests-footer">后续补充的测试卷会继续收录在这里。</footer>
  </main>
}
