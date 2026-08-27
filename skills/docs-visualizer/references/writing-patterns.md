# Writing pattern catalog

For each pattern: the roles to use in `participants`, the signals that justify
naming it, and the look-alike it gets confused with. Naming a pattern is a claim
about intent, so the signal is the bar - if you cannot point at it in the diff,
drop the claim or mark it `low`.

Each entry carries a Reference line. The page shows the same link under the
pattern name, but it reads it from the `REFERENCE` map in
`scripts/render_docs_graph.py`, not from here. Change one and change the other.

Contents: [Structure](#structure) · [Orientation](#orientation) ·
[Anti-patterns](#anti-patterns) · [Rhetorical moves](#rhetorical-moves)

## Structure

**Inverted pyramid** — roles: Lede, Body.
Reference: <https://www.nngroup.com/articles/inverted-pyramid/>
Signal: the outcome, the cost and the answer land in the first paragraph, before
any background. A reader who stops after three lines still got the point.
Look-alike: a doc that opens with a heading and a one-line "this document
describes…" summary of itself. That is a table of contents, not a lede.

**Progressive disclosure** — roles: Overview, Detail.
Reference: <https://www.nngroup.com/articles/progressive-disclosure/>
Signal: the common path runs unbroken, and the edge cases sit behind a link, a
collapsed block or a later section. Look-alike: content split across files for
filing reasons, with no reading order between them.

**Diátaxis role** — roles: Tutorial, How-to, Reference, Explanation.
Reference: <https://diataxis.fr/>
Signal: one document does exactly one of the four jobs. A how-to is a numbered
path to one outcome; a reference is complete and unordered; a tutorial is a
guaranteed-to-work lesson; an explanation argues. Name the role the document
takes, and name the Source node when a change split a mixed doc into two.
Look-alike: a "guide" that alternates steps and lookup tables is not a how-to
with a reference section - it is the mix the split exists to undo.

**ADR context-decision-consequence** — roles: Context, Decision, Consequence.
Reference: <https://adr.github.io/>
Signal: all three headings present, and the Decision states what was chosen in
the past tense. Look-alike: a design doc that proposes; an ADR records.

**Runbook step-and-check** — roles: Step, Check, Rollback.
Reference: <https://developers.google.com/style/procedures>
Signal: every step ends in an observable the operator can verify, and there is a
stated way back. Look-alike: a numbered list of commands with no checks - that
is a script, and it is worth saying so in `note`.

**Worked example** — roles: Setup, Example, Result.
Reference: <https://diataxis.fr/tutorials/>
Signal: a complete, runnable case with its real output, not a fragment with
`...`. Look-alike: a snippet that shows the API shape but cannot be run.

## Orientation

**Glossary-first** — roles: Glossary, Consumer.
Reference: <https://developers.google.com/style/abbreviations>
Signal: house terms are defined once in a glossary and linked from first use, so
the prose can stay short. Look-alike: a glossary nothing links to - that is an
orphan, and it belongs in the anti-patterns below.

**Prerequisites block** — roles: Prerequisite, Task.
Reference: <https://diataxis.fr/how-to-guides/>
Signal: the access, tools and state the reader must already have, stated before
step one, where a missing prerequisite costs a minute instead of an hour.

**Signposted hierarchy** — roles: Parent, Child.
Reference: <https://developers.google.com/style/headings>
Signal: headings that are claims or tasks ("Run the dev server"), nested no more
than three deep, readable as a list on their own. Look-alike: headings that are
nouns ("Overview", "Details", "Notes") - see *Heading that is not a claim*.

## Anti-patterns

Name these with the same card shape. Say in `intent` that it is an anti-pattern,
and put the fix in `note`. An anti-pattern with evidence is the single most
useful thing this page produces; one without evidence is a slur.

**Buried lede** — roles: Lede, Burial.
Reference: <https://www.nngroup.com/articles/inverted-pyramid/>
Signal: the thing the reader came for sits below background, history or scope
notes. Measure it: name the line the answer is on.

**Undefined jargon** — roles: Term, First use.
Reference: <https://developers.google.com/style/jargon>
Signal: a house term, product name or acronym used before it is defined, with no
glossary link. Look-alike: standard technical vocabulary for the stated
audience; a backend runbook may say "idempotent" without apology.

**Wall of text** — roles: Block.
Reference: <https://www.nngroup.com/articles/chunking/>
Signal: a paragraph past roughly 120 words, or a section past roughly 500, with
no list, break or heading. Look-alike: a reference section that is meant to be
long - check the Diátaxis role first.

**Orphan section** — roles: Orphan.
Reference: <https://www.writethedocs.org/guide/writing/docs-principles/>
Signal: no inbound link or reference anywhere in the repo, and no place in a
reading order. Prove it with the grep you ran.

**Dead link** — roles: Source, Missing target.
Reference: <https://developers.google.com/style/link-text>
Signal: a relative link or anchor that does not resolve after the change. The
anchor case is the one a diff hides: deleting a heading breaks every link to it,
in files the diff never touched.

**Duplicated content** — roles: Original, Copy.
Reference: <https://www.writethedocs.org/guide/writing/docs-principles/>
Signal: the same facts stated in two places, where one will be updated and the
other will not. Look-alike: a deliberate summary that links to the full version.

**Missing prerequisite** — roles: Task, Unstated requirement.
Reference: <https://diataxis.fr/how-to-guides/>
Signal: a step that cannot succeed without access, a tool or a state the document
never mentions.

**Passive throat-clearing** — roles: Sentence.
Reference: <https://developers.google.com/style/voice>
Signal: sentences that describe the document rather than the subject - "It should
be noted that", "This section will describe", "Care must be taken". Quote one.

**Heading that is not a claim** — roles: Heading.
Reference: <https://developers.google.com/style/headings>
Signal: nouns where a task or an assertion belongs ("Overview", "Notes",
"Miscellaneous"), so the heading list tells a reader nothing.

**Stale reference** — roles: Reference, Moved target.
Reference: <https://google.github.io/styleguide/docguide/best_practices.html>
Signal: a path, flag, command or ticket named in the prose that no longer exists
in the repo. Check the ones the change touches; you are already reading them.

## Rhetorical moves

The `moves[]` kinds, with the textual signal and the trap that produces a false
positive. A move needs a node, a `ref` and the words themselves.

**claim** — an assertion the reader is asked to accept.
Signal: a statement of fact about behaviour, timing, cost or safety, in the
present tense, with no source attached. Trap: an instruction is not a claim; "run
X" asserts nothing.

**evidence** — what backs a claim.
Signal: a command with its real output, a log line, a benchmark, a link to the
code or the ticket that settles it. Trap: a link that only points at more prose
is a reference, not evidence.

**caveat** — a named limit on a claim.
Signal: the condition under which the surrounding text stops being true, stated
specifically. Trap: a caveat names the condition; a hedge avoids naming it.

**hedge** — vagueness where a number or a condition belongs.
Signal: "usually", "in most cases", "should generally", "might", stacked or
standing in for a fact the writer could have looked up. Trap: honest uncertainty
about something genuinely unknown is a caveat; the hedge is the one that could
have been resolved.

**definition** — a term given a meaning.
Signal: "X is …", a glossary entry, a parenthetical gloss at first use.

**assumption** — a precondition the text relies on without arguing for it.
Signal: "assumes", "you already have", or a step that only works given unstated
state. Trap: a stated prerequisite is a good assumption; name it anyway, since
the page's job is to show where the argument rests.

**instruction** — a thing the reader is told to do.
Signal: imperative mood, usually a command or a UI action. Trap: only mark the
ones that carry weight; a nine-step guide has nine, and listing all of them
buries the moves that matter.

**contradiction** — the text disagrees with the repo or with itself.
Signal: two statements that cannot both hold, or one statement against a config,
a default or a code path you opened. Trap: an out-of-date statement you have not
checked is a `claim` with `low` confidence, not a contradiction. Read the file
before you use this kind.
