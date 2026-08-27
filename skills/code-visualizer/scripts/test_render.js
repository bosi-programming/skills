// Headless check on the page render_graph.py produces.
//
//   python3 scripts/render_graph.py references/example-model.json -o /tmp/cv.html
//   node scripts/test_render.js /tmp/cv.html
//
// It pulls the page's own functions out of the HTML and runs them against the
// page's own model, so what it proves is what the browser would see: the markup
// and the data. It cannot click, so opening a card and leaving the evidence
// view still need a person.

const fs = require('fs');

const path = process.argv[2];
if (!path) {
  console.error('usage: node test_render.js <rendered.html>');
  process.exit(2);
}
const html = fs.readFileSync(path, 'utf8');
const js = html.split('<script>').pop().split('</script>')[0];

const grab = (name) => {
  const i = js.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('missing ' + name);
  let depth = 0, started = false;
  for (let j = i; j < js.length; j++) {
    if (js[j] === '{') { depth++; started = true; }
    else if (js[j] === '}') { depth--; if (started && depth === 0) return js.slice(i, j + 1); }
  }
  throw new Error('unbalanced ' + name);
};

const MODEL = JSON.parse(html.split('type="application/json" id="model">')[1].split('</script>')[0]);
const state = { pattern: null, evidence: null };
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const nodeInfo = id => MODEL._byId[id];

const ctx = { MODEL, state, esc, nodeInfo };
const names = ['patternsFor', 'evIndex', 'diffHtml'];
const api = new Function(...Object.keys(ctx),
  names.map(grab).join('\n') + '\nreturn {' + names.join(',') + '};')(...Object.values(ctx));

let fail = 0;
const ok = (label, cond, extra = '') => {
  console.log((cond ? 'PASS  ' : 'FAIL  ') + label + (extra ? '  :: ' + extra : ''));
  if (!cond) fail++;
};

// ---- evidence registry
const reg = MODEL._evidence || [];
const pat = reg.filter(e => e.kind === 'pattern');
const hunks = reg.filter(e => e.kind === 'hunk');
const flat = [];
(MODEL.patterns || []).forEach((p, i) => (p.evidence || []).forEach(e => flat.push([i, e.ref])));
ok('the registry holds every evidence entry', pat.length === flat.length,
   pat.length + ' of ' + flat.length);
ok('the registry keeps the order the cards numbered them in',
   pat.every((e, i) => e.pattern === flat[i][0] && e.ref === flat[i][1]));
ok('pattern evidence keeps the low indices, so old deep links still land',
   reg.slice(0, flat.length).every(e => e.kind === 'pattern'));
ok('every registry entry declares its kind',
   reg.every(e => e.kind === 'pattern' || e.kind === 'hunk'));
ok('every pattern entry names its pattern', pat.every(e => e.patternName));
ok('evIndex round-trips a ref back to its index',
   pat.every((e, i) => api.evIndex(e.pattern, { ref: e.ref }) === i));
ok('evIndex returns -1 for a ref that is not there',
   api.evIndex(0, { ref: 'nowhere.ts:1' }) === -1);

// ---- note migrated to explanation
ok('note arrives as explanation', pat.every(e => e.explanation !== undefined));
ok('no evidence entry still carries a raw note',
   !(MODEL.patterns || []).some(p => (p.evidence || []).some(e => e.note)));
ok('every evidence entry has an explanation to show', pat.every(e => e.explanation));

// ---- node hunks: the diff a reviewer reads when no pattern covers the file
const modelHunks = [];
(MODEL.nodes || []).forEach(n => (n.hunks || []).forEach(h => modelHunks.push([n.id, h.ref])));
ok('the example model carries node hunks at all', modelHunks.length > 0);
ok('the registry holds every node hunk', hunks.length === modelHunks.length,
   hunks.length + ' of ' + modelHunks.length);
ok('the registry keeps the order the nodes listed them in',
   hunks.every((e, i) => e.node === modelHunks[i][0] && e.ref === modelHunks[i][1]));
ok('every hunk entry points at a real node',
   hunks.every(e => e.node && MODEL._byId[e.node]));
ok('every hunk entry names its node for the header',
   hunks.every(e => e.nodeLabel));
ok('every hunk entry carries a diff, since the ref alone shows nothing',
   hunks.every(e => e.diff));
ok('no hunk entry pretends to belong to a pattern',
   hunks.every(e => e.pattern == null));
