#!/usr/bin/env node

import fs from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const tesseractModule = process.env.TESSERACT_JS_PATH || 'tesseract.js'
let createWorker
let OEM
let PSM
try {
  ({ createWorker, OEM, PSM } = require(tesseractModule))
} catch {
  console.error('tesseract.js is required; install it or set TESSERACT_JS_PATH to its module directory')
  process.exit(2)
}

if (process.argv.length !== 5) {
  console.error('usage: ocr_pages_tesseract <input-directory> <lang-directory> <output-jsonl>')
  process.exit(2)
}

const [, , inputDirectory, langDirectory, outputPath] = process.argv
const imageNames = (await fs.readdir(inputDirectory))
  .filter((name) => name.toLowerCase().endsWith('.png'))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))

const worker = await createWorker('chi_sim', OEM.LSTM_ONLY, {
  langPath: langDirectory,
  cacheMethod: 'none',
})
await worker.setParameters({
  preserve_interword_spaces: '1',
  tessedit_pageseg_mode: PSM.SPARSE_TEXT,
})

const records = []
for (const [index, imageName] of imageNames.entries()) {
  const imagePath = path.join(inputDirectory, imageName)
  const imageBuffer = await fs.readFile(imagePath)
  const imageWidth = imageBuffer.readUInt32BE(16)
  const imageHeight = imageBuffer.readUInt32BE(20)
  const { data } = await worker.recognize(imagePath, {}, { tsv: true })
  const lines = new Map()
  for (const rawRow of data.tsv.trim().split('\n').slice(1)) {
    const columns = rawRow.split('\t')
    if (columns.length < 12 || Number(columns[0]) !== 5) continue
    const [level, pageNum, blockNum, paragraphNum, lineNum, wordNum, left, top, width, height, confidence, ...textParts] = columns
    const text = textParts.join('\t').trim()
    if (!text) continue
    const key = [pageNum, blockNum, paragraphNum, lineNum].join(':')
    const word = {
      text,
      confidence: Number(confidence),
      left: Number(left),
      top: Number(top),
      right: Number(left) + Number(width),
      bottom: Number(top) + Number(height),
    }
    const line = lines.get(key) || []
    line.push(word)
    lines.set(key, line)
  }

  const columnLines = [...lines.values()].flatMap((words) => {
    const splitX = imageWidth * 0.55
    const leftWords = words.filter((word) => word.left < splitX)
    const rightWords = words.filter((word) => word.left >= splitX)
    return [leftWords, rightWords].filter((columnWords) => columnWords.length)
  })
  const rows = columnLines
    .map((words) => {
      words.sort((a, b) => a.left - b.left)
      const left = Math.min(...words.map((word) => word.left))
      const top = Math.min(...words.map((word) => word.top))
      const right = Math.max(...words.map((word) => word.right))
      const bottom = Math.max(...words.map((word) => word.bottom))
      return {
        text: words.map((word) => word.text).join(' ').replace(/\s+/g, ' ').trim(),
        score: words.reduce((sum, word) => sum + word.confidence, 0) / (words.length * 100),
        box: [[left, top], [right, top], [right, bottom], [left, bottom]],
      }
    })
    .sort((a, b) => Math.abs(a.box[0][1] - b.box[0][1]) > 6
      ? a.box[0][1] - b.box[0][1]
      : a.box[0][0] - b.box[0][0])

  const page = Number(path.parse(imageName).name.split('-').at(-1)) || index + 1
  records.push(JSON.stringify({ page, width: imageWidth, height: imageHeight, rows }))
  console.error(`ocr ${index + 1}/${imageNames.length}: ${imageName} (${rows.length} lines)`)
}

await worker.terminate()
await fs.writeFile(outputPath, `${records.join('\n')}\n`)
