const SECTION = /^(?:Раздел\s+|Прайс[-–‑ ]листы\s+к\s+разделу\s+КАЦ\s*№\s*)(\d+)\s*[-–—]\s*(\S.*)$/i
const OFFER = /^КП\s*(\d+(?:\s*\.\s*\d+)+)(?![\d.])/i
const INFO_LETTER = /^Информационное\s+письмо(?:\s|[.\-–—]|$)/i
const MAX_DEPTH = 4

export function emptyAnalysis() {
  return {
    docx: undefined,
    sections: [],
    totals: { sections: 0, pdfs: 0 },
    ignored: [],
    letters: [],
    skipped: [],
    issues: []
  }
}

export function analyse(files) {
  const result = emptyAnalysis()
  const sections = new Map()
  const seen = new Map()
  const ignored = new Map()
  const documents = []

  for (const entry of files) {
    const parts = entry.path.split('/')
    const name = parts.at(-1)
    if (!/\.pdf$/i.test(name) && !/\.docx$/i.test(name)) continue

    const ancestor = sectionAncestor(parts)
    if (ancestor) {
      const node = seen.get(ancestor.number) ?? { folder: ancestor.folder, nested: new Set() }
      seen.set(ancestor.number, node)
    }

    if (/\.docx$/i.test(name)) {
      if (parts.length === 2 && !name.startsWith('~$')) documents.push({ file: entry.file, path: entry.path })
      continue
    }

    const parent = parts.length >= 2 ? parts[parts.length - 2].match(SECTION) : null
    if (!parent) {
      const folder = ancestor ? parts.slice(0, -1).join('/') : (parts.slice(0, -1).join('/') || 'корень')
      ignored.set(folder, (ignored.get(folder) ?? 0) + 1)
      if (ancestor) seen.get(ancestor.number).nested.add(parts.slice(ancestor.index + 1, -1).join('/'))
      continue
    }

    if (parts.length > MAX_DEPTH) {
      result.issues.push(`«${entry.path}» — слишком глубокая вложенность, такой путь не загружается.`)
      continue
    }

    if (INFO_LETTER.test(name)) {
      result.letters.push(entry.path)
      continue
    }

    const number = Number(parent[1])
    const title = parent[2]
    const folder = parts[parts.length - 2]
    const folderKey = parts.slice(0, -1).join('/')
    const offer = name.match(OFFER)
    if (!offer) {
      result.issues.push(`В разделе ${number} файл «${name}» не начинается с номера КП (например, «КП 1.1»).`)
      continue
    }

    const node = sections.get(number) ?? { number, title, folder, folderKey, files: [] }
    if (node.folderKey !== folderKey) {
      result.issues.push(`Раздел ${number} встречается в двух папках: «${node.folder}» и «${folder}».`)
      continue
    }
    const key = offer[1].split('.').map(Number).join('.')
    const duplicate = node.files.find(file => file.key === key)
    if (duplicate) {
      result.issues.push(`В разделе ${number} два КП №${key}: «${duplicate.name}» и «${name}».`)
      continue
    }
    node.files.push({ key, name, path: entry.path, size: entry.file.size, file: entry.file })
    sections.set(number, node)
  }

  if (documents.length > 1) {
    result.issues.push(`Выбрано несколько DOCX: ${documents.map(({ path }) => path.split('/').at(-1)).join(', ')}.`)
  } else if (documents.length === 1) {
    result.docx = documents[0].file
  }

  result.sections = [...sections.values()]
    .map(node => ({ ...node, files: node.files.sort(compareOffers) }))
    .sort((first, second) => first.number - second.number)
  result.totals = {
    sections: result.sections.length,
    pdfs: result.sections.reduce((sum, node) => sum + node.files.length, 0)
  }
  result.ignored = [...ignored]
    .map(([folder, count]) => ({ folder, count }))
    .sort((first, second) => first.folder.localeCompare(second.folder, 'ru'))
  result.skipped = [...seen]
    .filter(([number]) => !sections.has(number))
    .map(([number, node]) => ({ number, folder: node.folder, nested: [...node.nested] }))
    .sort((first, second) => first.number - second.number)
  return result
}

function sectionAncestor(parts) {
  for (let index = parts.length - 2; index >= 0; index -= 1) {
    const match = parts[index].match(SECTION)
    if (match) {
      return {
        index,
        number: Number(match[1]),
        title: match[2],
        folder: parts.slice(0, index + 1).join('/')
      }
    }
  }
  return null
}

function compareOffers(first, second) {
  const a = first.key.split('.').map(Number)
  const b = second.key.split('.').map(Number)
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] !== b[i]) return a[i] - b[i]
  }
  return a.length - b.length
}

export async function collectEntry(entry, depth = 1) {
  if (entry.isFile) {
    const file = await new Promise((resolve, reject) => entry.file(resolve, reject))
    return [{ file, path: entry.fullPath.slice(1) }]
  }
  if (!entry.isDirectory || depth === MAX_DEPTH) return []
  const reader = entry.createReader()
  const files = []
  for (;;) {
    const entries = await new Promise((resolve, reject) => reader.readEntries(resolve, reject))
    if (!entries.length) return files
    for (const child of entries) files.push(...await collectEntry(child, depth + 1))
  }
}

export async function collectDrop(dataTransfer) {
  const entries = Array.from(dataTransfer.items, item => item.webkitGetAsEntry?.()).filter(Boolean)
  const collected = await Promise.all(entries.map(entry => collectEntry(entry)))
  return collected.flat()
}

export function filesFromInput(input) {
  return Array.from(input.files, file => ({ file, path: file.webkitRelativePath }))
}
