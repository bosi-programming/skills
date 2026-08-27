#!/usr/bin/env python3
"""Render a change-model JSON into one self-contained dark-theme HTML page.

Stdlib only. No network, no CDN: the output file works offline and can be
mailed, attached to a PR, or opened straight from disk.
"""

import argparse
import html
import json
import os
import re
import sys
from collections import defaultdict, deque

STATUS = {
    "added": {"stroke": "#3fb950", "fill": "#10251a", "text": "#7ee787"},
    "modified": {"stroke": "#d29922", "fill": "#26200f", "text": "#e3b341"},
    "deleted": {"stroke": "#f85149", "fill": "#2a1315", "text": "#ff7b72"},
    "related": {"stroke": "#4d5a6b", "fill": "#161b22", "text": "#8b98a9"},
}

EDGE = {
    "imports": ("#7d8798", ""),
    "calls": ("#58a6ff", ""),
    "extends": ("#bc8cff", ""),
    "implements": ("#bc8cff", "6 4"),
    "injects": ("#39c5cf", ""),
    "emits": ("#f0883e", ""),
    "listens": ("#f0883e", "6 4"),
    "renders": ("#db61a2", ""),
    "queries": ("#56d364", ""),
    "reads": ("#56d364", "6 4"),
    "other": ("#7d8798", "2 4"),
}

NODE_H = 70
V_GAP = 26
H_GAP = 104
MIN_W = 190
MAX_W = 390
CH_SANS = 8.3
CH_MONO = 8.45
PAD = 48


def die(msg):
    print("render_graph: " + msg, file=sys.stderr)
    sys.exit(1)


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


def trunc(s, n):
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def status_of(node):
    st = (node.get("status") or "related").lower()
    return st if st in STATUS else "related"


def edge_style(kind):
    return EDGE.get((kind or "other").lower(), EDGE["other"])


# --------------------------------------------------------------------------
# model


def validate(model):
    errors = []
    if not isinstance(model.get("nodes"), list) or not model["nodes"]:
        errors.append("model.nodes must be a non-empty list")
        return errors
    ids = set()
    for i, n in enumerate(model["nodes"]):
        nid = n.get("id")
        if not nid:
            errors.append("nodes[%d] has no id" % i)
            continue
        if nid in ids:
            errors.append("duplicate node id: %s" % nid)
        ids.add(nid)
        if not n.get("label"):
            n["label"] = str(nid).split("/")[-1]
        lay = n.get("layer") or ("file" if n.get("kind") == "file" else "code")
        n["layer"] = "file" if lay == "file" else "code"
    for i, e in enumerate(model.get("edges") or []):
        for side in ("from", "to"):
            if e.get(side) not in ids:
                errors.append(
                    "edges[%d].%s points at unknown node %r" % (i, side, e.get(side))
                )
    for i, p in enumerate(model.get("patterns") or []):
        if not p.get("name"):
            errors.append("patterns[%d] has no name" % i)
        if not p.get("evidence"):
            errors.append(
                "patterns[%d] (%s) has no evidence; a pattern without file:line "
                "evidence must not be claimed" % (i, p.get("name"))
            )
        for part in p.get("participants") or []:
            if part.get("node") and part["node"] not in ids:
                errors.append(
                    "patterns[%d] participant points at unknown node %r"
                    % (i, part["node"])
                )
    return errors


# --------------------------------------------------------------------------
# layout


def break_cycles(ids, edges):
    adj = defaultdict(list)
    for i, e in enumerate(edges):
        if e["from"] != e["to"]:
            adj[e["from"]].append((e["to"], i))
    color = {n: 0 for n in ids}
    back = set()
    for start in ids:
        if color[start]:
            continue
        color[start] = 1
        stack = [(start, iter(adj[start]))]
        while stack:
            node, it = stack[-1]
            pushed = False
            for nxt, idx in it:
                c = color.get(nxt, 0)
                if c == 1:
                    back.add(idx)
                elif c == 0:
                    color[nxt] = 1
                    stack.append((nxt, iter(adj[nxt])))
                    pushed = True
                    break
            if not pushed:
                color[node] = 2
                stack.pop()
    return back


