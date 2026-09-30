import { readFileSync } from 'node:fs'

import { densityWarning } from './density.mjs'
import { ACCENTS, NOTICES, PALETTE } from './theme.mjs'

const CLIENT = readFileSync(new URL('./page-client.js', import.meta.url), 'utf8')

const TITLES = Object.freeze({
  class: 'Class diagram',
  sequence: 'Sequence diagram',
  state: 'State diagram',
  profile: 'Profile diagram',
  composite: 'Composite structure diagram',
  component: 'Component diagram',
  deployment: 'Deployment diagram',
  object: 'Object diagram',
  package: 'Package diagram',
  activity: 'Activity diagram',
  er: 'Entity-relationship diagram',
})

const ORIGIN_WORDS = Object.freeze({ code: 'code', description: 'description' })

const ESCAPES = Object.freeze({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })

const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ESCAPES[char])

const STYLE = `
:root { --bg: ${PALETTE.background}; --panel: ${PALETTE.panel}; --element: ${PALETTE.element}; --line: ${PALETTE.line}; --fg: ${PALETTE.text}; --muted: ${PALETTE.muted}; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
header { padding: 24px; }
main { padding: 24px; }
h1 { margin: 0 0 4px; font-size: 22px; }
code { background: var(--element); padding: 1px 5px; border-radius: 4px; }
nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
nav a { color: var(--fg); text-decoration: none; border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 6px; padding: 2px 10px; }
nav a:focus-visible, textarea:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.warning { border: 1px solid ${NOTICES.warningBorder}; background: ${NOTICES.warningBackground}; color: ${NOTICES.warningText}; border-radius: 6px; padding: 8px 12px; }
.diagram { background: var(--panel); border: 1px solid var(--line); border-top: 4px solid var(--accent); border-radius: 8px; padding: 16px 20px; margin: 0 0 24px; }
.diagram h2 { margin: 0 0 8px; font-size: 18px; color: var(--accent); }.why, .note, .status { color: var(--muted); }
.no-basis { font-weight: 600; }
.drawing { overflow: auto; background: var(--bg); border-radius: 6px; padding: 12px; transition: opacity .2s; }
.drawing svg { max-width: 100%; height: auto; }
.drawing.stale { opacity: .35; }
.render-error { white-space: pre-wrap; color: ${NOTICES.errorText}; background: ${NOTICES.errorBackground}; border: 1px solid ${NOTICES.errorBorder}; border-radius: 6px; padding: 8px 12px; }
textarea { width: 100%; min-height: 180px; background: var(--bg); color: var(--fg); border: 1px solid var(--line); border-radius: 6px; padding: 10px; font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; }
summary { cursor: pointer; color: var(--muted); margin: 12px 0 8px; }
`

const originLine = ({ origin, source }) =>
  origin === 'description'
    ? `Drawn from the description: ${escapeHtml(source)}`
    : `Drawn from the code in <code>${escapeHtml(source || '.')}</code>`

const smetanaWarning = () =>
  '<p class="warning" role="note">Graphviz <code>dot</code> was not found, so these diagrams use PlantUML&#39;s built-in smetana layout. Install Graphviz for the standard layout.</p>'

const accentStyle = (type) => `style="--accent: ${ACCENTS[type]}"`

const whyLine = (why) => (why ? `<p class="why"><strong>Chosen:</strong> ${escapeHtml(why)}</p>` : '')

const omittedLine = (omitted) => (omitted ? `<p class="why"><strong>Left out:</strong> ${escapeHtml(omitted)}</p>` : '')

const noBasisBody = (diagram, origin) =>
  `<p class="no-basis">Nothing in the ${ORIGIN_WORDS[origin]} supports this diagram.</p>
<p class="note">${escapeHtml(diagram.noBasis)}</p>`

const densityLine = (source, type) => {
  const warning = densityWarning(source ?? '', type)
  return `<p class="warning density" role="note"${warning ? '' : ' hidden'}>${escapeHtml(warning)}</p>`
}

const drawnBody = (diagram, result = {}) => {
  const failed = Boolean(result.error)
  return `${densityLine(result.source, diagram.type)}
<div class="drawing${failed ? ' stale' : ''}">${result.svg ?? ''}</div>
<pre class="render-error"${failed ? '' : ' hidden'}>${escapeHtml(result.error)}</pre>
<details open>
<summary>Edit the PlantUML source (saved to <code>${escapeHtml(diagram.file)}</code>)</summary>
<textarea spellcheck="false" aria-label="PlantUML source for the ${diagram.type} diagram">${escapeHtml(result.source)}</textarea>
<p class="status" aria-live="polite"></p>
</details>`
}

const sectionHtml = (diagram, results, origin) => {
  const editable = diagram.noBasis ? '' : ' data-editable'
  const body = diagram.noBasis ? noBasisBody(diagram, origin) : drawnBody(diagram, results[diagram.type])
  return `<section class="diagram" id="${diagram.type}" data-type="${diagram.type}"${editable} ${accentStyle(diagram.type)}>
<h2>${TITLES[diagram.type]}</h2>
${whyLine(diagram.why)}
${omittedLine(diagram.omitted)}
${body}
</section>`
}

const navHtml = (diagrams) =>
  `<nav aria-label="Diagrams">${diagrams.map((diagram) => `<a href="#${diagram.type}" ${accentStyle(diagram.type)}>${TITLES[diagram.type]}</a>`).join('')}</nav>`

export const renderPage = ({ manifest, results, smetana }) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UML diagrams</title>
<style>${STYLE}</style>
</head>
<body>
<header>
<h1>UML diagrams</h1>
<p>${originLine(manifest)}</p>
${smetana ? smetanaWarning() : ''}
${navHtml(manifest.diagrams)}
</header>
<main>
${manifest.diagrams.map((diagram) => sectionHtml(diagram, results, manifest.origin)).join('\n')}
</main>
<script>${CLIENT}</script>
</body>
</html>
`
