import assert from 'node:assert/strict'
import test from 'node:test'
import { analyse } from '../src/composables/useOffers.js'

const entry = path => ({ path, file: { name: path.split('/').at(-1), size: 1024 } })

test('accepts the project appendix folders, skips letters and sorts nested КП numbers', () => {
  const folder = 'Сметный/ПРАЙС-ЛИСТЫ К РАЗДЕЛУ КАЦ №11-МОСТ ТКР2'
  const letter = folder + '/Информационное письмо о смене адреса.pdf'
  const result = analyse([
    entry('Сметный/Смета.docx'), entry(letter),
    ...['3.1.10', '3.10', '3.1.2', '3.1'].map(n => entry(folder + '/КП ' + n + ' Мост.pdf'))
  ])
  assert.deepEqual(result.issues, [])
  assert.deepEqual(result.letters, [letter])
  assert.equal(result.docx.name, 'Смета.docx')
  assert.deepEqual(result.sections[0].files.map(f => f.key), ['3.1', '3.1.2', '3.1.10', '3.10'])
})

test('groups PDFs by section and sorts offers by number', () => {
  const result = analyse([
    entry('Проект/Раздел 2 - Сеть/КП 2.1 Подстанция.pdf'),
    entry('Проект/Раздел 1 - Связь/КП 1.2 Арксеть.pdf'),
    entry('Проект/Раздел 1 - Связь/КП 1.1 Транском.pdf')
  ])
  assert.deepEqual(result.totals, { sections: 2, pdfs: 3 })
  assert.deepEqual(result.sections.map(node => node.number), [1, 2])
  assert.deepEqual(result.sections[0].files.map(file => file.key), ['1.1', '1.2'])
  assert.equal(result.issues.length, 0)
})

test('groups PDFs from archive subfolders instead of listing them one by one', () => {
  const result = analyse([
    entry('Проект/Раздел 1 - Связь/КП 1.1 Сеть.pdf'),
    entry('Проект/Раздел 1 - Связь/арх/КП 1.0 Старое.pdf'),
    entry('Проект/Раздел 1 - Связь/арх/Счёт.pdf'),
    entry('Проект/Раздел 2 - Сеть/архив/КП 2.0 Старое.pdf')
  ])
  assert.equal(result.totals.pdfs, 1)
  assert.deepEqual(result.ignored, [
    { folder: 'Проект/Раздел 1 - Связь/арх', count: 2 },
    { folder: 'Проект/Раздел 2 - Сеть/архив', count: 1 }
  ])
  assert.deepEqual(result.skipped, [{ number: 2, folder: 'Проект/Раздел 2 - Сеть', nested: ['архив'] }])
})

test('rejects files without a КП number', () => {
  const result = analyse([entry('Раздел 1 - Связь/прайс-лист.pdf')])
  assert.equal(result.totals.pdfs, 0)
  assert.match(result.issues.join('\n'), /не начинается с номера КП/)
})

test('rejects duplicate offer numbers in one section', () => {
  const result = analyse([
    entry('Раздел 1 - Связь/КП 1.1 Транском.pdf'),
    entry('Раздел 1 - Связь/КП 1.1 Другой.pdf')
  ])
  assert.equal(result.totals.pdfs, 1)
  assert.match(result.issues.join('\n'), /два КП №1\.1/)
})

test('rejects one section spread across two folders', () => {
  const result = analyse([
    entry('Проект/Раздел 1 - Связь/КП 1.1 Сеть.pdf'),
    entry('Проект/Копия/Раздел 1 - Связь/КП 1.2 Сеть.pdf')
  ])
  assert.match(result.issues.join('\n'), /встречается в двух папках/)
})

test('finds a single project DOCX and reports ambiguity', () => {
  const single = analyse([entry('Проект/Основной.docx'), entry('Проект/Раздел 1 - Связь/КП 1.1 Сеть.pdf')])
  assert.equal(single.docx.name, 'Основной.docx')

  const both = analyse([entry('Проект/Основной.docx'), entry('Проект/Копия.docx')])
  assert.equal(both.docx, undefined)
  assert.match(both.issues.join('\n'), /несколько DOCX/)
})

test('reports a section skipped when its PDFs live only in a subfolder', () => {
  const result = analyse([
    entry('Проект/Раздел 7 - Земполотно/арх/КП 1.1 Грунт.pdf'),
    entry('Проект/Раздел 1 - Связь/КП 1.1 Сеть.pdf')
  ])
  assert.equal(result.totals.sections, 1)
  assert.deepEqual(result.skipped, [{ number: 7, folder: 'Проект/Раздел 7 - Земполотно', nested: ['арх'] }])
})