def layer_nodes(ids, edges, back):
    idset = set(ids)
    out = defaultdict(list)
    indeg = {n: 0 for n in ids}
    for i, e in enumerate(edges):
        if i in back or e["from"] == e["to"]:
            continue
        if e["from"] in idset and e["to"] in idset:
            out[e["from"]].append(e["to"])
            indeg[e["to"]] += 1
    layer = {n: 0 for n in ids}
    q = deque([n for n in ids if indeg[n] == 0])
    while q:
        u = q.popleft()
        for v in out[u]:
            layer[v] = max(layer[v], layer[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return layer


def order_layers(ids, edges, layer):
    buckets = defaultdict(list)
    for n in ids:
        buckets[layer[n]].append(n)
    pos = {}
    for lv in buckets:
        for i, n in enumerate(buckets[lv]):
            pos[n] = i
    preds = defaultdict(list)
    succs = defaultdict(list)
    for e in edges:
        if e["from"] == e["to"] or e["from"] not in pos or e["to"] not in pos:
            continue
        succs[e["from"]].append(e["to"])
        preds[e["to"]].append(e["from"])
    keys = sorted(buckets)
    for sweep in range(6):
        ref = preds if sweep % 2 == 0 else succs
        for lv in (keys if sweep % 2 == 0 else list(reversed(keys))):
            def bary(n, ref=ref):
                vals = [pos[m] for m in ref.get(n, ()) if m in pos]
                return sum(vals) / len(vals) if vals else pos[n]
            buckets[lv].sort(key=bary)
            for i, n in enumerate(buckets[lv]):
                pos[n] = i
    return buckets


def sublabel_of(node):
    """Second line of a box: the kind, then where it lives.

    Keeping both on one line avoids a separate corner label that collides with
    long paths, and it is the pair a reader needs to place the box: what it is
    and where to find it.
    """
    kind = node.get("kind") or ""
    sub = node.get("sublabel") or ""
    if kind and node.get("layer") == "code":
        return ("%s · %s" % (kind, sub)) if sub else kind
    return sub


def node_text(node):
    """The three strings a box shows: title, second line, diff badge.

    Width and drawing must agree on these, so both go through here.
    """
    label = trunc(node["label"], 32)
    sub = trunc(sublabel_of(node), 30)
    ins, dele = node.get("insertions"), node.get("deletions")
    badge = ""
    if ins is not None or dele is not None:
        badge = "+%s \u2212%s" % (ins or 0, dele or 0)
    return label, sub, badge


def node_width(node):
    label, sub, badge = node_text(node)
    badge_w = (len(badge) * CH_MONO + 16) if badge else 0
    line1 = len(label) * CH_SANS + (badge_w if not sub else 0)
    line2 = (len(sub) * CH_MONO + badge_w) if sub else 0
    return int(max(MIN_W, min(MAX_W, max(line1, line2) + 32)))


def layout(nodes, edges):
    ids = [n["id"] for n in nodes]
    if not ids:
        return {}, 200, 200
    back = break_cycles(ids, edges)
    layer = layer_nodes(ids, edges, back)
    buckets = order_layers(ids, edges, layer)
    by_id = {n["id"]: n for n in nodes}

    widths = {}
    for lv, members in buckets.items():
        widths[lv] = max(node_width(by_id[n]) for n in members)
    x_of = {}
    x = PAD
    for lv in sorted(buckets):
        x_of[lv] = x
        x += widths[lv] + H_GAP

    tallest = max(len(m) for m in buckets.values())
    box = {}
    for lv, members in buckets.items():
        col_h = len(members) * NODE_H + (len(members) - 1) * V_GAP
        full_h = tallest * NODE_H + (tallest - 1) * V_GAP
        top = PAD + (full_h - col_h) / 2.0
        for i, nid in enumerate(members):
            box[nid] = {
                "x": x_of[lv],
                "y": top + i * (NODE_H + V_GAP),
                "w": widths[lv],
                "h": NODE_H,
                "layer": lv,
            }
    width = x - H_GAP + PAD
    height = PAD * 2 + tallest * NODE_H + (tallest - 1) * V_GAP
    return box, int(width), int(height)


# --------------------------------------------------------------------------
# svg


def edge_path(a, b):
    x1, y1 = a["x"] + a["w"], a["y"] + a["h"] / 2.0
    x2, y2 = b["x"], b["y"] + b["h"] / 2.0
    forward = b["layer"] > a["layer"]
    if a is b:
        return "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
            x1, y1 - 8, x1 + 46, y1 - 40, x1 + 46, y1 + 40, x1, y1 + 8), forward
    if forward:
        dx = max(36.0, (x2 - x1) * 0.45)
        return "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
            x1, y1, x1 + dx, y1, x2 - dx, y2, x2, y2), True
    x1, y1 = a["x"], a["y"] + a["h"] / 2.0
    x2, y2 = b["x"] + b["w"], b["y"] + b["h"] / 2.0
    bow = 40 + abs(y2 - y1) * 0.25
    return "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
        x1, y1, x1 - bow, y1, x2 + bow, y2, x2, y2), False


def render_svg(view, nodes, edges):
    box, w, h = layout(nodes, edges)
    parts = []
    markers = []
    seen_marker = set()
    for kind, (color, _dash) in EDGE.items():
        mid = "arw-" + slug(color)
        if mid in seen_marker:
            continue
        seen_marker.add(mid)
        markers.append(
            '<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>' % (mid, color)
        )
    parts.append(
        '<svg id="svg-%s" class="graph" viewBox="0 0 %d %d" width="%d" height="%d" '
        'xmlns="http://www.w3.org/2000/svg">' % (view, w, h, w, h)
    )
    parts.append("<defs>" + "".join(markers) + "</defs>")
    parts.append('<g class="viewport">')

    parts.append('<g class="edges">')
    for e in edges:
        a, b = box.get(e["from"]), box.get(e["to"])
        if not a or not b:
            continue
        color, dash = edge_style(e.get("kind"))
        d, forward = edge_path(a, b)
        st = (e.get("status") or "existing").lower()
        if st == "added":
            width_px, opacity = 2.2, 0.95
        elif st == "removed":
            width_px, opacity = 1.6, 0.5
            dash = dash or "4 4"
        else:
            width_px, opacity = 1.4, 0.65
        title = "%s: %s → %s" % (e.get("kind") or "other", e["from"], e["to"])
        if e.get("label"):
            title += " (%s)" % e["label"]
        if e.get("evidence"):
            title += "  [%s]" % e["evidence"]
        parts.append(
            '<path class="edge" d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
            'stroke-opacity="%.2f" %s marker-end="url(#arw-%s)" data-from="%s" '
            'data-to="%s" data-kind="%s" data-status="%s"><title>%s</title></path>'
            % (
                d, color, width_px, opacity,
                ('stroke-dasharray="%s"' % dash) if dash else "",
                slug(color), esc(e["from"]), esc(e["to"]),
                esc((e.get("kind") or "other").lower()), esc(st), esc(title),
            )
        )
    parts.append("</g>")

    parts.append('<g class="nodes">')
    for n in nodes:
        b = box.get(n["id"])
        if not b:
            continue
        st = status_of(n)
        c = STATUS[st]
        label, sub, badge = node_text(n)
        parts.append(
            '<g class="node" data-node-id="%s" data-status="%s" transform="translate(%.1f,%.1f)">'
            % (esc(n["id"]), st, b["x"], b["y"])
        )
        parts.append(
            '<rect class="node-box" width="%d" height="%d" rx="10" fill="%s" '
            'stroke="%s" stroke-width="1.6"/>' % (b["w"], b["h"], c["fill"], c["stroke"])
        )
        parts.append(
            '<rect class="node-accent" width="4" height="%d" rx="2" fill="%s"/>'
            % (b["h"], c["stroke"])
        )
        parts.append(
            '<text class="node-label" x="16" y="%d" fill="#e6edf3">%s</text>'
            % (28 if sub else 41, esc(label))
        )
        if sub:
            parts.append(
                '<text class="node-sub" x="16" y="52" fill="#8b98a9">%s</text>' % esc(sub)
            )
        if badge:
            plus, minus = badge.split(" ")
            parts.append(
                '<text class="node-diff" x="%d" y="%d" text-anchor="end">'
                '<tspan fill="#3fb950">%s</tspan> <tspan fill="#f85149">%s</tspan></text>'
                % (b["w"] - 12, 52 if sub else 41, plus, minus)
            )
        parts.append("<title>%s</title>" % esc(n["id"]))
        parts.append("</g>")
    parts.append("</g></g></svg>")
    return "".join(parts), w, h


