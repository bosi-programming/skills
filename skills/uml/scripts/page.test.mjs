import assert from 'node:assert/strict'
import { test } from 'node:test'

import { DIAGRAM_TYPES } from './args.mjs'
import { renderPage } from './page.mjs'

const SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'

const drawn = (type, extra = {}) => ({ type, file: `${type}.puml`, why: null, noBasis: null, ...extra })

const page = ({ origin = 'code', source = 'src/orders', diagrams, results = {}, smetana = false }) =>
  renderPage({ manifest: { origin, source, diagrams }, results, smetana })

const section = (html, type) => {
  const start = html.indexOf(`<section class="diagram" id="${type}"`)
  return html.slice(start, html.indexOf('</section>', start))
}

const scriptOf = (html) => html.split('<script>').pop().split('</script>')[0]

const grab = (js, name) => {
  const start = js.indexOf(`function ${name}(`)
  let depth = 0
  for (let index = js.indexOf('{', start); index < js.length; index += 1) {
    depth += js[index] === '{' ? 1 : js[index] === '}' ? -1 : 0
    if (depth === 0) return js.slice(start, index + 1)
  }
  return ''
}

const fakeSection = () => {
  const classes = new Set()
  const drawing = { innerHTML: '<svg>old</svg>', classList: { add: (name) => classes.add(name), remove: (name) => classes.delete(name) } }
  const error = { hidden: true, textContent: '' }
  const status = { textContent: '' }
  const parts = { '.drawing': drawing, '.render-error': error, '.status': status }
  return { section: { querySelector: (selector) => parts[selector] }, drawing, error, status, classes }
}

const applyResult = (html) => new Function(`${grab(scriptOf(html), 'applyResult')}\nreturn applyResult`)()

test('page: a drawn section inlines its svg', () => {
  const html = page({ diagrams: [drawn('class')], results: { class: { source: '@startuml\n@enduml', svg: SVG } } })
  assert.ok(section(html, 'class').includes(SVG))
})

test('page: sections follow the manifest order', () => {
  const html = page({ diagrams: [drawn('class'), drawn('package')], results: {} })
  assert.ok(html.indexOf('id="class"') < html.indexOf('id="package"'))
})

test('page: sequence section shows why', () => {
  const html = page({ diagrams: [drawn('sequence', { why: 'Checkout is the flow every order takes.' })], results: {} })
  assert.ok(section(html, 'sequence').includes('Checkout is the flow every order takes.'))
})

test('page: noBasis section shows code text and note, no svg', () => {
  const html = page({
    diagrams: [drawn('profile', { file: null, noBasis: 'The code defines no stereotypes.' })],
    results: { profile: { svg: SVG } },
  })
  const profile = section(html, 'profile')
  assert.deepEqual(
    [/Nothing in the code supports this diagram/.test(profile), profile.includes('The code defines no stereotypes.'), profile.includes('<svg')],
    [true, true, false]
  )
})

test('page: description origin uses description wording', () => {
  const html = page({ origin: 'description', source: 'a shop', diagrams: [drawn('object', { file: null, noBasis: 'No instances named.' })] })
  assert.match(section(html, 'object'), /Nothing in the description supports this diagram/)
})

test('page: a no-basis section has no editor', () => {
  const html = page({ diagrams: [drawn('object', { file: null, noBasis: 'None.' })] })
  assert.equal(section(html, 'object').includes('<textarea'), false)
})

test('page: all sections noBasis still renders', () => {
  const html = page({ diagrams: DIAGRAM_TYPES.map((type) => drawn(type, { file: null, noBasis: 'Empty repo.' })) })
  assert.deepEqual(
    [html.startsWith('<!doctype html>'), html.trimEnd().endsWith('</html>'), html.match(/Nothing in the code supports this diagram/g).length],
    [true, true, 9]
  )
})

test('page: smetana shows warning', () => {
  const html = page({ diagrams: [drawn('class')], smetana: true })
  assert.match(html, /Graphviz <code>dot<\/code> was not found/)
})

test('page: graphviz shows no warning', () => {
  const html = page({ diagrams: [drawn('class')], smetana: false })
  assert.equal(/was not found/.test(html), false)
})

test('page: the editor holds the escaped source', () => {
  const html = page({ diagrams: [drawn('class')], results: { class: { source: 'A <|-- B & C', svg: SVG } } })
  assert.ok(section(html, 'class').includes('A &lt;|-- B &amp; C</textarea>'))
})

test('page: the editor has a label naming the diagram', () => {
  const html = page({ diagrams: [drawn('state', { why: 'Order.' })], results: { state: { source: 's', svg: SVG } } })
  assert.match(section(html, 'state'), /<textarea[^>]*aria-label="PlantUML source for the state diagram"/)
})

