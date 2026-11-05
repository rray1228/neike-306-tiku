import Highlight from './SearchHighlight.jsx'
import { memo, useDeferredValue, useEffect, useMemo, useState } from 'react'
import { blockText, indexMnemonics, mnemonicDirectory, MNEMONIC_SUBJECTS, previewBlocks, searchMnemonics } from './mnemonic-search.js'

const PAGE_SIZE = 40


function KnowledgeBlock({ block, query }) {
  const text = blockText(block)
  const separator = block.kind === 'mapping' ? text.indexOf('→') : -1
  if (separator >= 0) return <div className="mnemonic-mapping"><span className="mnemonic-fragment"><Highlight text={text.slice(0, separator).trim()} query={query} /></span><span className="mnemonic-mapping-arrow" aria-hidden="true">→</span><span className="mnemonic-meaning"><Highlight text={text.slice(separator + 1).trim()} query={query} /></span></div>
  return <p className="mnemonic-fact"><Highlight text={text} query={query} /></p>
}

const MnemonicCard = memo(function MnemonicCard({ item, query, favorite, onFavorite }) {
  const [expanded, setExpanded] = useState(false)
  const preview = previewBlocks(item, query)
  const remaining = item.blocks.filter(block => block.kind !== 'mapping' && !preview.includes(block))
  return <article className="mnemonic-card" aria-labelledby={`mnemonic-${item.id}`}>
    <div className="mnemonic-card-heading">
      <div className="mnemonic-card-title">
        <div className="mnemonic-meta">{[...new Set([item.subject, ...(item.locations || []).map(location => location.subject)])].map(subject => <span key={subject} className={`mnemonic-subject mnemonic-subject-${subject}`}>{MNEMONIC_SUBJECTS[subject]}</span>)}<span><Highlight text={item.section || item.chapter} query={query} /></span><span className="mnemonic-number">{String(item.number).padStart(3, '0')}</span></div>
        <h3 id={`mnemonic-${item.id}`}><Highlight text={item.title} query={query} /></h3>
        {item.scope ? <p className="mnemonic-scope"><Highlight text={item.scope} query={query} /></p> : null}
      </div>
      <button className={`mnemonic-save ${favorite ? 'is-saved' : ''}`} aria-label={`${favorite ? '取消收藏' : '收藏'}口诀：${item.title}`} aria-pressed={favorite} title={favorite ? '取消收藏' : '收藏口诀'} onClick={() => onFavorite(item.id, item.alternateIds)}><svg width="18" height="18" viewBox="0 0 24 24" fill={favorite ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9Z" /></svg></button>
    </div>
    <div className="mnemonic-knowledge">{preview.map((block, index) => <KnowledgeBlock key={index} block={block} query={query} />)}</div>
    {remaining.length ? <>
      <button className="mnemonic-expand" aria-expanded={expanded} aria-controls={`mnemonic-detail-${item.id}`} onClick={() => setExpanded(value => !value)}>{expanded ? '收起补充说明' : '补充说明'}<span aria-hidden="true">{expanded ? '−' : '+'}</span></button>
      {expanded ? <div id={`mnemonic-detail-${item.id}`} className="mnemonic-detail">{remaining.map((block, index) => <KnowledgeBlock key={index} block={block} query={query} />)}</div> : null}
    </> : null}
  </article>
})

export default function MnemonicLibrary({ data, query, subject, chapter, favorites, onFavorite, onClear, onNavigate, error, onRetry }) {
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [matchMode, setMatchMode] = useState('auto')
  const [limit, setLimit] = useState(PAGE_SIZE)
  const deferredQuery = useDeferredValue(query)
  const indexed = useMemo(() => indexMnemonics(data?.items || []), [data])
  const directory = useMemo(() => mnemonicDirectory(data?.items || []), [data])
  const options = useMemo(() => ({ query: deferredQuery, subject, chapter, favorites, favoritesOnly }), [deferredQuery, subject, chapter, favorites, favoritesOnly])
  const titleResults = useMemo(() => deferredQuery.trim() ? searchMnemonics(indexed, { ...options, matchMode: 'title' }) : [], [indexed, options, deferredQuery])
  const knowledgeResults = useMemo(() => deferredQuery.trim() ? searchMnemonics(indexed, { ...options, matchMode: 'knowledge' }) : [], [indexed, options, deferredQuery])
  const selectedMode = matchMode === 'auto' ? (titleResults.length ? 'title' : 'knowledge') : matchMode
  const results = useMemo(() => deferredQuery.trim() ? selectedMode === 'title' ? titleResults : knowledgeResults : searchMnemonics(indexed, options), [indexed, options, deferredQuery, selectedMode, titleResults, knowledgeResults])
  const favoriteIds = useMemo(() => new Set(favorites), [favorites])
  const browseDirectory = !query.trim() && !chapter && !favoritesOnly
  const groups = useMemo(() => {
    const grouped = new Map()
    for (const item of results.slice(0, limit)) {
      const key = `${item.subject}:${item.chapter}:${item.section}`
      if (!grouped.has(key)) grouped.set(key, { key, subject: item.subject, chapter: item.chapter, section: item.section, items: [] })
      grouped.get(key).items.push(item)
    }
    return [...grouped.values()]
  }, [results, limit])
  useEffect(() => { setLimit(PAGE_SIZE); setMatchMode('auto') }, [deferredQuery, subject, chapter, favoritesOnly])

  return <div className="mnemonic-page">
    <aside className="mnemonic-directory" aria-label="口诀分类目录"><h2>科目与章节</h2><nav>{directory.map(group => <details key={group.subject} open={subject === group.subject || (subject === 'all' && group.subject === 'med')}><summary><span className={`mnemonic-subject mnemonic-subject-${group.subject}`}>{group.label}</span><span>{group.count}</span></summary><button className={subject === group.subject && !chapter ? 'active' : ''} onClick={() => onNavigate(group.subject, '')}>全部章节</button>{group.chapters.map(item => <button key={item.name} className={chapter === `${group.subject}:${item.name}` ? 'active' : ''} onClick={() => onNavigate(group.subject, `${group.subject}:${item.name}`)}><span>{item.name}</span><small>{item.count}</small></button>)}</details>)}</nav></aside>
    <main className="mnemonic-library" aria-label="五科口诀库">
      <div className="mnemonic-library-heading"><div><div className="mnemonic-eyebrow">{MNEMONIC_SUBJECTS[subject] || '五科'} / 口诀</div><h1>{browseDirectory ? '按章节查找' : '口诀库'}</h1><p>{data ? `${data.items.length.toLocaleString()} 条口诀` : '五科口诀'}<span>口诀 · 对应考点</span></p></div><button className={`mnemonic-favorites-filter ${favoritesOnly ? 'active' : ''}`} aria-pressed={favoritesOnly} onClick={() => setFavoritesOnly(value => !value)}>★ {favoritesOnly ? '已收藏' : '只看收藏'}<span>{favorites.length}</span></button></div>
      {!data ? <div className="mnemonic-empty" role="status"><h2>{error ? '口诀暂时加载失败' : '正在加载五科口诀…'}</h2>{error ? <button className="ghost-button" onClick={onRetry}>重新加载</button> : null}</div> : browseDirectory ? <div className="mnemonic-category-groups">{directory.filter(group => subject === 'all' || subject === group.subject).map(group => <section key={group.subject} className="mnemonic-category-group"><h2><span className={`mnemonic-subject mnemonic-subject-${group.subject}`}>{group.label}</span><small>{group.chapters.length} 个系统／章节 · {group.count} 条</small></h2><div className="mnemonic-chapter-tiles">{group.chapters.map(item => <button key={item.name} onClick={() => onNavigate(group.subject, `${group.subject}:${item.name}`)}><span>{item.name}</span><small>{item.count} 条 {item.sections.size > 1 ? `· ${item.sections.size} 节` : ''}</small><span aria-hidden="true">›</span></button>)}</div></section>)}</div> : <>
        {deferredQuery.trim() ? <div className="mnemonic-search-modes" aria-label="搜索范围"><button className={selectedMode === 'title' ? 'active' : ''} aria-pressed={selectedMode === 'title'} onClick={() => { setMatchMode('title'); setLimit(PAGE_SIZE) }}>口诀 <span>{titleResults.length}</span></button><button className={selectedMode === 'knowledge' ? 'active' : ''} aria-pressed={selectedMode === 'knowledge'} onClick={() => { setMatchMode('knowledge'); setLimit(PAGE_SIZE) }}>知识点 <span>{knowledgeResults.length}</span></button></div> : null}
        <div className="mnemonic-result-bar" role="status" aria-live="polite"><span>{deferredQuery.trim() ? <>“<strong>{deferredQuery.trim()}</strong>” · </> : null}{MNEMONIC_SUBJECTS[subject] || '五科'} · <strong>{results.length}</strong> 条{favoritesOnly ? '收藏' : ''}</span><button onClick={() => { setFavoritesOnly(false); onClear() }}>返回分类</button></div>
        <div className="mnemonic-results" aria-busy={query !== deferredQuery}>{groups.map(group => <section key={group.key} className="mnemonic-result-group"><h2><span>{MNEMONIC_SUBJECTS[group.subject]}</span> / {group.chapter}{group.section ? ` / ${group.section}` : ''}</h2><div>{group.items.map(item => <MnemonicCard key={item.id} item={item} query={deferredQuery} favorite={favoriteIds.has(item.id) || (item.alternateIds || []).some(id => favoriteIds.has(id))} onFavorite={onFavorite} />)}</div></section>)}</div>
        {!results.length ? <div className="mnemonic-empty"><h2>{favoritesOnly ? '没有符合条件的收藏' : '没有找到匹配口诀'}</h2><p>{favoritesOnly ? '点击口诀右侧星标即可收藏。' : '可切换到“知识点”，或换一个疾病名、药物名。'}</p><button className="ghost-button" onClick={() => { setFavoritesOnly(false); onClear() }}>返回分类</button></div> : null}
        {results.length > limit ? <div className="mnemonic-more"><button className="ghost-button" onClick={() => setLimit(value => value + PAGE_SIZE)}>显示更多<span>{Math.min(limit, results.length)} / {results.length}</span></button></div> : null}
      </>}
    </main>
  </div>
}