# --------------------------------------------------------------------------
# html

CSS = """
:root{
  --bg:#0b0e14; --panel:#11151d; --panel-2:#161b25; --line:#222a36;
  --fg:#e6edf3; --muted:#8b98a9; --dim:#6e7b8b; --accent:#58a6ff;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--fg);
  font:14px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  display:flex;flex-direction:column;overflow:hidden}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
a,a:visited{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{padding:14px 20px;border-bottom:1px solid var(--line);background:var(--panel);
  display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
header h1{font-size:16px;margin:0;font-weight:600}
header .src{color:var(--muted);font-size:14px}
header .stats{margin-left:auto;display:flex;gap:14px;font-size:14px;color:var(--muted)}
header .stats b{color:var(--fg);font-weight:600}
.toolbar{display:flex;gap:8px;align-items:center;padding:10px 20px;
  border-bottom:1px solid var(--line);background:var(--panel-2);flex-wrap:wrap}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{background:transparent;color:var(--muted);border:0;padding:6px 14px;
  cursor:pointer;font-size:14px}
.seg button[aria-pressed="true"]{background:#1f2937;color:var(--fg)}
.chip{border:1px solid var(--line);background:transparent;color:var(--muted);
  border-radius:999px;padding:4px 11px;font-size:14px;cursor:pointer;display:flex;
  align-items:center;gap:6px}
.chip[aria-pressed="true"]{color:var(--fg);background:#1b2230}
.chip .dot{width:8px;height:8px;border-radius:50%}
.chip.off{opacity:.42;text-decoration:line-through}
input[type=search]{background:#0d1117;border:1px solid var(--line);color:var(--fg);
  border-radius:8px;padding:6px 10px;min-width:190px;font-size:14px}
.spacer{flex:1}
.btn{background:#1b2230;border:1px solid var(--line);color:var(--muted);border-radius:8px;
  padding:6px 12px;font-size:14px;cursor:pointer}
.btn:hover{color:var(--fg)}
main{flex:1;display:flex;min-height:0}
#left{flex:1;display:flex;flex-direction:column;min-width:0}
#stage{flex:1;position:relative;overflow:hidden;cursor:grab;background:
  radial-gradient(circle at 18px 18px,#1a212c 1px,transparent 1px) 0 0/34px 34px,var(--bg)}
#stage.dragging{cursor:grabbing}
#stage .pane{position:absolute;inset:0}
#stage .pane[hidden]{display:none}
svg.graph{position:absolute;top:0;left:0;overflow:visible}
.node{cursor:pointer}
.node-label{font-size:14px;font-weight:600}
.node-sub,.node-kind{font-size:14px;font-family:ui-monospace,Menlo,monospace}
.node-diff{font-size:14px;font-family:ui-monospace,Menlo,monospace}
.node .node-box{transition:filter .12s}
.node:hover .node-box{filter:brightness(1.35)}
.dim{opacity:.14}
.hide{display:none}
.hit .node-box{stroke-width:3}
#explainer{flex:0 0 25vh;height:25vh;min-height:150px;max-height:60vh;overflow-y:auto;
  resize:vertical;border-top:1px solid var(--line);background:var(--panel);padding:14px 20px 18px}
#explainer .head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
#explainer .eyebrow{font-size:14px;letter-spacing:.09em;text-transform:uppercase;color:var(--dim)}
#explainer .name{font-size:15px;font-weight:600}
#explainer .meta{font-size:14px;color:var(--dim);font-family:ui-monospace,Menlo,monospace}
#explainer p{margin:0 0 8px;font-size:15px;color:#cbd5e1;max-width:82ch}
#explainer ul.bullets{margin:0 0 10px;padding-left:18px;font-size:14px;color:var(--muted);
  max-width:82ch}
#explainer ul.bullets li{margin:2px 0}
#explainer .body{display:flex;gap:30px;align-items:flex-start}
#explainer .prose{flex:1 1 48%;min-width:280px}
#explainer .prose p,#explainer .prose ul{max-width:none}
#explainer .cols{display:flex;gap:24px;flex-wrap:wrap;flex:1 1 46%;align-items:flex-start}
#explainer .col{flex:1 1 190px;min-width:180px}
#explainer .col h4{margin:0 0 4px;font-size:14px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--dim);font-weight:600}
#explainer .rel{margin:0;padding:0;list-style:none;font-size:14px;color:var(--muted)}
#explainer .rel li{padding:2px 0}
#explainer .back{margin-left:auto}
aside{width:33.333%;min-width:320px;max-width:620px;flex:0 0 33.333%;
  border-left:1px solid var(--line);background:var(--panel);
  overflow-y:auto;padding:16px 20px 40px}
aside h2{font-size:14px;letter-spacing:.09em;text-transform:uppercase;color:var(--dim);
  margin:22px 0 10px;display:flex;align-items:baseline;gap:10px}
aside h2 .count{color:var(--muted);letter-spacing:0;text-transform:none}
.linkish{background:none;border:0;color:var(--accent);cursor:pointer;font-size:14px;
  padding:0;margin-left:auto;letter-spacing:0;text-transform:none}
.linkish:hover{text-decoration:underline}
aside h2:first-child{margin-top:0}
.card{border:1px solid var(--line);border-radius:10px;padding:11px 13px;margin-bottom:9px;
  background:var(--panel-2);cursor:pointer}
.card:hover{border-color:#3a465a}
.card.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.card .row{display:flex;align-items:center;gap:8px}
.card .name{font-weight:600;font-size:14px}
.card .conf{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
  border:1px solid var(--line);border-radius:999px;padding:1px 9px;color:var(--muted)}
.card .conf.high{color:#7ee787;border-color:#2c5c39}
.card .conf.medium{color:#e3b341;border-color:#5c4a1e}
.card .conf.low{color:#ff9492;border-color:#6b2b2b}
.card p{margin:7px 0 0;color:var(--muted);font-size:14px}
.card ul{margin:8px 0 0;padding-left:16px;color:var(--muted);font-size:14px}
.card .ev{font-size:14px;color:var(--dim)}
.empty{color:var(--dim);font-size:14px}
.legend{display:flex;flex-direction:column;gap:6px;font-size:14px;color:var(--muted)}
.legend .row{display:flex;align-items:center;gap:9px}
.legend .sw{width:22px;height:0;border-top-width:2px;border-top-style:solid}
.legend .bx{width:14px;height:12px;border-radius:3px;border:1.5px solid}
.filelist{font-size:14px}
.filelist div{display:flex;gap:8px;padding:4px 0;border-top:1px solid var(--line);
  cursor:pointer;align-items:center}
.filelist div:hover{color:#fff}
.filelist .p{flex:1;word-break:break-all;color:var(--muted);font-family:ui-monospace,Menlo,monospace}
.filelist .n{font-family:ui-monospace,Menlo,monospace;font-size:14px;white-space:nowrap}
.summary{color:var(--muted);font-size:14px;margin:0 0 4px}
"""

