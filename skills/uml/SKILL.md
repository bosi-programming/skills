---
name: uml
description: >-
  Draw UML diagrams of a codebase or of a described system with PlantUML, and
  serve them on a local dark-theme page where each diagram can be edited live
  and the edit is saved back to its source. Covers class, sequence, state,
  profile, composite structure, component, deployment, object and package
  diagrams. Use when the user asks for UML, a class diagram, a sequence
  diagram, a state machine, a deployment or package view of a repo or a
  folder, or wants a system they describe drawn as UML, or says "/uml".
---

# UML

The LLM decides what to draw; a script turns it into a page. You write one
PlantUML source per diagram and a manifest, `uml.json`. The script renders
them, themes them and serves the page. The LLM never writes HTML: the page comes
only from the script.

## Settings

Read these keys as `../setup/references/config.md` describes:

- `uml.outputDir`, default `docs/uml`. Folder, relative to the project root,
  for the `.puml` files and `uml.json`.
- `uml.plantumlJar`, default `''`. Path to the PlantUML jar. Empty means the
  cache folder the script reports as `jarCachePath`.
- `uml.plantumlServer`, default `local`. `local` renders through the jar and
  Java. A URL renders through that PlantUML server instead, with no Java.
- `uml.idleMinutes`, default `30`. Minutes with no request before the page
  server stops itself.

Pass them to the script as flags on every call. `$SKILL_DIR` below is the
folder this file sits in.

## What the person can ask

- `/uml`: reverse-engineer the current repo.
- `/uml src/orders`: only that path.
- `/uml an order service where carts become orders`: draw from the
  description.
- `--diagrams=class,state`: only those types. With no flag, all nine.
- `--regenerate`: write new sources even when some are on disk.

## Run it

1. Check the invocation. Pass the person's words through unchanged:

   ```bash
   node "$SKILL_DIR/scripts/uml.mjs" check --diagrams=class,state src/orders
   ```

   It prints JSON: `mode` (`repo`, `path` or `description`), `target`,
   `diagrams` in page order and `regenerate`. On an unknown diagram type, an
   unknown flag or a path that does not exist, it exits non-zero with a
   message: show that message and stop, before any other work.

2. Check what is on disk and on this machine:

   ```bash
   node "$SKILL_DIR/scripts/uml.mjs" status --output-dir docs/uml --jar '' --server local
   ```

   It prints JSON with `manifest` (`ok`, `missing` or `unreadable`),
   `manifestError`, `java`, `dot`, `layout`, `jar` and `jarCachePath`.

3. Decide whether to write sources:
   - `manifest` is `ok` and there is no `--regenerate`: render only. Skip to
     step 5, and tell the person you reused the sources on disk.
   - `--regenerate`: write new sources (step 4), overwriting the old ones.
   - `manifest` is `missing` or `unreadable`: write sources (step 4), and say
     so, quoting `manifestError` when there is one.

4. Write the sources. Read the code (or the description), then for each type
   in `diagrams`, in order:
   - Read its reference file, listed below, and follow its notation and its
     anti-patterns.
   - Write `<type>.puml` in the output folder, between `@startuml` and
     `@enduml`, with no `skinparam`, `!theme` or colour lines: the script adds
     the theme when it renders.
   - When the source gives no basis for the type, write no file and set
     `noBasis` instead. Do not invent a drawing.

   Then write `uml.json` as `./references/manifest.md` describes: `origin` is
   `code` for the repo or a path and `description` for text; `source` is the
   path (`.` for the repo) or the description word for word.

5. In local mode (`uml.plantumlServer` is `local`):
   - `java` is `false`: stop. Tell the person that rendering needs a Java
     runtime, and that they can install one or set `uml.plantumlServer` to the
     URL of a PlantUML server. Never install Java yourself.
   - `jar` is `null`: offer to download the PlantUML jar from the PlantUML
     GitHub releases to `jarCachePath` (or to `uml.plantumlJar` when set).
     Download only after the person says yes. On a no, stop and tell them to
     download it by hand and set `uml.plantumlJar` to its path.

     ```bash
     node "$SKILL_DIR/scripts/uml.mjs" download-jar --jar ''
     ```

   - `layout` is `smetana`: Graphviz `dot` is missing, so PlantUML uses its
     built-in layout. The page shows a warning; mention it once.

6. Serve the page:

   ```bash
   node "$SKILL_DIR/scripts/uml.mjs" serve --output-dir docs/uml --jar '' --server local --idle-minutes 30
   ```

   It starts the page server in the background on `127.0.0.1` and a free
   port, opens the browser, prints the URL, the PID and the stop command, and
   returns. Pass those three lines on to the person. The server stops by
   itself after `uml.idleMinutes` with no request.

Edits in the page are saved to their `.puml` file 600 ms after the last
keystroke and redrawn. An edit PlantUML cannot parse is still saved; the
section shows the error and keeps the last good drawing, dimmed.

## Diagram selection guide

The page always shows the selected types in this order. For each, draw it when
the source gives a basis, and otherwise set `noBasis` to one sentence on what
is missing. Activity and use-case diagrams are not offered.

### Class

The central domain types, their key members and how they relate. Basis: any
code with classes, interfaces, types or structs; any description that names
things and what they hold. Leave out helpers and framework glue.
`./references/class.md`.

### Sequence

One flow over time. Pick the flow most work passes through, or the one that
touches the most classes, and say which and why in `why`. Basis: a call path
between two or more parts. `./references/sequence.md`.

### State

The lifecycle of one entity. Pick the one with a status field, a state enum or
guarded transitions, and say which and why in `why`. Basis: an entity with
more than two states. `./references/state.md`.

### Profile

Stereotypes the system adds on top of UML. Basis: decorators, annotations,
marker interfaces or framework base classes the system's own classes use.
Most repos have none: then give the no-basis note. `./references/profile.md`.

### Composite structure

The inside of one class or component: parts, ports, connectors. Basis: a
class or module that builds and wires its own collaborators.
`./references/composite.md`.

### Component

Services, modules or libraries and the interfaces between them. Basis: more
than one deployable or separately built unit, or clear module boundaries.
`./references/component.md`.

### Deployment

Where the software runs. Basis: Dockerfiles, compose files, Kubernetes
manifests, Terraform, deploy steps in CI or serverless config. Never guess
infrastructure from the language. `./references/deployment.md`.

### Object

A snapshot of instances and their values. Basis: fixtures, seed data, test
builders or examples. Never make values up. `./references/object.md`.

### Package

How the code is grouped and which groups depend on which. Basis: more than
one folder, module or namespace with imports between them.
`./references/package.md`.

## Rules

- Use the names the code uses, as written.
- One flow per sequence diagram and one entity per state diagram.
- A description is the only source in description mode: draw only what it
  states or clearly implies, and give the no-basis note for the rest.
- The `.puml` files hold diagram text only. The script injects the dark theme,
  the type's accent colour and the colours for interfaces, abstract classes,
  enums and final states at render time, so the files stay clean.
