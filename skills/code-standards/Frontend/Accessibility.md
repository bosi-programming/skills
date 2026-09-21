# Accessibility

What decides whether the UI works for someone not using a mouse, or not using their eyes. Most of it is cheap while you build and expensive to retrofit, so treat these as build-time checks rather than review findings.

## 1. Actions and navigation

`<button>` for something that acts, `<a href>` for something that goes somewhere. A click handler on `<div>` or `<span>` paints the right picture and reports the wrong semantics — never use one. An `<a>` with no `href` is not a link.

## 2. Headings and landmarks

Heading levels descend without skipping. One `<main>` per page. Where two landmarks share a type, `aria-label` tells them apart.

More than one `<h1>` is acceptable only when each sits inside its own `<section>` or `<article>`.

## 3. Lists and tables

Content that is a list goes in `<ul>` or `<ol>` — screen readers announce the item count, which a stack of `<div>`s never will. `<table>` is for tabular data only, named with `<th scope="col">` plus a `<caption>` or `aria-labelledby`. Never lay a page out with a table.

## 4. Keyboard reachability

Tab reaches every interactive element, in DOM order. `tabIndex` takes only `0` and `-1`. Nothing may trap the keyboard. `aria-hidden="true"` on something focusable is a critical break — `inert` is the tool for that.

## 5. Focus indicator

Every interactive element shows a visible focus indicator. If you drop the default `outline`, put back something that isn't color alone — a ring, a thicker border, an underline. `:focus-visible` is preferred over `:focus`.

The indicator needs **3:1 contrast** against the color beside it (WCAG 1.4.11 Non-text Contrast).

## 6. Modals and dialogs

Opening a modal must move focus in, hold focus there, close on `Escape`, and return focus to the trigger afterwards. Missing any one of the four is critical. Prefer a headless library or the native `<dialog>`.

## 7. Focus on route change

On SPA navigation, move focus to `<main>` or the page `<h1>`. Skip it and a screen-reader user has no signal that the page changed.

## 8. ARIA

The first rule of ARIA is not to use ARIA where a native element already does the job. The second is not to change semantics that need no changing. After that, be correct: every ID reference resolves, every state attribute matches the state it describes, and any ID that ARIA points at comes from `useId()`.

Use `useId()` for any ID an ARIA attribute references — `Math.random()` and hand-rolled counters cause hydration mismatches.

## 9. Live regions

Anything dynamic the user needs to hear goes through a live region. `role="status"` (polite) for routine updates, `role="alert"` (assertive) held back for urgent ones. Live regions announce on **insertion**, so render them conditionally rather than pre-rendering and toggling visibility.

## 10. Composite widgets

Menus, listboxes, comboboxes, tablists, trees and grids follow the [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/patterns/). Reach for a headless library — Radix, React Aria, Headless UI, Ariakit — before hand-rolling one. Composites move focus with **roving `tabindex`**, not `tabIndex={0}` on every item.

## 11. Images, icons and SVG

Every `<img>` carries an `alt`. Decorative images take `alt=""` — present and empty, **not omitted**. Informative images describe the purpose, not the appearance. An icon-only button needs an `aria-label` naming the **action**, with the icon itself `aria-hidden="true"`. A decorative inline SVG gets `aria-hidden="true"` and `focusable="false"`; a meaningful one gets `role="img"` and a label.

## 12. Video and audio

Video with spoken content needs a captions track. Audio needs a link to a transcript. Nothing autoplays with sound. Background video may autoplay only while muted — `<video autoPlay muted loop playsInline aria-hidden="true">`. Nothing on the page flashes more than three times a second.

Use `kind="captions"` for spoken content; `kind="subtitles"` is translation only.

## 13. Color and contrast

Color is never the only signal — status and validation colors travel with an icon, a shape, or text. Body text needs **4.5:1** against its background. Large text (24px / 18pt regular, or 18.66px / 14pt bold), UI components and focus rings need **3:1**.

## 14. Motion

Every non-essential animation respects `prefers-reduced-motion: reduce`. Animate `transform` and `opacity`, which the compositor handles and which disturb the vestibular system less. A carousel that rotates on its own needs a pause control.

## Red flags

Flag these in review:

- `onClick` on a `<div>` or `<span>`; an `<a>` with no `href` used as an action
- a skipped heading level; several `<h1>`s in a flat layout
- stacked `<div>`s holding list content; a `<table>` used for layout
- a positive `tabindex`; `aria-hidden="true"` on something focusable
- `outline: none` or `focus:outline-none` with no `:focus-visible` rule behind it
- a focus indicator that is color and nothing else
- a hand-rolled modal with no focus trap, no return, or no `Escape`
- SPA navigation with no focus move and no live-region update
- ARIA repeating what the native element already says (`<button role="button">`, `<nav role="navigation">`)
- state attributes hardcoded (`aria-expanded="false"` that never changes)
- `Math.random()` or a counter feeding an ARIA reference — `useId()` is the answer
- `aria-live="assertive"` on routine UI; `role="alert"` pre-rendered and toggled with visibility
- an `<img>` with no `alt`; an `alt` describing the icon instead of the action; an icon-only button with no `aria-label`
- a decorative inline SVG with no `aria-hidden="true"`
- autoplay with sound; video with spoken content and no `<track kind="captions">`
- state carried by color alone, e.g. Tailwind `text-red-500` as the only signal
- `transition: all`; an animation with no `prefers-reduced-motion` variant
- an auto-rotating carousel with no pause control
- a composite widget putting `tabIndex={0}` on every item instead of roving
- drag-and-drop with no keyboard path
