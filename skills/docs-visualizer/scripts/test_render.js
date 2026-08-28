// Headless check on the page render_docs_graph.py produces.
//
//   python3 scripts/render_docs_graph.py references/example-model.json -o /tmp/dv.html
//   node scripts/test_render.js /tmp/dv.html
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
const MOVE_COLOR = JSON.parse(js.match(/const MOVE_COLOR = (\{[^}]*\})/)[1]);
const MOVE_REFERENCE = JSON.parse(js.match(/const MOVE_REFERENCE = (\{[^}]*\})/)[1]);
const state = { move: null, pattern: null, evidence: null };
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const nodeInfo = id => MODEL._byId[id];

const ctx = { MODEL, MOVE_COLOR, MOVE_REFERENCE, state, esc, nodeInfo };
const names = ['movesFor', 'moveList', 'patternsFor', 'evIndex', 'diffHtml'];
const api = new Function(...Object.keys(ctx),
  names.map(grab).join('\n') + '\nreturn {' + names.join(',') + '};')(...Object.values(ctx));

let fail = 0;
const ok = (label, cond, extra = '') => {
  console.log((cond ? 'PASS  ' : 'FAIL  ') + label + (extra ? '  :: ' + extra : ''));
  if (!cond) fail++;
};

const flatCount = () => (MODEL.patterns || [])
  .reduce((n, p) => n + (p.evidence || []).length, 0);

// ---- rhetorical moves
const secId = 'docs/onboarding.md#tokens';
const docId = 'docs/onboarding.md';
const sec = api.movesFor(secId);
ok('a section owns its own moves', sec.length === 2, sec.length + ' moves');
ok('a doc inherits every move its sections make', api.movesFor(docId).length === 6);
ok('a doc with no sections has no moves', api.movesFor('CONTRIBUTING.md').length === 0);

const markup = api.moveList(sec);
ok('a move is a collapsible card', markup.includes('<details class="card move"'));
ok('no move card is open by default', !markup.includes('data-move="' + sec[0].i + '" open'));
ok('move markup carries the kind badge', markup.includes('class="mv"'));
ok('move markup carries the verbatim quote', markup.includes('Local tokens never expire'));
ok('move markup carries the ref', markup.includes('docs/onboarding.md:101'));
ok('every move in the model has a ref', (MODEL.moves || []).every(m => m.ref));
ok('a move card links to what the move is', markup.includes('class="patref"'));
ok('every move kind has a reference url',
   (MODEL.moves || []).every(m => MOVE_REFERENCE[(m.kind || '').toLowerCase()]));
ok('a move ref is a button into the evidence view', markup.includes('class="reflink mono" data-ev='));
ok('a move card links back to its node', markup.includes('data-goto='));

state.move = sec[0].i;
ok('a pinned move card opens', api.moveList(sec).includes('data-move="' + sec[0].i + '" open'));
state.move = null;

// ---- moves reach the evidence registry
const slots = MODEL._moveEvidence || {};
ok('every move has a slot in the evidence registry',
   (MODEL.moves || []).every((m, i) => slots[i] != null));
ok('a move slot resolves to that move\'s ref',
   (MODEL.moves || []).every((m, i) => (MODEL._evidence[slots[i]] || {}).ref === m.ref));
ok('move slots sit after the pattern evidence',
   Object.values(slots).every(v => v >= flatCount()));

// ---- evidence registry
const reg = MODEL._evidence || [];
const flat = [];
(MODEL.patterns || []).forEach((p, i) => (p.evidence || []).forEach(e => flat.push([i, e.ref])));
ok('the registry holds every pattern evidence entry and every move',
   reg.length === flat.length + (MODEL.moves || []).length,
   reg.length + ' of ' + (flat.length + (MODEL.moves || []).length));
ok('pattern evidence keeps the numbering the cards gave it',
   flat.every((f, i) => reg[i].pattern === f[0] && reg[i].ref === f[1]));
ok('every registry entry is labelled', reg.every(e => e.patternName));
ok('evIndex round-trips a pattern ref back to its index',
   flat.every((f, i) => api.evIndex(reg[i].pattern, { ref: reg[i].ref }) === i));
ok('evIndex returns -1 for a ref that is not there',
   api.evIndex(0, { ref: 'nowhere.md:1' }) === -1);

// ---- note migrated to explanation
ok('note arrives as explanation', reg.every(e => e.explanation !== undefined));
ok('no evidence entry still carries a raw note',
   !(MODEL.patterns || []).some(p => (p.evidence || []).some(e => e.note)));

// ---- diff rendering
const withDiff = reg.find(e => e.diff);
ok('at least one evidence entry carries a diff', !!withDiff);
if (withDiff) {
  const d = api.diffHtml(withDiff.diff);
  ok('an added line is coloured', d.includes('class="a"'));
  ok('a hunk header is coloured', d.includes('class="h"'));
}
ok('the diff escapes markup in the hunk',
   api.diffHtml('+<script>alert(1)</script>').includes('&lt;script&gt;'));
ok('the diff leaves no raw tag from the hunk',
   !api.diffHtml('+<script>alert(1)</script>').includes('<script>'));
