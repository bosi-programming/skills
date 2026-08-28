#!/usr/bin/env python3
"""Render a docs-change model JSON into one self-contained dark-theme HTML page.

Sibling of code-visualizer's render_graph.py, with a prose vocabulary: docs and
sections instead of files and symbols, links instead of imports, writing
patterns instead of design patterns, and rhetorical moves in the strip.

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

INF = float("inf")

STATUS = {
    "added": {"stroke": "#3fb950", "fill": "#10251a", "text": "#7ee787"},
    "modified": {"stroke": "#d29922", "fill": "#26200f", "text": "#e3b341"},
    "deleted": {"stroke": "#f85149", "fill": "#2a1315", "text": "#ff7b72"},
    "related": {"stroke": "#4d5a6b", "fill": "#161b22", "text": "#8b98a9"},
}

EDGE = {
    "links": ("#58a6ff", ""),
    "references": ("#7d8798", ""),
    "includes": ("#39c5cf", ""),
    "see-also": ("#7d8798", "6 4"),
    "defines": ("#bc8cff", ""),
    "supersedes": ("#f0883e", ""),
    "contradicts": ("#f85149", ""),
    "duplicates": ("#db61a2", "6 4"),
    "other": ("#7d8798", "2 4"),
}

# Where each rhetorical move is explained, shown inside the move card.
MOVE_REFERENCE = {
    "claim": "https://en.wikipedia.org/wiki/Toulmin_method",
    "evidence": "https://owl.purdue.edu/owl/general_writing/academic_writing/establishing_arguments/index.html",
    "caveat": "https://en.wikipedia.org/wiki/Toulmin_method",
    "hedge": "https://en.wikipedia.org/wiki/Hedge_(linguistics)",
    "definition": "https://plato.stanford.edu/entries/definitions/",
    "assumption": "https://en.wikipedia.org/wiki/Presupposition",
    "instruction": "https://developers.google.com/style/procedures",
    "contradiction": "https://owl.purdue.edu/owl/general_writing/academic_writing/logic_in_argumentative_writing/index.html",
}

MOVE = {
    "claim": "#58a6ff",
    "evidence": "#3fb950",
    "caveat": "#d29922",
    "hedge": "#bc8cff",
    "definition": "#39c5cf",
    "assumption": "#f0883e",
    "instruction": "#56d364",
    "contradiction": "#f85149",
}

# Where each catalog name is explained. No single site covers writing patterns
# the way refactoring.guru covers the code ones, so each entry points at its own
# best source. A model's patterns[].reference overrides anything here.
REFERENCE = {
    "inverted pyramid": "https://www.nngroup.com/articles/inverted-pyramid/",
    "progressive disclosure": "https://www.nngroup.com/articles/progressive-disclosure/",
    "diátaxis role": "https://diataxis.fr/",
    "diataxis role": "https://diataxis.fr/",
    "adr context-decision-consequence": "https://adr.github.io/",
    "runbook step-and-check": "https://developers.google.com/style/procedures",
    "worked example": "https://diataxis.fr/tutorials/",
    "glossary-first": "https://developers.google.com/style/abbreviations",
    "prerequisites block": "https://diataxis.fr/how-to-guides/",
    "signposted hierarchy": "https://developers.google.com/style/headings",
    "buried lede": "https://www.nngroup.com/articles/inverted-pyramid/",
    "undefined jargon": "https://developers.google.com/style/jargon",
    "wall of text": "https://www.nngroup.com/articles/chunking/",
    "orphan section": "https://www.writethedocs.org/guide/writing/docs-principles/",
    "dead link": "https://developers.google.com/style/link-text",
    "duplicated content": "https://www.writethedocs.org/guide/writing/docs-principles/",
    "missing prerequisite": "https://diataxis.fr/how-to-guides/",
    "passive throat-clearing": "https://developers.google.com/style/voice",
    "heading that is not a claim": "https://developers.google.com/style/headings",
    "stale reference": "https://google.github.io/styleguide/docguide/best_practices.html",
}


SAFE_SCHEMES = ("https://", "http://")


def safe_url(value):
    """A model-supplied URL, or "" when its scheme is not one we will link.

    `esc` is not enough on its own: `javascript:alert(1)` carries no
    HTML-special character, so it survives escaping and runs on click in the
    page the reader opens. The model writes `reference`, and the model reads the
    diff, so treat it as untrusted and allowlist the scheme.
    """
    u = str(value or "").strip()
    return u if u.lower().startswith(SAFE_SCHEMES) else ""


def reference_for(pattern):
    """The URL shown under a pattern name. The model wins over the catalog map.

    A reference the page will not follow falls through to the catalog, so
    dropping an unsafe link does not cost the card its link.
    """
    own = safe_url(pattern.get("reference"))
    if own:
        return own
    key = re.sub(r"[`\u2019']", "", str(pattern.get("name") or "")).strip().lower()
    key = re.sub(r"\s+", " ", key)
    return REFERENCE.get(key, "")


NODE_H = 70
V_GAP = 26
H_GAP = 104
MIN_W = 190
MAX_W = 390
CH_SANS = 8.3
CH_MONO = 8.45
PAD = 48


def die(msg):
    print("render_docs_graph: " + msg, file=sys.stderr)
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


REF_RE = re.compile(r"^[^\s:]+:\d+(?:[-,]\d+)*$")


def bad_ref(ref):
    """True when `ref` is not `path:line`, so it cannot reach any prose.

    Presence was the only check, and `"ref": "somewhere"` passed it. That renders
    as a sourced reading with a dead link: the reader sees a citation and has no
    way to reach what it cites, which is worse than an honest gap.
    """
    return not REF_RE.match(str(ref or "").strip())


def nonfinite_paths(value, path="model"):
    """Every path in the model holding NaN or Infinity.

    `json.dumps` writes those as bare `NaN` and `Infinity`, which are not JSON,
    so the page's `JSON.parse` throws and nothing renders. Catching it here names
    the field instead of leaving a blank page.
    """
    out = []
    if isinstance(value, float) and (value != value or value in (INF, -INF)):
        out.append(path)
    elif isinstance(value, dict):
        for k, v in value.items():
            out += nonfinite_paths(v, "%s.%s" % (path, k))
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            out += nonfinite_paths(v, "%s[%d]" % (path, i))
    return out


def unknown_node(value, ids):
    """The error text for a bad node reference, or "" when it is fine.

    Every list in the model can name a node, and testing `value not in ids`
    straight away raises TypeError on a dict or a list, so the check that exists
    to catch a typo was itself the crash.
    """
    if not value:
        return ""
    if not isinstance(value, str):
        return "must be a node id string, not %s" % type(value).__name__
    if value not in ids:
        return "points at unknown node %r" % value
    return ""


def validate(model):
    """Every error the model can carry, as a list, never as an exception.

    `--check` exists so a bad model fails here rather than as a wrong-looking
    picture, and a traceback is the one outcome that helps nobody: it names a
    Python line instead of the field the author has to fix. So every container is
    type-checked before it is walked.
    """
    errors = []
    if not isinstance(model, dict):
        return ["model must be a JSON object, not %s" % type(model).__name__]
    bad = nonfinite_paths(model)
    if bad:
        return [
            "%s is NaN or Infinity; JSON has no such number and the page would "
            "fail to parse" % b
            for b in bad
        ]
    if not isinstance(model.get("nodes"), list) or not model["nodes"]:
        errors.append("model.nodes must be a non-empty list")
        return errors
    stats = model.get("stats")
    if stats is not None and not isinstance(stats, dict):
        errors.append("model.stats must be an object of counts")
        model["stats"] = {}
    if model.get("edges") is not None and not isinstance(model["edges"], list):
        errors.append("model.edges must be a list of {from, to, kind}")
        model["edges"] = []
    if model.get("patterns") is not None and not isinstance(model["patterns"], list):
        errors.append("model.patterns must be a list of pattern objects")
        model["patterns"] = []
    if model.get("moves") is not None and not isinstance(model["moves"], list):
        errors.append("model.moves must be a list of move objects")
        model["moves"] = []
    ids = set()
    for i, n in enumerate(model["nodes"]):
        if not isinstance(n, dict):
            errors.append("nodes[%d] must be an object, not %s" % (i, type(n).__name__))
            continue
        nid = n.get("id")
        if not nid:
            errors.append("nodes[%d] has no id" % i)
            continue
        if not isinstance(nid, str):
            errors.append(
                "nodes[%d].id must be a string, not %s" % (i, type(nid).__name__)
            )
            continue
        if nid in ids:
            errors.append("duplicate node id: %s" % nid)
        ids.add(nid)
        for key in ("status", "kind", "layer", "label", "sublabel"):
            v = n.get(key)
            if v is not None and not isinstance(v, str):
                errors.append(
                    "nodes[%s].%s must be a string, not %s"
                    % (nid, key, type(v).__name__)
                )
                n.pop(key)
        if not n.get("label"):
            n["label"] = str(nid).split("/")[-1]
        lay = n.get("layer") or ("doc" if n.get("kind") == "doc" else "section")
        n["layer"] = "doc" if lay == "doc" else "section"
    for i, e in enumerate(model.get("edges") or []):
        if not isinstance(e, dict):
            errors.append("edges[%d] must be an object, not %s" % (i, type(e).__name__))
            continue
        for side in ("from", "to"):
            v = e.get(side)
            if not isinstance(v, str):
                errors.append(
                    "edges[%d].%s must be a node id string, not %s"
                    % (i, side, type(v).__name__)
                )
            elif v not in ids:
                errors.append("edges[%d].%s points at unknown node %r" % (i, side, v))
    for i, p in enumerate(model.get("patterns") or []):
        if not isinstance(p, dict):
            errors.append(
                "patterns[%d] must be an object, not %s" % (i, type(p).__name__)
            )
            continue
        if not p.get("name"):
            errors.append("patterns[%d] has no name" % i)
        ev = p.get("evidence")
        if ev is not None and not isinstance(ev, list):
            errors.append(
                "patterns[%d] (%s) evidence must be a list of {ref, quote, explanation}"
                % (i, p.get("name"))
            )
            ev = None
            p["evidence"] = []
        if not ev:
            errors.append(
                "patterns[%d] (%s) has no evidence; a pattern without file:line "
                "evidence must not be claimed" % (i, p.get("name"))
            )
        for j, x in enumerate(ev or []):
            if not isinstance(x, dict):
                errors.append(
                    "patterns[%d] evidence[%d] must be an object, not %s"
                    % (i, j, type(x).__name__)
                )
                continue
            # An evidence entry with no usable ref is the same claim as a pattern
            # with no evidence at all: a name with nothing behind it.
            if bad_ref(x.get("ref")):
                errors.append(
                    "patterns[%d] (%s) evidence[%d] ref is %r; a pattern needs "
                    "path:line evidence, not a name"
                    % (i, p.get("name"), j, x.get("ref"))
                )
            if x.get("note") and not x.get("explanation"):
                x["explanation"] = x.pop("note")
        parts = p.get("participants")
        if parts is not None and not isinstance(parts, list):
            errors.append("patterns[%d] participants must be a list" % i)
            parts = None
        for part in parts or []:
            if not isinstance(part, dict):
                errors.append(
                    "patterns[%d] participant must be an object, not %s"
                    % (i, type(part).__name__)
                )
                continue
            bad = unknown_node(part.get("node"), ids)
            if bad:
                errors.append("patterns[%d] participant %s" % (i, bad))
    for i, m in enumerate(model.get("moves") or []):
        if not isinstance(m, dict):
            errors.append("moves[%d] must be an object, not %s" % (i, type(m).__name__))
            continue
        if not m.get("kind"):
            errors.append("moves[%d] has no kind" % i)
        bad = unknown_node(m.get("node"), ids)
        if not m.get("node"):
            errors.append("moves[%d] points at unknown node %r" % (i, m.get("node")))
        elif bad:
            errors.append("moves[%d] %s" % (i, bad))
        if bad_ref(m.get("ref")):
            errors.append(
                "moves[%d] (%s) ref is %r; a rhetorical move needs path:line, and "
                "a citation the reader cannot reach is an impression with a link "
                "on it" % (i, m.get("kind") or "?", m.get("ref"))
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
    if kind and node.get("layer") == "section":
        return ("%s · %s" % (kind, sub)) if sub else kind
    return sub


def node_text(node):
    """The three strings a box shows: title, second line, word-count badge.

    Width and drawing must agree on these, so both go through here.
    """
    label = trunc(node["label"], 32)
    sub = trunc(sublabel_of(node), 30)
    ins, dele = node.get("words_added"), node.get("words_removed")
    badge = ""
    if ins is not None or dele is not None:
        badge = "+%s \u2212%s w" % (ins or 0, dele or 0)
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
            plus, minus, unit = badge.split(" ")
            parts.append(
                '<text class="node-diff" x="%d" y="%d" text-anchor="end">'
                '<tspan fill="#3fb950">%s</tspan> <tspan fill="#f85149">%s</tspan> '
                '<tspan fill="#6e7b8b">%s</tspan></text>'
                % (b["w"] - 12, 52 if sub else 41, plus, minus, unit)
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
#explainer .moves{font-size:14px;color:var(--muted)}
#explainer .moves .card{margin-bottom:6px}
#explainer .moves .card>summary{padding:7px 10px;gap:7px;flex-wrap:wrap}
#explainer .moves .cardbody{padding:8px 10px 10px}
#explainer .moves .cardbody p{margin:0 0 7px;font-size:14px}
#explainer .moves .cardbody a{color:var(--accent);text-decoration:none}
#explainer .moves .cardbody a:hover{text-decoration:underline}
#explainer .moves .quote{color:#cbd5e1}
.mv{display:inline-block;font-size:14px;letter-spacing:.06em;text-transform:uppercase;
  padding:0 6px;border-radius:5px;border:1px solid;margin-right:6px}

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
.card{border:1px solid var(--line);border-radius:10px;margin-bottom:9px;
  background:var(--panel-2)}
.card:hover{border-color:#3a465a}
.card.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.card>summary{display:flex;align-items:center;gap:8px;padding:11px 13px;cursor:pointer;
  list-style:none;user-select:none}
.card>summary::-webkit-details-marker{display:none}
.card>summary::before{content:"▸";color:var(--dim);font-size:14px;transition:transform .12s}
.card[open]>summary::before{transform:rotate(90deg)}
.card>summary:hover{color:#fff}
.cardbody{padding:0 13px 12px 13px;border-top:1px solid var(--line);margin-top:2px;padding-top:10px}
.patref{display:inline-block;font-size:14px;color:var(--accent);text-decoration:none;margin-bottom:8px}
.patref:hover{text-decoration:underline}
.isolate{display:flex;align-items:center;gap:7px;font-size:14px;color:var(--muted);
  cursor:pointer;margin-bottom:8px}
.isolate input{accent-color:var(--accent);cursor:pointer;width:14px;height:14px;margin:0}
.evlist{list-style:none;padding-left:0;margin:8px 0 0}
.evlist li{padding:2px 0}
.reflink{background:none;border:0;padding:0;color:var(--accent);cursor:pointer;
  font-size:14px;font-family:ui-monospace,Menlo,monospace;text-align:left}
.reflink:hover{text-decoration:underline}
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
#evidence-view{position:fixed;inset:0;z-index:20;background:var(--bg);overflow-y:auto;
  padding:26px 34px 60px}
#evidence-view .evhead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:6px}
#evidence-view h2{margin:0;font-size:15px;font-family:ui-monospace,Menlo,monospace;color:#e6edf3;
  letter-spacing:0;text-transform:none}
#evidence-view .from{font-size:14px;color:var(--dim)}
#evidence-view .from a{color:var(--accent);text-decoration:none}
#evidence-view .from a:hover{text-decoration:underline}
#evidence-view pre{margin:14px 0 0;padding:12px 14px;border:1px solid var(--line);border-radius:10px;
  background:var(--panel-2);overflow-x:auto;font-size:14px;line-height:1.5;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
#evidence-view pre .a{color:#7ee787;display:block}
#evidence-view pre .d{color:#ff7b72;display:block}
#evidence-view pre .h{color:#79c0ff;display:block}
#evidence-view pre .c{color:#8b98a9;display:block}
#evidence-view .why{margin:18px 0 0;max-width:82ch;font-size:15px;color:#cbd5e1}
#evidence-view .why h3{margin:0 0 6px;font-size:14px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--dim);font-weight:600}
.legend{display:flex;flex-direction:column;gap:6px;font-size:14px;color:var(--muted)}
.legend .row{display:flex;align-items:center;gap:9px}
.legend .sw{width:22px;height:0;border-top-width:2px;border-top-style:solid}
.legend .bx{width:14px;height:12px;border-radius:3px;border:1.5px solid}
.doclist{font-size:14px}
.doclist div{display:flex;gap:8px;padding:4px 0;border-top:1px solid var(--line);
  cursor:pointer;align-items:center}
.doclist div:hover{color:#fff}
.doclist .p{flex:1;word-break:break-all;color:var(--muted);font-family:ui-monospace,Menlo,monospace}
.doclist .n{font-family:ui-monospace,Menlo,monospace;font-size:14px;white-space:nowrap}
.summary{color:var(--muted);font-size:14px;margin:0 0 4px}
"""