JS = r"""
const MODEL = JSON.parse(document.getElementById('model').textContent);
const stage = document.getElementById('stage');
const state = {view:'file', scale:1, tx:0, ty:0, statuses:new Set(['added','modified','deleted','related']),
               kinds:new Set(MODEL._kinds), selected:null, pattern:null, query:'',
               allPatterns:false};

function svgEl(){ return document.querySelector('#pane-'+state.view+' svg'); }
function vp(){ return svgEl().querySelector('.viewport'); }

function applyTransform(){
  vp().setAttribute('transform', `translate(${state.tx},${state.ty}) scale(${state.scale})`);
  document.getElementById('zoom').textContent = Math.round(state.scale*100)+'%';
}
function fit(){
  const svg = svgEl();
  const w = +svg.getAttribute('width'), h = +svg.getAttribute('height');
  const r = stage.getBoundingClientRect();
  const s = Math.min((r.width-40)/w, (r.height-40)/h, 1.4);
  state.scale = s;
  state.tx = (r.width - w*s)/2;
  state.ty = (r.height - h*s)/2;
  applyTransform();
}
stage.addEventListener('wheel', e => {
  e.preventDefault();
  const r = stage.getBoundingClientRect();
  const mx = e.clientX-r.left, my = e.clientY-r.top;
  const k = Math.exp(-e.deltaY*0.0016);
  const ns = Math.max(0.12, Math.min(4, state.scale*k));
  state.tx = mx - (mx-state.tx)*(ns/state.scale);
  state.ty = my - (my-state.ty)*(ns/state.scale);
  state.scale = ns; applyTransform();
}, {passive:false});
let drag = null;
stage.addEventListener('pointerdown', e => {
  if (e.target.closest('.node')) return;
  drag = {x:e.clientX, y:e.clientY, tx:state.tx, ty:state.ty};
  stage.classList.add('dragging'); stage.setPointerCapture(e.pointerId);
});
stage.addEventListener('pointermove', e => {
  if (!drag) return;
  state.tx = drag.tx + (e.clientX-drag.x); state.ty = drag.ty + (e.clientY-drag.y);
  applyTransform();
});
stage.addEventListener('pointerup', () => { drag=null; stage.classList.remove('dragging'); });

function setView(v){
  state.view = v;
  document.querySelectorAll('#viewseg button').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.view === v)));
  document.querySelectorAll('#stage .pane').forEach(p =>
    p.hidden = (p.id !== 'pane-'+v));
  refresh(); fit();
}

function nodeInfo(id){ return MODEL._byId[id]; }

// Which patterns touch a node. A code node matches by being a participant; a
// file node matches when a participant lives in it, so selecting a file in the
// default view still narrows the pattern list to that file's patterns.
function patternsFor(id){
  const n = nodeInfo(id) || {};
  const base = String(id).split('/').pop();
  return (MODEL.patterns||[]).map((p,i) => ({p,i})).filter(({p}) => {
    const parts = p.participants || [];
    if (parts.some(x => x.node === id)) return true;
    if (n.layer !== 'file') return false;
    if (parts.some(x => {
      const o = nodeInfo(x.node) || {};
      return o.parent === id || o.sublabel === base || String(o.sublabel||'').endsWith('/'+base);
    })) return true;
    return (p.evidence||[]).some(e =>
      String(e.ref||'').split(':')[0].split('/').pop() === base);
  });
}

function syncPatterns(){
  const head = document.getElementById('patterns-head');
  const empty = document.getElementById('patterns-empty');
  const cards = [...document.querySelectorAll('#patterns .card')];
  const total = cards.length;
  if (!state.selected || state.allPatterns){
    cards.forEach(c => c.hidden = false);
    empty.hidden = true;
    head.innerHTML = `Design patterns <span class="count">${total}</span>`
      + (state.selected ? '<button class="linkish" id="narrowbtn">only this one</button>' : '');
  } else {
    const keep = new Set(patternsFor(state.selected).map(x => x.i));
    cards.forEach(c => c.hidden = !keep.has(+c.dataset.idx));
    const n = nodeInfo(state.selected) || {};
    head.innerHTML = `Patterns in ${esc(n.label || state.selected)} `
      + `<span class="count">${keep.size} of ${total}</span>`
      + '<button class="linkish" id="allbtn">show all</button>';
    empty.hidden = keep.size > 0;
    empty.textContent = keep.size
      ? '' : 'No pattern claimed here. Whatever this node does, it is plain wiring.';
  }
  const all = document.getElementById('allbtn');
  if (all) all.onclick = () => { state.allPatterns = true; syncPatterns(); };
  const narrow = document.getElementById('narrowbtn');
  if (narrow) narrow.onclick = () => { state.allPatterns = false; syncPatterns(); };
}

function refresh(){
  const q = state.query.trim().toLowerCase();
  const patternNodes = state.pattern
    ? new Set((MODEL.patterns[state.pattern].participants||[]).map(p=>p.node))
    : null;
  document.querySelectorAll('#stage .pane .node').forEach(g => {
    const id = g.dataset.nodeId, n = nodeInfo(id);
    const okStatus = state.statuses.has(g.dataset.status);
    g.classList.toggle('hide', !okStatus);
    let dim = false;
    if (q) dim = !((id+' '+(n.label||'')+' '+(n.sublabel||'')+' '+(n.summary||'')).toLowerCase().includes(q));
    if (patternNodes && !patternNodes.has(id)) dim = true;
    g.classList.toggle('dim', dim);
    g.classList.toggle('hit', !!(state.selected && id === state.selected));
  });
  const visible = new Set([...document.querySelectorAll('#stage .pane:not([hidden]) .node')]
    .filter(g => !g.classList.contains('hide')).map(g => g.dataset.nodeId));
  document.querySelectorAll('#stage .pane .edge').forEach(p => {
    const on = state.kinds.has(p.dataset.kind) && visible.has(p.dataset.from) && visible.has(p.dataset.to);
    p.classList.toggle('hide', !on);
    let dim = false;
    if (patternNodes) dim = !(patternNodes.has(p.dataset.from) && patternNodes.has(p.dataset.to));
    if (state.selected) dim = dim || !(p.dataset.from===state.selected || p.dataset.to===state.selected);
    p.classList.toggle('dim', dim);
  });
}

function select(id){
  state.selected = (state.selected === id) ? null : id;
  state.allPatterns = false;
  if (state.selected) state.pattern = null;
  document.querySelectorAll('#patterns .card').forEach(c =>
    c.classList.toggle('active', +c.dataset.idx === state.pattern));
  renderExplainer(); syncPatterns(); refresh();
}

function relList(list, dir){
  return list.map(e => {
    const other = dir === 'out' ? e.to : e.from;
    const arrow = dir === 'out' ? '\u2192' : '\u2190';
    const o = nodeInfo(other) || {};
    return `<li>${esc(e.kind||'other')} ${arrow} <a href="#" data-goto="${esc(other)}">${esc(o.label||other)}</a>`
      + `${e.label?` <span class="ev">${esc(e.label)}</span>`:''}`
      + `${e.evidence?` <span class="ev mono">${esc(e.evidence)}</span>`:''}</li>`;
  }).join('');
}

function derivedLine(id, n, outs, ins){
  const bits = [];
  bits.push(`${n.kind || 'node'}, ${n.status || 'related'}`);
  if (n.insertions != null || n.deletions != null)
    bits.push(`+${n.insertions||0} \u2212${n.deletions||0} lines`);
  if (n.line) bits.push(`from line ${n.line}`);
  bits.push(`${outs.length} outgoing, ${ins.length} incoming relation${ins.length===1?'':'s'}`);
  return bits.join(' \u00b7 ') + '. No written explanation in the model for this one.';
}

function renderExplainer(){
  const host = document.getElementById('explainer');
  const back = '<button class="btn back" id="backbtn">Back to overview</button>';

  if (state.selected){
    const id = state.selected, n = nodeInfo(id) || {};
    const outs = (MODEL.edges||[]).filter(e => e.from === id);
    const ins = (MODEL.edges||[]).filter(e => e.to === id);
    const pats = patternsFor(id).map(x => [x.p, x.i]);
    const meta = [id, n.status, n.line ? 'line '+n.line : null,
      (n.insertions != null || n.deletions != null) ? `+${n.insertions||0} \u2212${n.deletions||0}` : null]
      .filter(Boolean).join('  \u00b7  ');
    host.innerHTML = `
      <div class="head">
        <span class="eyebrow">${esc(n.kind || 'node')}</span>
        <span class="name">${esc(n.label || id)}</span>
        ${back}
      </div>
      <div class="meta" style="margin-bottom:8px">${esc(meta)}</div>
      <div class="body"><div class="prose">
      <p>${esc(n.summary || derivedLine(id, n, outs, ins))}</p>
      ${(n.details||[]).length ? `<ul class="bullets">${(n.details||[]).map(d=>`<li>${esc(d)}</li>`).join('')}</ul>` : ''}
      </div>
      <div class="cols">
        ${outs.length ? `<div class="col"><h4>Depends on</h4><ul class="rel">${relList(outs,'out')}</ul></div>` : ''}
        ${ins.length ? `<div class="col"><h4>Used by</h4><ul class="rel">${relList(ins,'in')}</ul></div>` : ''}
        ${pats.length ? `<div class="col"><h4>Patterns here</h4><ul class="rel">${
          pats.map(([p,i]) => `<li><a href="#" data-pat="${i}">${esc(p.name)}</a> <span class="ev">${esc(p.confidence||'')}</span></li>`).join('')
        }</ul></div>` : ''}
      </div></div>`;
  } else if (state.pattern != null){
    const p = MODEL.patterns[state.pattern];
    host.innerHTML = `
      <div class="head">
        <span class="eyebrow">design pattern</span>
        <span class="name">${esc(p.name)}</span>
        <span class="meta">${esc(p.confidence||'')} confidence</span>
        ${back}
      </div>
      <div class="body"><div class="prose">
      ${p.intent ? `<p>${esc(p.intent)}</p>` : ''}
      ${p.note ? `<p class="meta" style="font-family:inherit;font-size:14px">${esc(p.note)}</p>` : ''}
      </div>
      <div class="cols">
        ${(p.participants||[]).length ? `<div class="col"><h4>Participants</h4><ul class="rel">${
          (p.participants||[]).map(x => `<li><b>${esc(x.role||'participant')}</b>: <a href="#" data-goto="${esc(x.node)}">${esc((nodeInfo(x.node)||{}).label || x.node)}</a></li>`).join('')
        }</ul></div>` : ''}
        ${(p.evidence||[]).length ? `<div class="col"><h4>Evidence</h4><ul class="rel">${
          (p.evidence||[]).map(x => `<li><span class="mono">${esc(x.ref)}</span>${x.note?' \u2014 '+esc(x.note):''}</li>`).join('')
        }</ul></div>` : ''}
      </div></div>`;
  } else {
    const top = (MODEL.nodes||[]).filter(n => n.layer === 'file' && n.status !== 'related')
      .sort((a,b) => ((b.insertions||0)+(b.deletions||0)) - ((a.insertions||0)+(a.deletions||0)))
      .slice(0,4);
    host.innerHTML = `
      <div class="head">
        <span class="eyebrow">what this change is about</span>
        <span class="name">${esc(MODEL.title||'Code change map')}</span>
        <span class="meta">${esc(MODEL.source||'')}</span>
      </div>
      <div class="body"><div class="prose">
      ${MODEL.summary ? `<p>${esc(MODEL.summary)}</p>`
        : '<p class="meta" style="font-family:inherit">No summary in the model.</p>'}
      <p class="meta" style="font-family:inherit">Click any box, file or pattern to swap this panel for its explanation.</p>
      </div>
      <div class="cols">
        ${top.length ? `<div class="col"><h4>Where the change lands</h4><ul class="rel">${
          top.map(n => `<li><a href="#" data-goto="${esc(n.id)}">${esc(n.label||n.id)}</a> <span class="ev mono">+${n.insertions||0} \u2212${n.deletions||0}</span></li>`).join('')
        }</ul></div>` : ''}
        ${(MODEL.patterns||[]).length ? `<div class="col"><h4>Patterns found</h4><ul class="rel">${
          (MODEL.patterns||[]).map((p,i) => `<li><a href="#" data-pat="${i}">${esc(p.name)}</a> <span class="ev">${esc(p.confidence||'')}</span></li>`).join('')
        }</ul></div>` : '<div class="col"><h4>Patterns found</h4><p class="meta" style="font-family:inherit">None claimed: plain procedural change.</p></div>'}
      </div></div>`;
  }

  host.querySelectorAll('[data-pat]').forEach(a => a.onclick = ev => {
    ev.preventDefault(); state.selected = null; pickPattern(+a.dataset.pat);
  });
  host.querySelectorAll('[data-goto]').forEach(a => a.onclick = ev => {
    ev.preventDefault(); state.selected = a.dataset.goto; state.pattern = null;
    document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
    renderExplainer(); syncPatterns(); refresh();
  });
  const b = document.getElementById('backbtn');
  if (b) b.onclick = () => {
    state.selected = null; state.pattern = null; state.allPatterns = false;
    document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
    renderExplainer(); syncPatterns(); refresh();
  };
}

function pickPattern(i){
  state.pattern = (state.pattern === i) ? null : i;
  document.querySelectorAll('#patterns .card').forEach(c =>
    c.classList.toggle('active', +c.dataset.idx === state.pattern));
  renderExplainer(); syncPatterns(); refresh();
}

function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

document.querySelectorAll('#viewseg button').forEach(b => b.onclick = () => setView(b.dataset.view));
document.querySelectorAll('.chip[data-status]').forEach(c => c.onclick = () => {
  const s = c.dataset.status;
  state.statuses.has(s) ? state.statuses.delete(s) : state.statuses.add(s);
  c.setAttribute('aria-pressed', String(state.statuses.has(s)));
  c.classList.toggle('off', !state.statuses.has(s));
  refresh();
});
document.querySelectorAll('.chip[data-kind]').forEach(c => c.onclick = () => {
  const k = c.dataset.kind;
  state.kinds.has(k) ? state.kinds.delete(k) : state.kinds.add(k);
  c.setAttribute('aria-pressed', String(state.kinds.has(k)));
  c.classList.toggle('off', !state.kinds.has(k));
  refresh();
});
document.getElementById('search').oninput = e => { state.query = e.target.value; refresh(); };
document.getElementById('fitbtn').onclick = fit;
document.getElementById('resetbtn').onclick = () => {
  state.selected = null; state.pattern = null; state.query = ''; state.allPatterns = false;
  document.getElementById('search').value = '';
  document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
  renderExplainer(); syncPatterns(); refresh();
};
document.querySelectorAll('#patterns .card').forEach(c => c.onclick = () => pickPattern(+c.dataset.idx));
document.querySelectorAll('#stage .node').forEach(g => g.onclick = () => select(g.dataset.nodeId));
document.querySelectorAll('.filelist div').forEach(d => d.onclick = () => {
  if (state.view !== 'file') setView('file');
  select(d.dataset.nodeId);
});
window.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === '1') setView('file');
  if (e.key === '2') setView('code');
  if (e.key === 'f') fit();
  if (e.key === 'Escape') document.getElementById('resetbtn').click();
});
window.addEventListener('resize', fit);
// Deep links: #code, #node=<id>, #pattern=<index>. Handy for pasting a link to
// one box into a review comment.
(function fromHash(){
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (!h) return;
  if (h === 'code' && !document.querySelector('#viewseg [data-view=code]').disabled) { setView('code'); return; }
  if (h.startsWith('node=')){
    const id = h.slice(5);
    const n = nodeInfo(id);
    if (!n) return;
    if (n.layer === 'code' && !document.querySelector('#viewseg [data-view=code]').disabled) setView('code');
    state.selected = id;
    return;
  }
  if (h.startsWith('pattern=')){
    const i = +h.slice(8);
    if (MODEL.patterns[i]) { state.pattern = i;
      document.querySelectorAll('#patterns .card').forEach(c => c.classList.toggle('active', +c.dataset.idx === i)); }
  }
})();
renderExplainer(); syncPatterns(); refresh(); fit();
"""


