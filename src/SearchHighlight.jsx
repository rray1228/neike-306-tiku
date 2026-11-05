import { highlightParts } from './mnemonic-search.js'

export default function SearchHighlight({ text = '', query = '' }) {
  return highlightParts(text, query).map((part, index) => part.match
    ? <mark className="memory-search-hit" key={index}>{part.text}</mark>
    : part.text)
}
