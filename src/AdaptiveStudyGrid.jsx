import { Children, useEffect, useLayoutEffect, useRef, useState } from 'react'

export function AdaptiveStudyGrid({ group, children }) {
  const [phone, setPhone] = useState(false)
  const [narrow, setNarrow] = useState(false)
  const gridRef = useRef(null)
  useLayoutEffect(() => {
    const grid = gridRef.current
    const context = document.createElement('canvas').getContext('2d')
    if (!context) return
    const measure = (element) => {
      const style = getComputedStyle(element)
      context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`
      return context.measureText(element.textContent).width
    }
    const update = () => {
      setNarrow(grid.clientWidth < 560)
      const labels = Array.from(grid.querySelectorAll('.shared-option span'))
      if (labels.length) {
        const longest = Math.max(...labels.map(measure))
        // Long options already need wrapping: balance their lines instead of
        // keeping a wide rail just to leave a few characters on the last line.
        const lines = Math.max(1, Math.ceil(longest / 260))
        const bank = grid.querySelector('.option-bank')
        const chrome = bank.offsetWidth - labels[0].offsetWidth
        const width = Math.ceil(Math.max(205, Math.min(340, longest / lines + chrome + 10)))
        grid.style.setProperty('--option-width', `${width}px`)
      }
    }
    update()
    const observer = new ResizeObserver(update)
    observer.observe(grid)
    let active = true
    document.fonts.ready.then(() => { if (active) update() })
    return () => { active = false; observer.disconnect() }
  }, [group])
  useEffect(() => {
    const update = () => {
      const iPad = /iPad/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
      setPhone(!iPad && innerWidth <= 720 && Math.min(screen.width, screen.height) <= 600 && matchMedia('(pointer: coarse)').matches)
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])
  return <div ref={gridRef} className={`study-grid ${group.options.length && !group.judgement && !group.showOptionText ? '' : 'no-options'} ${phone || narrow ? 'stacked-study' : ''}`}>{children}</div>
}

export function AdaptiveAnswerLayout({ minTableWidth, table, children }) {
  const containerRef = useRef(null)
  const [fits, setFits] = useState(false)
  useLayoutEffect(() => {
    const container = containerRef.current
    const update = () => setFits(container.clientWidth >= minTableWidth)
    update()
    const observer = new ResizeObserver(update)
    observer.observe(container)
    return () => observer.disconnect()
  }, [minTableWidth])
  return <div ref={containerRef} className="adaptive-answer-layout">{fits ? table : children}</div>
}

export function BalancedAnswerChoices({ count, children, judgement, className = '' }) {
  const choicesRef = useRef(null)
  const [rowCount, setRowCount] = useState(1)
  useLayoutEffect(() => {
    const choices = choicesRef.current
    const row = choices.closest('.stem-row')
    const context = document.createElement('canvas').getContext('2d')
    const measure = (element) => {
      if (!element || !context) return 0
      const font = getComputedStyle(element)
      context.font = `${font.fontWeight} ${font.fontSize} ${font.fontFamily}`
      return context.measureText(element.textContent).width
    }
    const update = () => {
      const button = choices.querySelector('.answer-chip')
      if (!button) return
      const gap = Number.parseFloat(getComputedStyle(choices).columnGap) || 0
      const buttonWidth = button.offsetWidth
      if (row.classList.contains('compact-stem')) {
        const columns = count > 10 ? Math.ceil(count / 2) : count
        const preferredWidth = columns * buttonWidth + Math.max(0, columns - 1) * gap
        const rowStyle = getComputedStyle(row)
        const width = row.clientWidth - Number.parseFloat(rowStyle.paddingLeft) - Number.parseFloat(rowStyle.paddingRight)
        const text = row.querySelector('.stem-copy p')
        const number = row.querySelector('.stem-number')
        const mode = row.querySelector('.answer-mode')
        const textWidth = measure(text)
        const headingChrome = (number?.offsetWidth || 0) + 12 + (mode ? mode.offsetWidth + 8 : 0)
        // Reserve what this stem needs, rather than arbitrarily giving each
        // column half the row. Short stems leave more room for their choices.
        const stemWidth = Math.min(textWidth + headingChrome + 4, 240)
        const answerWidth = Math.min(preferredWidth, Math.max(buttonWidth, width - stemWidth - 14))
        const sideCapacity = Math.max(1, Math.floor((answerWidth + gap) / (buttonWidth + gap)))
        const stackedCapacity = Math.max(1, Math.floor((width - 30 + gap) / (buttonWidth + gap)))
        const sideRows = Math.ceil(count / sideCapacity)
        const textLines = Math.ceil(textWidth / Math.max(1, width - answerWidth - 14 - headingChrome))
        row.style.setProperty('--answer-width', `${answerWidth}px`)
        row.classList.toggle('stack-answer-choices', width < stemWidth + buttonWidth + 14 || textLines > 3 || (sideRows > 2 && sideRows > Math.ceil(count / stackedCapacity)))
      }
      if (judgement) return
      const style = getComputedStyle(choices)
      const width = choices.clientWidth - Number.parseFloat(style.paddingLeft) - Number.parseFloat(style.paddingRight)
      const capacity = Math.max(1, Math.floor((width + gap) / (buttonWidth + gap)))
      const rows = Math.max(1, Math.ceil(count / capacity))
      setRowCount((previous) => previous === rows ? previous : rows)
    }
    update()
    const observer = new ResizeObserver(update)
    observer.observe(choices)
    observer.observe(row)
    let active = true
    document.fonts.ready.then(() => { if (active) update() })
    return () => { active = false; observer.disconnect() }
  }, [count, judgement])
  const buttons = Children.toArray(children)
  let offset = 0
  const rows = Array.from({ length: rowCount }, (_, index) => {
    const size = Math.floor(count / rowCount) + (index < count % rowCount ? 1 : 0)
    const row = buttons.slice(offset, offset + size)
    offset += size
    return <div className="choice-row" key={index}>{row}</div>
  })
  return <div ref={choicesRef} className={`answer-choices ${judgement ? '' : 'balanced-choices'} ${className}`}>{judgement ? children : rows}</div>
}