const hidx = MODEL._hunks || {};
ok('_hunks maps every node that has hunks', Object.keys(hidx).length ===
   (MODEL.nodes || []).filter(n => (n.hunks || []).length).length);
ok('_hunks points at the right registry entries',
   Object.entries(hidx).every(([id, list]) =>
     list.length === (MODEL._byId[id].hunks || []).length &&
     list.every(i => reg[i] && reg[i].kind === 'hunk' && reg[i].node === id)));
ok('every changed file node in the example shows its diff',
   (MODEL.nodes || [])
     .filter(n => n.layer === 'file' && ['added', 'modified', 'deleted'].includes(n.status))
     .every(n => (n.hunks || []).length > 0));
ok('a hunk diff is coloured the same way evidence is',
   hunks.every(e => api.diffHtml(e.diff).includes('class="h"')));

// ---- test coverage: the answer, the mark, the count, the chip
const changed = (MODEL.nodes || []).filter(
  n => n.layer === 'file' && n.kind !== 'test' &&
       ['added', 'modified', 'deleted'].includes(n.status));
const uncovered = changed.filter(n => n.tests && n.tests.status === 'none');
ok('every changed file node states its coverage', changed.every(n => n.tests));
ok('the example shows at least one uncovered file', uncovered.length > 0);
ok('a claimed coverage always carries refs',
   changed.every(n => n.tests.status === 'none' ||
     (Array.isArray(n.tests.refs) && n.tests.refs.length > 0)));
const svgMark = (t) => (html.match(
  new RegExp('<tspan fill="#[0-9a-f]{6}">' + t + '</tspan>', 'g')) || []).length;
ok('the graph marks every uncovered node', svgMark('no test') === uncovered.length,
   svgMark('no test') + ' for ' + uncovered.length);
ok('the file list marks the same set',
   (html.split('<div class="filelist">')[1].split('</div>\n')[0]
     .match(/class="nocov"/g) || []).length === uncovered.length);
ok('the header counts the untested files',
   html.includes('<b>' + uncovered.length + '</b> untested'));
ok('the coverage chip exists', html.includes('data-cover="none"'));
ok('the coverage chip starts off',
   /data-cover="none" aria-pressed="false"/.test(html));
ok('the chip drives one flag the graph reads', js.includes('state.coverOnly'));
ok('a covered node dims when the chip is on',
   js.includes("(n.tests||{}).status !== 'none'"));