ok('a missing diff renders a fallback, not an exception',
   api.diffHtml('').includes('No diff captured'));

// ---- pattern cards, counted in the panel rather than the whole file, since the
// script block carries the same class names inside the move-card template
const panel = html.split('<div id="patterns">')[1].split('</aside>')[0];
const nPat = (MODEL.patterns || []).length;
ok('every card is a collapsed details element',
   (panel.match(/<details class="card"/g) || []).length === nPat);
ok('no card is open by default', !panel.includes('<details class="card" open'));
ok('every card has an isolate checkbox',
   (panel.match(/type="checkbox" data-iso=/g) || []).length === nPat);
ok('every card links to what the pattern is',
   (panel.match(/class="patref"/g) || []).length === nPat);
ok('every pattern ref in a card is a button',
   (panel.match(/class="reflink mono" data-ev=/g) || []).length === flat.length);
ok('no card still binds click to pickPattern',
   !js.includes(".card').forEach(c => c.onclick = () => pickPattern"));

ok('the collapse marker is a real character, not a broken CSS escape',
   html.includes('summary::before{content:"\u25b8"'));

// ---- strip columns
ok('the strip kept Rhetorical moves', js.includes('<h4>Rhetorical moves'));
ok('the strip dropped Depends on', !js.includes('<h4>Depends on</h4>'));
ok('the strip dropped Patterns here', !js.includes('<h4>Patterns here</h4>'));
ok('the overview dropped Where the change lands', !js.includes('Where the change lands'));
ok('the overview dropped its pattern list', !js.includes('<h4>Writing patterns</h4>'));
ok('the strip dropped Used by', !js.includes('<h4>Used by</h4>'));
ok('the moves heading carries no per-kind tally', !js.includes('Rhetorical moves ${counts}'));

// ---- zoom
ok('wheel deltas are normalised per device', js.includes('e.deltaMode === 1'));
ok('a single wheel event is capped', js.includes('Math.max(-50, Math.min(50, dy))'));
ok('a trackpad pinch gets its own rate', js.includes("e.ctrlKey ? 0.02 : 0.005"));

// ---- deep links
['node=', 'pattern=', 'move=', 'evidence='].forEach(k =>
  ok('deep link ' + k + ' is handled', js.includes("h.startsWith('" + k + "')")));

// ---- the first pattern is a pattern like any other
ok('pattern index 0 isolates the graph', js.includes('state.pattern != null'));
ok('nothing checks state.pattern for truthiness', !/state\.pattern\s*\n?\s*\?/.test(js));

// ---- the Sections pane is guarded everywhere, not in three of four places
ok('the guard is one function', js.includes('function sectionBtn('));
ok('pressing 2 on a doc-only model is a no-op rather than a blank graph',
   js.includes("e.key === '2' && !sectionBtn().disabled"));
ok('no copy of the guard survives',
   !js.includes("document.querySelector('#viewseg [data-view=section]').disabled"));

// ---- Reset resets
ok('Reset restores the status and kind sets', js.includes('state.statuses = new Set(ALL_STATUSES)')
   && js.includes('state.kinds = new Set(ALL_KINDS)'));
ok('and puts the chips back with them',
   js.includes("document.querySelectorAll('.chip[data-status], .chip[data-kind]')"));

// ---- a malformed deep link costs the deep link, not the page
ok('the hash is decoded defensively', /try \{ h = decodeURIComponent/.test(js));
ok('an invalid escape reads as no deep link', /catch \(err\) \{ h = ''; \}/.test(js));

// ---- pattern links carry a scheme the page will follow.
// Markup only: the script block holds the template literal that writes a move's
// catalog link, and matching that source proves nothing about a rendered href.
const pageMarkup = html.split('<script>')[0];
const patrefs = [...pageMarkup.matchAll(/class="patref" href="([^"]*)"/g)].map(m => m[1]);
ok('the page renders pattern links at all', patrefs.length > 0, String(patrefs.length));
ok('every one of them is http(s)', patrefs.every(u => /^https?:\/\//.test(u)),
   patrefs.filter(u => !/^https?:\/\//.test(u)).join(', '));

// ---- fit() cannot flip or invert the graph
ok('the fitted scale has the same floor as the wheel handler',
   js.includes('Math.max(0.08, Math.min((r.width-40)/w'));

// ---- the page's model is parseable JSON
const modelBlock = html.split('type="application/json" id="model">')[1].split('</script>')[0];
ok('the model block parses',
   (() => { try { JSON.parse(modelBlock); return true; } catch (e) { return false; } })());
ok('no bare NaN or Infinity reached it',
   !/(^|[^"\w])(NaN|Infinity)([^"\w]|$)/.test(modelBlock));

// ---- self-contained
ok('the page loads nothing over the network', !/src="http|href="http(?!s?:\/\/[^"]*"\s+target)/.test(
  html.replace(/class="patref" href="[^"]*"/g, '')));

console.log(fail ? '\n' + fail + ' FAILED' : '\nall green');
process.exit(fail ? 1 : 0);
