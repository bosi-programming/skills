---
name: code-standards
description: The house coding standards — clean code, TypeScript import and export rules, and frontend accessibility — as a catalog to check code against. Use when code is being reviewed against these standards, when asked what the house standards are, or when writing code in a project that has adopted them.
---

Four files, grouped by what they can govern. Load the ones the code in front of you could actually violate — a backend diff has no use for the accessibility rules.

- `Common/Clean Code.md` — language-agnostic: naming, size, structure, immutability.
- `Typescript/Imports.md` — how TypeScript reaches other modules.
- `Typescript/Exports.md` — what a TypeScript module publishes.
- `Frontend/Accessibility.md` — anything that renders in a browser and takes input.

They sit beside this file; the paths above are relative to it.

## Checking code against it

Read the file that governs the code you are looking at, then hold the change against it hunk by hunk. **A finding names the standard it broke** — the file and the rule — so a reader can go and read it. A rule you cannot point at is an opinion, and an opinion does not belong in a standards finding.

Two rules bind the whole catalog:

- **The repo overrides.** A standard the project documents itself always wins; where the project endorses something this catalog would flag, this catalog says nothing.
- **Tooling has already had its say.** Skip anything a formatter, linter, or type-checker enforces. This catalog exists for what machines do not catch.