// ---- contract surface: what the change asks of callers
const surface = MODEL.surface || [];
const breaking = surface.filter(s => s.breaking);
ok('the model lists a contract surface', surface.length > 0);
ok('every surface entry points at a line', surface.every(s => s.ref));
const spanel = html.split('<div id="surface">')[1].split('id="surface-empty"')[0];
const srows = (spanel.match(/class="card srow/g) || []).length;
ok('the panel renders one card per entry', srows === surface.length,
   srows + ' of ' + surface.length);
ok('a breaking card is marked as breaking',
   (spanel.match(/class="card srow breaking"/g) || []).length === breaking.length);
ok('every card carries its ref as a button',
   (spanel.match(/data-sref="/g) || []).length === surface.length);
ok('a surface entry is a details element, like a pattern card',
   (spanel.match(/<details class="card srow/g) || []).length === surface.length);
ok('no surface card is open by default',
   !/<details class="card srow[^>]*open/.test(spanel));
ok('a long surface name wraps beside its arrow rather than under it',
   /\.srow \.sname\{[^}]*min-width:0/.test(html)
   && /\.srow \.sname\{[^}]*overflow-wrap:anywhere/.test(html));
ok('nothing on the summary can wrap to a line of its own',
   /\.srow>summary\{[^}]*flex-wrap:nowrap/.test(html));
ok('the change word is pinned to the right edge and never breaks',
   /\.srow \.schange\{[^}]*margin-left:auto/.test(html)
   && /\.srow \.schange\{[^}]*white-space:nowrap/.test(html));
ok('the name is the only item that gives way',
   /\.srow \.sname\{[^}]*flex:1 1 auto/.test(html));
const statsbar = html.split('<div class="stats">')[1].split('</div>')[0];
ok('the header counts the breaking changes, and says nothing when there are none',
   breaking.length ? statsbar.includes('<b>' + breaking.length + '</b> breaking')
                   : !statsbar.includes('breaking'));
ok('selecting a node narrows the surface list the way it narrows patterns',
   js.includes('function surfaceFor(') && js.includes('function syncSurface('));
ok('the overview names the breaking entries before anything is clicked',
   js.includes('Breaks for callers'));
ok('deep link surface= is handled', js.includes("h.startsWith('surface=')"));
ok('a surface ref resolves to a node it can jump to',
   surface.some(s => refNodeExists(s.ref)));
ok('the page wires those refs to the node, and disables the ones it cannot',
   js.includes("#surface .reflink[data-sref]") && js.includes("b.disabled = true"));

function refNodeExists(ref) {
  const base = String(ref || '').split(':')[0].split('/').pop();
  return (MODEL.nodes || []).some(
    n => n.id === base || String(n.id).split('/').pop() === base || n.label === base);
}

// ---- history: churn, ownership, and the hotspot mark
const withHist = (MODEL.nodes || []).filter(n => n.history);
const hot = withHist.filter(n => n.history.hotspot);
ok('the model carries churn on its changed files', withHist.length >= 3);
ok('the graph marks every hotspot', svgMark('hot') === hot.length,
   svgMark('hot') + ' for ' + hot.length);
ok('the two marks keep their own colours',
   !hot.length || html.includes('<tspan fill="#e3b341">hot</tspan>'));
ok('a hotspot node says so in its markup',
   (html.match(/data-hot="true"/g) || []).length === hot.length);
ok('the header counts the hotspots',
   hot.length ? html.includes('<b>' + hot.length + '</b> hotspot') : true);
ok('the strip has a column for churn', js.includes('<h4>History</h4>'));
ok('the strip only opens it when the node has history', js.includes('n.history ?'));
ok('churn reads as a sentence, not a row of numbers',
   js.includes('function historyHtml('));
ok('every count in the model is a number',
   withHist.every(n => ['commits_90d', 'authors_90d'].every(
     k => n.history[k] === undefined || typeof n.history[k] === 'number')));

// ---- the side panel: nothing scrolls sideways, the long lists fold
ok('the side panel never scrolls sideways', html.includes('overflow-x:hidden'));
ok('a long ref wraps instead of widening the panel',
   html.includes('overflow-wrap:anywhere'));
ok('a file row wraps its badges rather than squeezing the path',
   html.includes('.filelist div{display:flex;gap:8px;padding:4px 0;')
   && /\.filelist div\{[^}]*flex-wrap:wrap/.test(html));
ok('the file list lives in one collapsible card',
   /<details class="card bigcard" id="fileswrap" open>/.test(html));
ok('that card is open by default, so nothing is hidden that was not',
   html.includes('id="fileswrap" open'));
ok('the card counts the files it holds',
   html.includes('<span class="count">' +
     (MODEL.nodes || []).filter(n => n.layer === 'file').length + '</span>'));
ok('the old bare heading is gone', !html.includes('<h2>Files changed</h2>'));

// ---- the strip and the evidence view carry hunks
ok('the strip lists the changed lines of the selected node',
   js.includes('<h4>Changed lines</h4>'));
ok('the strip only opens that column when there is a hunk to show',
   js.includes('hix.length ?'));
ok('the evidence view labels a hunk by its node, not by a pattern',
   js.includes('changed lines in'));
ok('the evidence view heading adapts to a hunk',
   js.includes('What this hunk does'));
ok('the evidence view can jump from a hunk back to its node',
   js.includes('data-goto="${') && js.includes("host.querySelectorAll('[data-goto]')"));
ok('the strip lists the tests of the selected node', js.includes('<h4>Tests</h4>'));
ok('the strip only opens that column when the node has an answer',
   js.includes('n.tests ?'));
ok('a test ref that names a node in the graph becomes a jump',
   js.includes('refNode('));
ok('a test ref outside the graph stays plain text',
   js.includes('reflink mono" data-goto') && js.includes('<span class="mono">'));

// ---- diff rendering
const withDiff = reg.find(e => e.diff);
ok('at least one evidence entry carries a diff', !!withDiff);
if (withDiff) {
  const d = api.diffHtml(withDiff.diff);
  ok('an added line is coloured', d.includes('class="a"'));
  ok('a removed line is coloured', reg.some(e => api.diffHtml(e.diff).includes('class="d"')));
  ok('a hunk header is coloured', d.includes('class="h"'));
}
ok('the diff escapes markup in the hunk',
   api.diffHtml('+<script>alert(1)</script>').includes('&lt;script&gt;'));
ok('the diff leaves no raw tag from the hunk',
   !api.diffHtml('+<script>alert(1)</script>').includes('<script>'));
ok('a missing diff renders a fallback, not an exception',
   api.diffHtml('').includes('No diff captured'));

// ---- pattern cards
const panel = html.split('<div id="patterns">')[1].split('</aside>')[0];
const nPat = (MODEL.patterns || []).length;
ok('every card is a collapsed details element',
   (panel.match(/<details class="card"/g) || []).length === nPat);
ok('no card is open by default', !panel.includes('<details class="card" open'));
ok('every card has an isolate checkbox',
   (panel.match(/type="checkbox" data-iso=/g) || []).length === nPat);
ok('every card links to what the pattern is',
   (panel.match(/class="patref"/g) || []).length >= nPat);
ok('every ref in a card is a button',
   (panel.match(/class="reflink mono" data-ev=/g) || []).length === pat.length);
ok('no card still binds click to pickPattern',
   !js.includes(".card').forEach(c => c.onclick = () => pickPattern"));

// ---- the built-in reference map, and a model override
const cards = panel.split('<details class="card"').slice(1);
const hrefsIn = c => [...c.matchAll(/class="patref" href="([^"]+)"/g)].map(m => m[1]);
const hrefs = hrefsIn(panel);
ok('a GoF name resolves to refactoring.guru',
   hrefs.some(h => h.startsWith('https://refactoring.guru/design-patterns/')));
ok('every card carries at least one link', cards.every(c => hrefsIn(c).length >= 1));
ok('a classic pattern also links to a patterns.dev vanilla page',
   cards.some(c => hrefsIn(c).some(u => /patterns\.dev\/vanilla\/.+/.test(u))));
ok('no link lands on a patterns.dev index page',
   hrefs.every(u => !/^https:\/\/www\.patterns\.dev\/(vanilla|react)\/?$/.test(u)));
ok('the family link comes second, after the specific one',
   cards.every(c => {
     const h = hrefsIn(c);
     const i = h.findIndex(u => u.startsWith('https://www.patterns.dev/'));
     return i === -1 || i === h.length - 1;
   }));
ok('no card repeats the same url twice',
   cards.every(c => new Set(hrefsIn(c)).size === hrefsIn(c).length));
const override = (MODEL.patterns || []).find(p => p.reference);
ok('a model-level reference is present to override with', !!override);
if (override) {
  const card = cards.find(c => c.includes(override.reference));
  ok('the model reference wins', !!card);
  ok('the family link survives a model override',
     !!card && hrefsIn(card).some(u => u.startsWith('https://www.patterns.dev/')));
}

ok('the collapse marker is a real character, not a broken CSS escape',
   html.includes('summary::before{content:"\u25b8"'));

// ---- the strip gives its prose the full width now that the columns are gone
ok('the node branch has no empty column wrapper',
   (js.match(/<div class="cols">\s*<\/div>/g) || []).length === 0);
ok('the prose expands when nothing shares the row',
   html.includes('.body:not(:has(.cols)) .prose{flex:1 1 100%}'));

// ---- zoom
ok('wheel deltas are normalised per device', js.includes('e.deltaMode === 1'));
ok('a single wheel event is capped', js.includes('Math.max(-50, Math.min(50, dy))'));
ok('a trackpad pinch gets its own rate', js.includes("e.ctrlKey ? 0.02 : 0.005"));

// ---- strip columns
ok('the strip dropped Used by', !js.includes('<h4>Used by</h4>'));
ok('the strip dropped Depends on', !js.includes('<h4>Depends on</h4>'));
ok('the strip dropped Patterns here', !js.includes('<h4>Patterns here</h4>'));
ok('the overview dropped Where the change lands', !js.includes('Where the change lands'));
ok('the overview dropped its pattern list', !js.includes('<h4>Patterns found</h4>'));

// ---- deep links
['node=', 'pattern=', 'evidence='].forEach(k =>
  ok('deep link ' + k + ' is handled', js.includes("h.startsWith('" + k + "')")));

// ---- self-contained
ok('the page loads nothing over the network',
   !/<(script|link|img)[^>]+(src|href)="https?:/.test(html));

console.log(fail ? '\n' + fail + ' FAILED' : '\nall green');
process.exit(fail ? 1 : 0);
