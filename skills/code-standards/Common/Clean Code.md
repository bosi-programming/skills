# Clean Code

Seven rules, and the failures they exist to catch. The rules say what we want; the list at the end is what to call out in review rather than fix quietly.

## 1. Constants over magic values

A bare literal in the middle of logic makes the next reader reverse-engineer what it meant. Give the value a name that states its purpose — `MAX_RETRY_COUNT`, not `3` — and the call site explains itself.

## 2. Names that say what they are

A variable, function, or class should tell you what it holds or does, and why it exists at all. A name that needs a comment to decode is the wrong name.

## 3. One responsibility per unit

Every function, component, hook, and module does one thing, and does it completely. Split it when you see any of these:

- the name needs an "and" in it (`validateAndSave`)
- it runs past roughly 50 lines as a function, or 100 as a component
- it nests more than a couple of levels deep
- it resists being tested

## 4. Don't repeat yourself

The same shape written in two places is two places to fix, and one of them will be forgotten. Extract it into a function, hook, component, or utility, and call that from both.

## 5. Guard clauses at the top

Handle the edge cases first and return. What remains reads as the happy path instead of a climb through nested conditions.

## 6. Immutability by default

Reach for `const`, `Readonly<>`, and values that don't change under a caller's feet. A function that mutates what it was handed is a bug waiting for its second caller.

## 7. Open for extension, closed for modification

New behavior should arrive as new code rather than as edits threaded through code that already works. Composition and polymorphism are how you get there.

## Red flags

Call these out in review:

- a literal that carries meaning with no name on it
- single-letter or vague names, or a name that lies about what it holds
- a function or component whose name needs an "and"
- the same pattern written out twice or more
- indentation past two or three levels
- parameters mutated in place, or `let` where `const` would do
- a promise neither awaited nor returned
- URLs, keys, or API secrets written into source