JS = r"""
const MODEL = JSON.parse(document.getElementById('model').textContent);
const stage = document.getElementById('stage');
const state = {view:'doc', scale:1, tx:0, ty:0, statuses:new Set(['added','modified','deleted','related']),
               kinds:new Set(MODEL._kinds), selected:null, pattern:null, query:'',
               allPatterns:false, move:null, evidence:null};

// The full sets, so Reset can put the chips back rather than leaving a filter on
// under a chip that reads as off.
const ALL_STATUSES = ['added','modified','deleted','related'];
const ALL_KINDS = MODEL._kinds || [];

function sectionBtn(){ return document.querySelector('#viewseg [data-view=section]'); }

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
  // A pane narrower than the 40px margin makes this negative, which flips the
  // SVG and shows a negative zoom. Same floor the wheel handler uses.
  const s = Math.max(0.08, Math.min((r.width-40)/w, (r.height-40)/h, 1.4));
  state.scale = s;
  state.tx = (r.width - w*s)/2;
  state.ty = (r.height - h*s)/2;
  applyTransform();
}
stage.addEventListener('wheel', e => {
  e.preventDefault();
  const r = stage.getBoundingClientRect();
  const mx = e.clientX-r.left, my = e.clientY-r.top;
  // deltaY arrives in three units depending on the device, and a mouse notch is
  // two orders of magnitude bigger than one trackpad tick. Normalise to pixels,
  // then cap a single event so one notch is a step rather than a jump.
  let dy = e.deltaY;
  if (e.deltaMode === 1) dy *= 16;
  else if (e.deltaMode === 2) dy *= stage.clientHeight || 800;
  dy = Math.max(-50, Math.min(50, dy));
  // ctrlKey means a trackpad pinch, whose ticks are small and want a steeper curve.
  const k = Math.exp(-dy * (e.ctrlKey ? 0.02 : 0.005));
  const ns = Math.max(0.08, Math.min(8, state.scale*k));
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

// Which patterns touch a node. A section node matches by being a participant; a
// doc node matches when a participant lives in it, so selecting a doc in the
// default view still narrows the pattern list to that doc's patterns.
function patternsFor(id){
  const n = nodeInfo(id) || {};
  const base = String(id).split('/').pop();
  return (MODEL.patterns||[]).map((p,i) => ({p,i})).filter(({p}) => {
    const parts = p.participants || [];
    if (parts.some(x => x.node === id)) return true;
    if (n.layer !== 'doc') return false;
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
    head.innerHTML = `Writing patterns <span class="count">${total}</span>`
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
  const patternNodes = state.pattern != null
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
  state.move = null;
  if (state.selected) state.pattern = null;
  document.querySelectorAll('#patterns .card').forEach(c =>
    c.classList.toggle('active', +c.dataset.idx === state.pattern));
  renderExplainer(); syncPatterns(); refresh();
}

const MOVE_COLOR = __MOVE_COLORS__;
const MOVE_REFERENCE = __MOVE_REFERENCE__;

// Every move a node carries. A doc node also owns the moves of its sections, so
// clicking a doc shows the argument the whole file makes, not an empty column.
function movesFor(id){
  const kids = new Set((MODEL.nodes||[]).filter(n => n.parent === id).map(n => n.id));
  return (MODEL.moves||[]).map((m,i) => ({m,i}))
    .filter(({m}) => m.node === id || kids.has(m.node));
}

function moveList(items){
  return items.map(({m,i}) => {
    const c = MOVE_COLOR[(m.kind||'').toLowerCase()] || '#7d8798';
    const url = MOVE_REFERENCE[(m.kind||'').toLowerCase()] || '';
    const ev = (MODEL._moveEvidence||{})[i];
    return `<details class="card move" data-move="${i}"${state.move===i?' open':''}>`
      + `<summary><span class="mv" style="color:${c};border-color:${c}">${esc(m.kind||'move')}</span>`
      + `<span class="name">${esc((nodeInfo(m.node)||{}).label || m.node)}</span>`
      + `${m.confidence?`<span class="conf ${esc((m.confidence||'').toLowerCase())}">${esc(m.confidence)}</span>`:''}`
      + `</summary><div class="cardbody">`
      + `${url?`<a class="patref" href="${esc(url)}" target="_blank" rel="noreferrer noopener">What this move is \u2197</a>`:''}`
      + `${m.quote?`<p class="quote">\u201c${esc(m.quote)}\u201d</p>`:''}`
      + `${m.note?`<p class="ev">${esc(m.note)}</p>`:''}`
      + `<p><a href="#" data-goto="${esc(m.node)}">Go to ${esc((nodeInfo(m.node)||{}).label || m.node)}</a></p>`
      + `<ul class="evlist"><li>${ev != null
          ? `<button class="reflink mono" data-ev="${ev}">${esc(m.ref||'')}</button>`
          : `<span class="ev mono">${esc(m.ref||'')}</span>`}</li></ul>`
      + `</div></details>`;
  }).join('');
}

function derivedLine(id, n, outs, ins){
  const bits = [];
  bits.push(`${n.kind || 'node'}, ${n.status || 'related'}`);
  if (n.words_added != null || n.words_removed != null)
    bits.push(`+${n.words_added||0} \u2212${n.words_removed||0} words`);
  if (n.line) bits.push(`from line ${n.line}`);
  bits.push(`${outs.length} outgoing, ${ins.length} incoming relation${ins.length===1?'':'s'}`);
  return bits.join(' \u00b7 ') + '. No written explanation in the model for this one.';
}

// Flat index of every patterns[].evidence[] entry, in the order patterns_html
// numbered them, so a ref rendered in the side panel and the same ref rendered
// in the strip open the same view.
function evIndex(pi, entry){
  return (MODEL._evidence||[]).findIndex(e => e.pattern === pi && e.ref === entry.ref);
}

function diffHtml(text){
  if (!text) return '<p class="meta" style="font-family:inherit">No diff captured in the model for this ref.</p>';
  const cls = l => l.startsWith('@@') ? 'h'
    : (l.startsWith('+') && !l.startsWith('+++')) ? 'a'
    : (l.startsWith('-') && !l.startsWith('---')) ? 'd' : 'c';
  return '<pre>' + String(text).split('\n')
    .map(l => `<span class="${cls(l)}">${esc(l) || '&nbsp;'}</span>`).join('') + '</pre>';
}

function showEvidence(i){
  const e = (MODEL._evidence||[])[i];
  if (!e) return;
  state.evidence = i;
  const host = document.getElementById('evidence-view');
  host.innerHTML = `
    <div class="evhead">
      <h2>${esc(e.ref)}</h2>
      <span class="from">evidence for <a href="#" data-pat="${e.pattern}">${esc(e.patternName)}</a></span>
      <button class="btn back" id="evback">Back to the graph</button>
    </div>
    ${diffHtml(e.diff)}
    <div class="why"><h3>Why this proves it</h3>
    ${e.explanation ? `<p>${esc(e.explanation)}</p>`
      : '<p class="meta" style="font-family:inherit">No explanation in the model for this ref.</p>'}
    </div>`;
  host.hidden = false;
  host.querySelector('#evback').onclick = hideEvidence;
  host.querySelector('[data-pat]').onclick = ev => {
    ev.preventDefault(); hideEvidence(); pickPattern(+ev.target.dataset.pat);
  };
  host.scrollTop = 0;
}

function hideEvidence(){
  state.evidence = null;
  document.getElementById('evidence-view').hidden = true;
}

function renderExplainer(){
  const host = document.getElementById('explainer');
  const back = '<button class="btn back" id="backbtn">Back to overview</button>';

  if (state.selected){
    const id = state.selected, n = nodeInfo(id) || {};
    const outs = (MODEL.edges||[]).filter(e => e.from === id);
    const ins = (MODEL.edges||[]).filter(e => e.to === id);
    const mvs = movesFor(id);
    const meta = [id, n.status, n.line ? 'line '+n.line : null,
      (n.words_added != null || n.words_removed != null) ? `+${n.words_added||0} \u2212${n.words_removed||0} words` : null]
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
        ${mvs.length ? `<div class="col"><h4>Rhetorical moves</h4><div class="moves">${moveList(mvs)}</div></div>` : ''}
      </div></div>`;
  } else if (state.pattern != null){
    const p = MODEL.patterns[state.pattern];
    host.innerHTML = `
      <div class="head">
        <span class="eyebrow">writing pattern</span>
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
          (p.evidence||[]).map(x => `<li><button class="reflink mono" data-ev="${evIndex(state.pattern, x)}">${esc(x.ref)}</button></li>`).join('')
        }</ul></div>` : ''}
      </div></div>`;
  } else {
    const RANK = {low:0, medium:1, high:2};
    const all = (MODEL.moves||[]).map((m,i) => ({m,i}));
    const weak = all.slice().sort((a,b) =>
      (RANK[(a.m.confidence||'medium').toLowerCase()] ?? 1) - (RANK[(b.m.confidence||'medium').toLowerCase()] ?? 1)).slice(0,5);
    host.innerHTML = `
      <div class="head">
        <span class="eyebrow">what this change is about</span>
        <span class="name">${esc(MODEL.title||'Docs change map')}</span>
        <span class="meta">${esc(MODEL.source||'')}</span>
      </div>
      <div class="body"><div class="prose">
      ${MODEL.summary ? `<p>${esc(MODEL.summary)}</p>`
        : '<p class="meta" style="font-family:inherit">No summary in the model.</p>'}
      <p class="meta" style="font-family:inherit">Click any box, doc or move to swap this panel for its explanation. Open a pattern card on the right for its evidence.</p>
      </div>
      <div class="cols">
        ${weak.length ? `<div class="col"><h4>Rhetorical moves</h4><div class="moves">${moveList(weak)}</div></div>`
          : '<div class="col"><h4>Rhetorical moves</h4><p class="meta" style="font-family:inherit">None read out of this change.</p></div>'}
      </div></div>`;
  }

  host.querySelectorAll('[data-pat]').forEach(a => a.onclick = ev => {
    ev.preventDefault(); state.selected = null; pickPattern(+a.dataset.pat);
  });
  host.querySelectorAll('.reflink[data-ev]').forEach(b => b.onclick = ev => {
    ev.preventDefault(); showEvidence(+b.dataset.ev);
  });
  host.querySelectorAll('details.move').forEach(d => d.ontoggle = () => {
    if (d.open) state.move = +d.dataset.move;
    else if (state.move === +d.dataset.move) state.move = null;
  });
  host.querySelectorAll('[data-goto]').forEach(a => a.onclick = ev => {
    ev.preventDefault(); state.selected = a.dataset.goto; state.pattern = null;
    document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
    renderExplainer(); syncPatterns(); refresh();
  });
  const b = document.getElementById('backbtn');
  if (b) b.onclick = () => {
    state.selected = null; state.pattern = null; state.allPatterns = false; state.move = null;
    document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
    renderExplainer(); syncPatterns(); refresh();
  };
}

function syncIsolateBoxes(){
  document.querySelectorAll('#patterns .card input[data-iso]').forEach(b =>
    b.checked = (+b.dataset.iso === state.pattern));
}

function pickPattern(i){
  state.pattern = (state.pattern === i) ? null : i;
  document.querySelectorAll('#patterns .card').forEach(c => {
    const on = +c.dataset.idx === state.pattern;
    c.classList.toggle('active', on);
    if (on) c.open = true;
  });
  syncIsolateBoxes();
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
  hideEvidence();
  state.selected = null; state.pattern = null; state.query = ''; state.allPatterns = false; state.move = null;
  state.statuses = new Set(ALL_STATUSES);
  state.kinds = new Set(ALL_KINDS);
  document.querySelectorAll('.chip[data-status], .chip[data-kind]').forEach(c => {
    c.setAttribute('aria-pressed','true'); c.classList.remove('off');
  });
  document.querySelectorAll('#patterns .card input[data-iso]').forEach(b => b.checked = false);
  document.getElementById('search').value = '';
  document.querySelectorAll('#patterns .card').forEach(c => c.classList.remove('active'));
  renderExplainer(); syncPatterns(); refresh();
};
document.querySelectorAll('#patterns .card input[data-iso]').forEach(b => b.onchange = () => {
  const i = +b.dataset.iso;
  state.pattern = b.checked ? i : null;
  syncIsolateBoxes();
  document.querySelectorAll('#patterns .card').forEach(c =>
    c.classList.toggle('active', +c.dataset.idx === state.pattern));
  renderExplainer(); syncPatterns(); refresh();
});
document.querySelectorAll('.reflink[data-ev]').forEach(b =>
  b.onclick = ev => { ev.preventDefault(); ev.stopPropagation(); showEvidence(+b.dataset.ev); });
document.querySelectorAll('#stage .node').forEach(g => g.onclick = () => select(g.dataset.nodeId));
document.querySelectorAll('.doclist div').forEach(d => d.onclick = () => {
  if (state.view !== 'doc') setView('doc');
  select(d.dataset.nodeId);
});
window.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === '1') setView('doc');
  if (e.key === '2' && !sectionBtn().disabled) setView('section');
  if (e.key === 'f') fit();
  if (e.key === 'Escape'){
    if (state.evidence != null) hideEvidence();
    else document.getElementById('resetbtn').click();
  }
});
window.addEventListener('resize', fit);
// Deep links: #sections, #node=<id>, #pattern=<index>, #move=<index>. Handy for
// pasting a link to one box, one pattern or one sentence into a review comment.
(function fromHash(){
  // A hash like #% throws URIError. Losing the deep link is fine; losing the
  // rest of this function leaves the page unrendered.
  let h;
  try { h = decodeURIComponent(location.hash.replace(/^#/, '')); }
  catch (err) { h = ''; }
  if (!h) return;
  if ((h === 'sections' || h === 'section') && !sectionBtn().disabled) { setView('section'); return; }
  if (h.startsWith('node=')){
    const id = h.slice(5);
    const n = nodeInfo(id);
    if (!n) return;
    if (n.layer === 'section' && !sectionBtn().disabled) setView('section');
    state.selected = id;
    return;
  }
  if (h.startsWith('pattern=')){
    const i = +h.slice(8);
    if (MODEL.patterns[i]) { state.pattern = i;
      document.querySelectorAll('#patterns .card').forEach(c => {
        const on = +c.dataset.idx === i;
        c.classList.toggle('active', on);
        if (on) c.open = true;
      });
      syncIsolateBoxes(); }
    return;
  }
  if (h.startsWith('evidence=')){ showEvidence(+h.slice(9)); return; }
  if (h.startsWith('move=')){
    const i = +h.slice(5);
    const m = (MODEL.moves||[])[i];
    if (!m) return;
    const n = nodeInfo(m.node);
    if (n && n.layer === 'section' && !sectionBtn().disabled) setView('section');
    state.move = i;
    state.selected = m.node;
    return;
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
            '<p class="empty">No writing pattern is claimed for this change. That is a '
            "finding, not a gap: the prose is plain and does nothing clever.</p>"
        )
    out = []
    ei = 0
    for i, p in enumerate(patterns):
        conf = (p.get("confidence") or "medium").lower()
        parts = "".join(
            "<li><b>%s</b>: <span class=\"mono\">%s</span></li>"
            % (esc(x.get("role") or "participant"), esc(x.get("node")))
            for x in (p.get("participants") or [])
        )
        ev_items = []
        for x in (p.get("evidence") or []):
            ev_items.append(
                '<li><button class="reflink mono" data-ev="%d">%s</button></li>'
                % (ei, esc(x.get("ref")))
            )
            ei += 1
        ev = "".join(ev_items)
        url = reference_for(p)
        link = (
            '<a class="patref" href="%s" target="_blank" rel="noreferrer noopener">'
            'What this pattern is ↗</a>' % esc(url)
        ) if url else ""
        out.append(
            '<details class="card" data-idx="%d">'
            '<summary><span class="name">%s</span>'
            '<span class="conf %s">%s</span></summary>'
            '<div class="cardbody">%s'
            '<label class="isolate"><input type="checkbox" data-iso="%d"> Isolate on graph</label>'
            '%s%s%s%s</div></details>'
            % (
                i, esc(p.get("name")), conf, conf, link, i,
                ('<p>%s</p>' % esc(p["intent"])) if p.get("intent") else "",
                ('<ul>%s</ul>' % parts) if parts else "",
                ('<ul class="evlist">%s</ul>' % ev) if ev else "",
                ('<p class="ev">%s</p>' % esc(p["note"])) if p.get("note") else "",
            )
        )
    return "".join(out)


def evidence_index(patterns, moves):
    """Every evidence entry, flattened and numbered the way patterns_html does.

    The index is the id in `#evidence=<i>`, so it has to stay stable between the
    card markup and the page's JavaScript. Pattern evidence comes first and keeps
    its old numbering; the moves are appended, so a link written against an
    earlier render still lands on the same pattern evidence.

    Returns the list plus a map from move index to its slot in that list, which
    is what lets a move card link its ref into the same view.
    """
    out = []
    for i, p in enumerate(patterns):
        for x in (p.get("evidence") or []):
            out.append({
                "ref": x.get("ref") or "",
                "diff": x.get("diff") or "",
                "explanation": x.get("explanation") or "",
                "pattern": i,
                "patternName": p.get("name") or "",
            })
    move_slots = {}
    for i, m in enumerate(moves or []):
        move_slots[i] = len(out)
        out.append({
            "ref": m.get("ref") or "",
            "diff": m.get("diff") or "",
            "explanation": m.get("note") or "",
            "pattern": None,
            "patternName": "%s move" % (m.get("kind") or "rhetorical"),
            "quote": m.get("quote") or "",
        })
    return out, move_slots


def docs_html(nodes):
    rows = []
    for n in sorted(
        [x for x in nodes if x["layer"] == "doc"],
        key=lambda x: (-(x.get("words_added") or 0) - (x.get("words_removed") or 0), x["id"]),
    ):
        st = status_of(n)
        rows.append(
            '<div data-node-id="%s"><span class="dot" style="width:8px;height:8px;'
            'border-radius:50%%;background:%s"></span><span class="p">%s</span>'
            '<span class="n"><span style="color:#3fb950">+%s</span> '
            '<span style="color:#f85149">−%s</span></span></div>'
            % (esc(n["id"]), STATUS[st]["stroke"], esc(n["id"]),
               n.get("words_added") or 0, n.get("words_removed") or 0)
        )
    return "".join(rows) or '<p class="empty">No docs in the model.</p>'


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
    doc_nodes = [n for n in nodes if n["layer"] == "doc"]
    section_nodes = [n for n in nodes if n["layer"] == "section"]
    fids, cids = {n["id"] for n in doc_nodes}, {n["id"] for n in section_nodes}
    doc_edges = [e for e in edges if e["from"] in fids and e["to"] in fids]
    section_edges = [e for e in edges if e["from"] in cids and e["to"] in cids]

    if not doc_nodes:
        doc_nodes, doc_edges = section_nodes, section_edges
    doc_svg, _, _ = render_svg("doc", doc_nodes, doc_edges)
    section_svg, _, _ = render_svg("section", section_nodes, section_edges) if section_nodes else ("", 0, 0)

    kinds = []
    for e in edges:
        k = (e.get("kind") or "other").lower()
        if k not in kinds:
            kinds.append(k)

    ev_all, move_slots = evidence_index(
        model.get("patterns") or [], model.get("moves") or [])

    stats = model.get("stats") or {}
    stat_bits = []
    for key, label in (
        ("files_changed", "docs"),
        ("words_added", "words added"),
        ("words_removed", "words removed"),
    ):
        if stats.get(key) is not None:
            stat_bits.append("<span><b>%s</b> %s</span>" % (esc(stats[key]), label))
    stat_bits.append("<span><b>%d</b> nodes</span>" % len(nodes))
    stat_bits.append("<span><b>%d</b> relations</span>" % len(edges))
    stat_bits.append("<span><b>%d</b> patterns</span>" % len(model.get("patterns") or []))
    stat_bits.append("<span><b>%d</b> moves</span>" % len(model.get("moves") or []))

    payload = {
        "title": model.get("title") or "Docs change map",
        "source": model.get("source") or "",
        "summary": model.get("summary") or "",
        "stats": stats,
        "nodes": nodes,
        "edges": edges,
        "patterns": model.get("patterns") or [],
        "moves": model.get("moves") or [],
        "_evidence": ev_all,
        "_moveEvidence": move_slots,
        "_byId": {n["id"]: n for n in nodes},
        "_kinds": kinds,
    }
    section_btn = (
        '<button data-view="section" aria-pressed="false">Sections</button>'
        if section_nodes
        else '<button data-view="section" aria-pressed="false" disabled '
             'title="model has no section nodes">Sections</button>'
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
    <button data-view="doc" aria-pressed="true">Docs</button>__SECTION_BTN__
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
      <div class="pane" id="pane-doc">__DOC_SVG__</div>
      <div class="pane" id="pane-section" hidden>__SECTION_SVG__</div>
    </div>
    <section id="explainer"></section>
<div id="evidence-view" hidden></div>
  </div>
  <aside>
    <h2 id="patterns-head">Writing patterns</h2>
    <div id="patterns">__PATTERNS__
      <p class="empty" id="patterns-empty" hidden></p>
    </div>
    <h2>Docs changed</h2>
    <div class="doclist">__DOCS__</div>
    <h2>Legend</h2>
    <div class="legend">__LEGEND__</div>
  </aside>
</main>
<script type="application/json" id="model">__MODEL__</script>
<script>__JS__</script>
</body></html>"""

    subs = {
        "__TITLE__": esc(model.get("title") or "Docs change map"),
        "__SOURCE__": esc(model.get("source") or ""),
        "__STATS__": "".join(stat_bits),
        "__CSS__": CSS,
        "__CHIPS__": chips_html(nodes, kinds),
        "__SECTION_BTN__": section_btn,
        "__DOC_SVG__": doc_svg,
        "__SECTION_SVG__": section_svg,
        "__PATTERNS__": patterns_html(model.get("patterns") or []),
        "__DOCS__": docs_html(nodes),
        "__LEGEND__": legend_html(kinds),
        "__MODEL__": json.dumps(payload, allow_nan=False).replace("</", "<\\/"),
        "__JS__": (JS.replace("__MOVE_COLORS__", json.dumps(MOVE))
                     .replace("__MOVE_REFERENCE__", json.dumps(MOVE_REFERENCE))),
    }
    for k, v in subs.items():
        doc = doc.replace(k, v)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", help="path to the docs-change model JSON")
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
        print("model ok: %d nodes, %d edges, %d patterns, %d moves" % (
            len(model["nodes"]), len(model.get("edges") or []),
            len(model.get("patterns") or []), len(model.get("moves") or [])))
        return

    out = args.out or os.path.splitext(args.model)[0] + ".html"
    with open(out, "w") as fh:
        fh.write(render(model))
    print(os.path.abspath(out))


if __name__ == "__main__":
    main()