def chips_html(nodes, kinds):
    out = []
    counts = defaultdict(int)
    for n in nodes:
        counts[status_of(n)] += 1
    for st in ("added", "modified", "deleted", "related"):
        if not counts[st]:
            continue
        out.append(
            '<button class="chip" data-status="%s" aria-pressed="true">'
            '<span class="dot" style="background:%s"></span>%s <span style="color:#6e7b8b">%d</span>'
            "</button>" % (st, STATUS[st]["stroke"], st, counts[st])
        )
    for k in kinds:
        color = edge_style(k)[0]
        out.append(
            '<button class="chip" data-kind="%s" aria-pressed="true">'
            '<span class="dot" style="background:%s"></span>%s</button>'
            % (esc(k), color, esc(k))
        )
    return "".join(out)


def patterns_html(patterns):
    if not patterns:
        return (
            '<p class="empty">No design pattern is claimed for this change. That is a '
            "finding, not a gap: the diff is plain procedural code.</p>"
        )
    out = []
    for i, p in enumerate(patterns):
        conf = (p.get("confidence") or "medium").lower()
        parts = "".join(
            "<li><b>%s</b>: <span class=\"mono\">%s</span></li>"
            % (esc(x.get("role") or "participant"), esc(x.get("node")))
            for x in (p.get("participants") or [])
        )
        ev = "".join(
            '<li class="ev mono">%s%s</li>'
            % (esc(x.get("ref")), (" — " + esc(x.get("note"))) if x.get("note") else "")
            for x in (p.get("evidence") or [])
        )
        out.append(
            '<div class="card" data-idx="%d"><div class="row"><span class="name">%s</span>'
            '<span class="conf %s">%s</span></div>%s%s%s%s</div>'
            % (
                i, esc(p.get("name")), conf, conf,
                ('<p>%s</p>' % esc(p["intent"])) if p.get("intent") else "",
                ('<ul>%s</ul>' % parts) if parts else "",
                ('<ul>%s</ul>' % ev) if ev else "",
                ('<p class="ev">%s</p>' % esc(p["note"])) if p.get("note") else "",
            )
        )
    return "".join(out)


