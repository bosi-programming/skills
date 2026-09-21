# Exports

## 1. No `export *`

Never re-export a module wholesale. List the members you mean to publish, renaming at the export line if a name needs to differ. A wildcard puts everything on the public surface now, and anything added later on it by default.

## 2. Barrels for the public API

Use `index.ts` to gather what a module or directory publishes. The barrel is the boundary: what it exports is what callers may use, so export only that.

## 3. Re-export types by name

Types leave a module the same way values do — as explicit named exports.

## 4. Default exports are the exception

Named exports are the default answer: they import explicitly from the module and tree-shake more predictably. A default export earns its place only when a framework requires one.

Where that is true:

1. **Framework requirements** — the framework accepts nothing else.
2. **React components** — named is still preferred, but a default on a component is not worth a comment.

## Red flags

Flag these in review:

- `export * from '...'`
- `export * as ... from '...'`
- a barrel built from several `export *` lines
- a default export where a named one reads clearer, unless a framework requires it