test('page: a first render that failed shows its error', () => {
  const html = page({ diagrams: [drawn('class')], results: { class: { source: 'x', error: 'Syntax Error? <line 1>' } } })
  assert.ok(section(html, 'class').includes('<pre class="render-error">Syntax Error? &lt;line 1&gt;</pre>'))
})

test('page: each section carries its type accent', () => {
  const html = page({ diagrams: [drawn('component')] })
  assert.match(section(html, 'component'), /style="--accent: #f0883e"/)
})

test('page: the header names the origin and source', () => {
  const html = page({ diagrams: [drawn('class')], source: 'src/orders' })
  assert.match(html, /Drawn from the code in <code>src\/orders<\/code>/)
})

test('page: loads nothing from outside the page', () => {
  const html = page({ diagrams: [drawn('class')], results: { class: { source: 's', svg: SVG } } })
  assert.equal(/<(script|link)[^>]+(src|href)=/.test(html), false)
})

const typeInEditor = (context, keystrokeGaps, waitAfter) => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  const html = page({ diagrams: [drawn('class')] })
  const saves = []
  const listeners = []
  const editor = { value: '', addEventListener: (event, listener) => listeners.push(listener) }
  const status = { textContent: '' }
  const section = { dataset: { type: 'class' }, querySelector: (selector) => (selector === 'textarea' ? editor : status) }
  const document = { querySelectorAll: () => [section] }
  const fetch = (url, options) => saves.push([url, JSON.parse(options.body).source]) && new Promise(() => {})
  new Function('document', 'fetch', 'setTimeout', 'clearTimeout', scriptOf(html))(document, fetch, setTimeout, clearTimeout)
  keystrokeGaps.forEach((gap, index) => {
    context.mock.timers.tick(gap)
    editor.value += String(index)
    listeners.forEach((listener) => listener())
  })
  context.mock.timers.tick(waitAfter)
  return saves
}

test('page: the editor posts 600 ms after the last keystroke', (context) => {
  assert.deepEqual(typeInEditor(context, [0, 300, 300], 600), [['/api/diagram/class', '012']])
})

test('page: the editor waits the full 600 ms before posting', (context) => {
  assert.deepEqual(typeInEditor(context, [0], 599), [])
})

const saveWith = async (context, reply) => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  const html = page({ diagrams: [drawn('class')] })
  const fake = fakeSection()
  const listeners = []
  const editor = { value: '', addEventListener: (event, listener) => listeners.push(listener) }
  const parts = { textarea: editor }
  const section = { dataset: { type: 'class' }, querySelector: (selector) => parts[selector] ?? fake.section.querySelector(selector) }
  const document = { querySelectorAll: () => [section] }
  const fetch = () => Promise.resolve(reply)
  new Function('document', 'fetch', 'setTimeout', 'clearTimeout', scriptOf(html))(document, fetch, setTimeout, clearTimeout)
  editor.value = 'class {'
  listeners.forEach((listener) => listener())
  context.mock.timers.tick(600)
  await new Promise((resolve) => setImmediate(resolve))
  return fake
}

test('page: a failed save says not saved and keeps the drawing', async (context) => {
  const fake = await saveWith(context, { ok: false, status: 500, json: () => ({ error: 'disk full' }) })
  assert.deepEqual(
    [fake.status.textContent, fake.drawing.innerHTML, fake.classes.has('stale'), fake.error.hidden],
    ['Not saved: disk full', '<svg>old</svg>', false, true]
  )
})

test('page: a failed save with no error text names the status', async (context) => {
  const fake = await saveWith(context, { ok: false, status: 413, json: () => ({}) })
  assert.equal(fake.status.textContent, 'Not saved: HTTP 413')
})

test('page: a good save applies the result', async (context) => {
  const fake = await saveWith(context, { ok: true, status: 200, json: () => ({ svg: '<svg>new</svg>' }) })
  assert.deepEqual([fake.status.textContent, fake.drawing.innerHTML], ['Saved.', '<svg>new</svg>'])
})

test('page: client keeps last svg dimmed on error', () => {
  const html = page({ diagrams: [drawn('class')] })
  const fake = fakeSection()
  applyResult(html)(fake.section, { error: 'Syntax Error?' })
  assert.deepEqual(
    [fake.drawing.innerHTML, fake.classes.has('stale'), fake.error.hidden, fake.error.textContent],
    ['<svg>old</svg>', true, false, 'Syntax Error?']
  )
})

test('page: client swaps in a new svg and clears the error', () => {
  const html = page({ diagrams: [drawn('class')] })
  const fake = fakeSection()
  fake.classes.add('stale')
  applyResult(html)(fake.section, { svg: '<svg>new</svg>' })
  assert.deepEqual([fake.drawing.innerHTML, fake.classes.has('stale'), fake.error.hidden], ['<svg>new</svg>', false, true])
})