def files_html(nodes):
    rows = []
    for n in sorted(
        [x for x in nodes if x["layer"] == "file"],
        key=lambda x: (-(x.get("insertions") or 0) - (x.get("deletions") or 0), x["id"]),
    ):
        st = status_of(n)
        rows.append(
            '<div data-node-id="%s"><span class="dot" style="width:8px;height:8px;'
            'border-radius:50%%;background:%s"></span><span class="p">%s</span>'
            '<span class="n"><span style="color:#3fb950">+%s</span> '
            '<span style="color:#f85149">−%s</span></span></div>'
            % (esc(n["id"]), STATUS[st]["stroke"], esc(n["id"]),
               n.get("insertions") or 0, n.get("deletions") or 0)
        )
    return "".join(rows) or '<p class="empty">No files in the model.</p>'


def legend_html(kinds):
    rows = []
    for st in ("added", "modified", "deleted", "related"):
        c = STATUS[st]
        rows.append(
            '<div class="row"><span class="bx" style="border-color:%s;background:%s"></span>%s</div>'
            % (c["stroke"], c["fill"], st)
        )
    for k in kinds:
        color, dash = edge_style(k)
        style = "border-top-color:%s;%s" % (
            color, ("border-top-style:dashed;" if dash else ""))
        rows.append(
            '<div class="row"><span class="sw" style="%s"></span>%s</div>' % (style, esc(k))
        )
    rows.append(
        '<div class="row"><span class="sw" style="border-top-color:#7d8798;'
        'border-top-style:dashed"></span>edge drawn right-to-left = cycle / back reference</div>'
    )
    return "".join(rows)


