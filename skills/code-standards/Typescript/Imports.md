# Imports

## 1. No relative imports

Project code reaches other modules through path aliases, never `./` or `../`. An alias names the module you mean; a relative path only says how far the file happens to sit from it.

Co-located tests are the exception — `Component.test.tsx` may import `./Component` from beside it.

## 2. Import the public API, not internals

Import only what a module publishes. Reaching inside couples you to a detail nobody agreed to keep, and it breaks the moment that detail changes.

## 3. Type-only imports use the inline form

Write `import { type Foo } from '...'` rather than `import type { Foo } from '...'`. The inline form is the one the linter is configured for, and the type is erased at build time either way.

## 4. No circular dependencies

Imports must not form a cycle between modules or files.

## Red flags

Flag these in review:

- `import ... from './...'` or `import ... from '../...'`, outside a co-located test
- `import type ... from '...'`, where the inline form is wanted
