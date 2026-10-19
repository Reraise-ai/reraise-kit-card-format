# Card format v2

A card is a small Markdown file: a header of fields between two `---` lines, then free text.
Every piece of knowledge, every source and every decision is a card. Because all tools read and write
the same form, any tool can work with any card.

The machine-readable rules are in [`cardformat/card-v2.schema.json`](cardformat/card-v2.schema.json) (JSON Schema, draft-07).
This page explains them.

## File layout

```
---
format: 2
id: "topic-heating-contract"
type: "topic"
title: "Heating maintenance contract"
created_by: "agent:keeper"
date: "2026-10-01"
language: "en"
release: "private"
---
The contract can be cancelled with three months' notice.
```

- One field per line: `name: value`. Values are JSON: text in double quotes, lists in square brackets, numbers and `true`/`false` as is.
  A value that is not valid JSON is read as plain text. A field may appear only once.
  Values spread over several lines (YAML style) are not supported; such a card cannot be read.
- File name: a short readable name. Decision cards: `E-<number>_<short-name>.md`.

## Fields every newly written card must have

| Field | Meaning | Values |
|---|---|---|
| `format` | format marker | `2` |
| `id` | fixed identifier, unique within the writing tool | text |
| `type` | kind of card | e.g. `source`, `topic`, `decision`, `proposal`, `claim`, `evidence` |
| `title` | title | text |
| `created_by` | who created the card | `human` or `agent:<name>` |
| `date` | date of the statement | `YYYY-MM-DD` |
| `language` | language of title and text | e.g. `de`, `es`, `en` |
| `release` | may it leave the machine? | `private` (default), `community`, `commercial` |

## Optional fields

| Field | Meaning |
|---|---|
| `source` | where it comes from: a path, an address or a card id. **Required** when `layer` is `evidenced` or `said`. |
| `sourceChecksum` | checksum of the original file (for evidence and text copies) |
| `layer` | kind of statement: `evidenced` (backed by a document), `said` (someone said it), `experience` (lived experience) |
| `originSystem` | which tool wrote the card |
| `worlds`, `tags`, `edges` | groupings, keywords, links to other cards |
| `training` | `true`/`false`: may be used for training |

Any other field is allowed. Version 2 only adds; it never removes or renames.

## Decision cards (`type: "decision"`)

A decision is something a human decided. It is only a decision card if the human's own words are on it.

| Field | Meaning | Required |
|---|---|---|
| `number` | running number, same as in the decision log (1, 2, 3 ...; shown as E-1, E-2 ...) | yes |
| `question`, `choice` | the question and what was chosen | yes |
| `options` | the possibilities | no |
| `decision_type` | `decision`, `revision`, `postponed`, `delegated` | yes |
| `decided_by` | the human who decided (`human` or a name; never `agent:...`) | yes |
| `decided_quote` | the human's sentence, word for word | yes |
| `decided_ref` | where the sentence was said: channel, session, time | yes |
| `captured_by` | the agent that wrote the card, preferably `agent:<name>` | yes |
| `expected_outcome`, `review_date` | what is expected and when to ask again | no |
| `actual_outcome`, `hit` | what happened and whether the expectation was met | no |
| `guardrails` | which of the owner's guardrails are touched | no |

Suggested sections in the text: Situation, Trigger, Decided by, Captured by, Conditions, Facts, Priorities,
Action, Alternatives, Excluded, Reasoning, Cards used, Outcome.

## Proposal cards (`type: "proposal"`)

Without a word-for-word quote and a reference, it is not a decision but an agent's proposal.

| Field | Meaning | Required |
|---|---|---|
| `proposed_by` | the agent that proposes, `agent:<name>` | yes |
| `question` | what is to be decided | yes |
| `number` | not allowed: only confirmed decisions get a number | – |

## Rule for every card: `decided_by` only with a quote

`decided_by`, `decided_quote` and `decided_ref` always come together. A card may name a human as decider
only if it also carries the human's sentence and where it was said.

## Locked fields

`level` and `signature` must not be used until a separate decision allows them.
A personal belief ("I believe") is never part of a card.

## Read rule for older field names

Older cards use other names for the same thing. Every tool reads both. **No file is ever rewritten.**

| Canonical (written) | Also read | Value translation when reading |
|---|---|---|
| `created_by` | `urheber`, `author` | `mensch` becomes `human`; `agent:<name>` stays. `agent:unbenannt` stays valid but is reported as "author unclear". |
| `source` | `quelle` | unchanged |
| `layer` | `ebene` | `belegt` becomes `evidenced`, `gesagt` becomes `said`, `erfahrung` becomes `experience`. `geglaubt` is a private belief, not a layer, and is not taken over. |
| `originSystem` | `herkunft_system` | unchanged |
| `worlds`, `edges` | `welten`, `kanten` | unchanged |
| `training` | `training` | `ja` becomes `true`, `nein` becomes `false` |

1. If only the older name is present, it counts as the canonical one.
2. If both are present and agree: fine. If they disagree: the canonical field applies, and the card is reported. Nothing is corrected automatically.
3. New cards are written with canonical names only. The validator's `--strict` mode rejects older names.
4. Old cards are never rewritten.
5. `author` is only produced at the boundary to a public card exchange: `author` = `created_by`; for decision cards `author` = `human`.
   `decided_by`, `decided_quote` and `decided_ref` never leave the machine.
6. Cards without `format: 2` are read with the read rule but not checked against v2.

Going back: the rule only affects reading. If it changes, every card stays as it is.