def render(model):
    nodes = model["nodes"]
    edges = model.get("edges") or []
    file_nodes = [n for n in nodes if n["layer"] == "file"]
    code_nodes = [n for n in nodes if n["layer"] == "code"]
    fids, cids = {n["id"] for n in file_nodes}, {n["id"] for n in code_nodes}
    file_edges = [e for e in edges if e["from"] in fids and e["to"] in fids]
    code_edges = [e for e in edges if e["from"] in cids and e["to"] in cids]

    if not file_nodes:
        file_nodes, file_edges = code_nodes, code_edges
    file_svg, _, _ = render_svg("file", file_nodes, file_edges)
    code_svg, _, _ = render_svg("code", code_nodes, code_edges) if code_nodes else ("", 0, 0)

    kinds = []
    for e in edges:
        k = (e.get("kind") or "other").lower()
        if k not in kinds:
            kinds.append(k)

    stats = model.get("stats") or {}
    stat_bits = []
    for key, label in (
        ("files_changed", "files"),
        ("insertions", "added"),
        ("deletions", "removed"),
    ):
        if stats.get(key) is not None:
            stat_bits.append("<span><b>%s</b> %s</span>" % (esc(stats[key]), label))
    stat_bits.append("<span><b>%d</b> nodes</span>" % len(nodes))
    stat_bits.append("<span><b>%d</b> relations</span>" % len(edges))
    stat_bits.append("<span><b>%d</b> patterns</span>" % len(model.get("patterns") or []))

    payload = {
        "title": model.get("title") or "Code change map",
        "source": model.get("source") or "",
        "summary": model.get("summary") or "",
        "stats": stats,
        "nodes": nodes,
        "edges": edges,
        "patterns": model.get("patterns") or [],
        "_byId": {n["id"]: n for n in nodes},
        "_kinds": kinds,
    }
    code_btn = (
        '<button data-view="code" aria-pressed="false">Code</button>'
        if code_nodes
        else '<button data-view="code" aria-pressed="false" disabled '
             'title="model has no class/function nodes">Code</button>'
    )

    doc = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style></head>
