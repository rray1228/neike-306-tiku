import { useEffect, useLayoutEffect, useRef } from 'react'
import { fillNavigationTarget } from './fill-navigation.js'

export function useNumericShortcuts({ enabled, cardRef, itemId, submitted, sourceOpen, onMove, onSubmit, onRedo, onFavorite, onToggleSource }) {
  const activeRow = useRef(0)
  const latest = useRef(null)
  useLayoutEffect(() => { latest.current = { submitted, sourceOpen, onMove, onSubmit, onRedo, onFavorite, onToggleSource } })
  useLayoutEffect(() => { activeRow.current = 0 }, [itemId])
  useEffect(() => {
    if (!enabled) return undefined
    let modifierTap = null
    const cancel = () => { modifierTap = null }
    function context(event) {
      const target = event.target instanceof Element ? event.target : null
      const editable = target?.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"]), [role="textbox"], [role="combobox"]')
      const fillInput = editable?.matches('.numeric-blank input') ? editable : null
      const control = target?.closest('button, a, summary, [role="button"]')
      return { editable, fillInput, control }
    }
    function allowed(event) {
      return !event.defaultPrevented && !event.isComposing && event.keyCode !== 229
        && !event.ctrlKey && !event.metaKey && !event.getModifierState?.('AltGraph')
    }
    function rows() {
      return [...(cardRef.current?.querySelectorAll('.numeric-row') || [])]
        .map(row => [...row.querySelectorAll('.numeric-blank input:not(:disabled)')])
        .filter(row => row.length)
    }
    function focus(input, allRows) {
      if (!input) return
      activeRow.current = Math.max(0, allRows.findIndex(row => row.includes(input)))
      input.focus({ preventScroll: true })
      input.select()
      input.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    }
    function trackFocus(event) {
      if (!event.target?.matches?.('.numeric-blank input')) return
      const allRows = rows()
      activeRow.current = Math.max(0, allRows.findIndex(row => row.includes(event.target)))
    }
    function down(event) {
      const { editable, fillInput, control } = context(event)
      if (event.key === 'Shift' || event.key === 'Alt') {
        if (event.repeat) return
        const single = allowed(event) && (event.key === 'Shift' ? !event.altKey : !event.shiftKey)
        modifierTap = single && (latest.current.sourceOpen ? event.key === 'Shift' : !editable || fillInput)
          ? { key: event.key, code: event.code } : null
        return
      }
      cancel()
      if (!allowed(event) || event.altKey || event.shiftKey) return
      if (latest.current.sourceOpen) {
        if (event.key === 'Escape' && !event.repeat) {
          event.preventDefault(); latest.current.onToggleSource()
        }
        return
      }
      if (control && !control.matches('.numeric-submit button, .numeric-pager button')) return
      if (editable && !fillInput) return
      if (['a', 'd', 'w', 'e'].includes(event.key)) {
        const allRows = rows()
        if (!allRows.length) return
        event.preventDefault()
        if (event.repeat) return
        const row = fillInput ? allRows.findIndex(row => row.includes(fillInput)) : Math.min(activeRow.current, allRows.length - 1)
        focus(fillNavigationTarget(allRows, row, fillInput, event.key), allRows)
        return
      }
      // As in the original workbench, arrows inside an input edit the value.
      if (fillInput && event.key !== 'Enter') return
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Enter'].includes(event.key)) return
      event.preventDefault()
      if (event.repeat) return
      if (event.key === 'Enter') {
        if (latest.current.submitted) latest.current.onRedo()
        else latest.current.onSubmit(event)
      } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        latest.current.onMove(event.key === 'ArrowRight' ? 1 : -1)
      } else {
        const allRows = rows()
        const row = Math.min(Math.max(activeRow.current + (event.key === 'ArrowDown' ? 1 : -1), 0), allRows.length - 1)
        focus(allRows[row]?.[0], allRows)
      }
    }
    function up(event) {
      const tap = modifierTap
      cancel()
      if (!tap || tap.key !== event.key || (tap.code && tap.code !== event.code) || !allowed(event) || event.altKey || event.shiftKey) return
      const { editable, fillInput } = context(event)
      if (!latest.current.sourceOpen && editable && !fillInput) return
      if (tap.key === 'Shift') { event.preventDefault(); latest.current.onToggleSource() }
      else if (!latest.current.sourceOpen) { event.preventDefault(); latest.current.onFavorite() }
    }
    window.addEventListener('keydown', down, true)
    window.addEventListener('keyup', up, true)
    window.addEventListener('focusin', trackFocus)
    window.addEventListener('blur', cancel)
    window.addEventListener('pointerdown', cancel, true)
    return () => {
      window.removeEventListener('keydown', down, true)
      window.removeEventListener('keyup', up, true)
      window.removeEventListener('focusin', trackFocus)
      window.removeEventListener('blur', cancel)
      window.removeEventListener('pointerdown', cancel, true)
    }
  }, [enabled, cardRef, itemId, submitted, sourceOpen, onMove, onSubmit, onRedo, onFavorite, onToggleSource])
}