<body>
<header>
  <h1>__TITLE__</h1>
  <span class="src mono">__SOURCE__</span>
  <div class="stats">__STATS__</div>
</header>
<div class="toolbar">
  <div class="seg" id="viewseg">
    <button data-view="file" aria-pressed="true">Files</button>__CODE_BTN__
  </div>
  __CHIPS__
  <div class="spacer"></div>
  <input id="search" type="search" placeholder="filter by name or summary">
  <button class="btn" id="fitbtn">Fit</button>
  <button class="btn" id="resetbtn">Reset</button>
  <span class="src mono" id="zoom">100%</span>
</div>
<main>
  <div id="left">
    <div id="stage">
      <div class="pane" id="pane-file">__FILE_SVG__</div>
      <div class="pane" id="pane-code" hidden>__CODE_SVG__</div>
    </div>
    <section id="explainer"></section>
  </div>
  <aside>
    <h2 id="patterns-head">Design patterns</h2>
    <div id="patterns">__PATTERNS__
      <p class="empty" id="patterns-empty" hidden></p>
    </div>
    <h2>Files changed</h2>
    <div class="filelist">__FILES__</div>
    <h2>Legend</h2>
    <div class="legend">__LEGEND__</div>
  </aside>
</main>
<script type="application/json" id="model">__MODEL__</script>
<script>__JS__</script>
</body></html>"""

    subs = {
        "__TITLE__": esc(model.get("title") or "Code change map"),
        "__SOURCE__": esc(model.get("source") or ""),
        "__STATS__": "".join(stat_bits),
        "__CSS__": CSS,
        "__CHIPS__": chips_html(nodes, kinds),
        "__CODE_BTN__": code_btn,
        "__FILE_SVG__": file_svg,
        "__CODE_SVG__": code_svg,
        "__PATTERNS__": patterns_html(model.get("patterns") or []),
        "__FILES__": files_html(nodes),
        "__LEGEND__": legend_html(kinds),
        "__MODEL__": json.dumps(payload).replace("</", "<\\/"),
        "__JS__": JS,
    }
    for k, v in subs.items():
        doc = doc.replace(k, v)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", help="path to the change-model JSON")
    ap.add_argument("-o", "--out", help="output HTML path (default: <model>.html)")
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args()

    try:
        with open(args.model) as fh:
            model = json.load(fh)
    except (OSError, ValueError) as exc:
        die("cannot read model: %s" % exc)

    errors = validate(model)
    if errors:
        for e in errors:
            print("  - " + e, file=sys.stderr)
        die("%d problem(s) in the model; fix them and re-run" % len(errors))
    if args.check:
        print("model ok: %d nodes, %d edges, %d patterns" % (
            len(model["nodes"]), len(model.get("edges") or []),
            len(model.get("patterns") or [])))
        return

    out = args.out or os.path.splitext(args.model)[0] + ".html"
    with open(out, "w") as fh:
        fh.write(render(model))
    print(os.path.abspath(out))


if __name__ == "__main__":
    main()
