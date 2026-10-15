# Stakeholder audiences (no code)

There are four presets, `stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner` and `stakeholder-public`, for readers who need to understand what the software does and how far to trust it, **without any code knowledge**.

Unlike the other audiences, these presets don't produce one chapter per abstraction. Each one gets its own short, **question-led page set**, chosen from the menu below. The technical outline and evidence are still the inputs; a planning step translates them into `plain-outline.yaml`.

Pipeline additions:
- **plan**: `tutorial-plain-planner` writes `plain-outline.yaml`, after the outline and evidence steps
- **write**: `tutorial-plain-writer`, one per page per stakeholder audience
- **check**: `check_snippets.py --no-code`, plus the clarity and accuracy critics. The code critic is skipped.

## Zero-code rules (hard rules)

- **No code** anywhere: no code blocks, no inline code, no file paths, no function, class or variable names, no command lines, no configuration syntax.
- **Plain names.** Every component is called by the plain-English name in `plain-outline.yaml` (e.g. "the scheduler", "the results checker"), and that name is used consistently on every page. The technical name appears **once**, in the glossary only, for readers who later need to talk to the developers.
- **Allowed visuals**: `{mermaid}` flowcharts (at most 8 boxes, plain labels, left-to-right or top-down), simple journey diagrams, tables, and (if enabled) value boxes. No class, state or sequence diagrams.
- **Allowed links**: other pages in this audience's folder, the glossary, and, only inside the closing "For the technical team" callout, issue and commit links taken from the evidence.
- Unavoidable terms (e.g. "database", "API") are explained in plain words the first time they appear, and listed in the glossary.

## Writing style (all stakeholder presets)

- Plain English: short sentences, active voice, one idea per paragraph, and lists where they help. British English.
- **Lead with the answer.** Every page opens with an `In brief` callout of 2–4 bullet points:
  ```markdown
  ::: {.callout-note title="In brief"}
  - ...
  :::
  ```
- Use concrete examples in real-world terms: what goes in, what comes out, what a person sees. Use everyday analogies where they help, and never let an analogy stand in for a fact.
- **Be honest about certainty.** Separate what the code *does* from what it *assumes*. Say plainly when something couldn't be determined from the code ("The code doesn't show how long results are kept"). Never guess about data handling, security or accuracy.
- Keep pages short: roughly 400–900 words each, or 300–600 for `stakeholder-public`.
- No marketing tone. Describe value in terms of what the software does, not adjectives.

## Page menu

Each page has a fixed filename, so links and navigation are predictable.

| Page id | File | Question it answers | Main inputs |
|---|---|---|---|
| `overview` | `index.qmd` | What is this, and how do I use this guide? | summary, plain system diagram, project signals, known-issues note |
| `what-it-does` | `what-it-does.qmd` | What problem does it solve, for whom, and what does it produce? | summary, entry points, outputs, a worked example |
| `how-it-works` | `how-it-works.qmd` | What are the main parts, and how do they fit together? | plain components + relationships (a flowchart, then one short section per component) |
| `information-flow` | `information-flow.qmd` | What goes in, what happens to it, and what comes out? Where is it stored or sent? | `data_flows` |
| `your-data` | `your-data.qmd` | What does it use about me, where does it go, and what can I do? | `data_flows` (personal-data items only, conservatively) |
| `how-decisions-are-made` | `how-decisions-are-made.qmd` | What rules, calculations or thresholds does it apply, and how can I sanity-check them? | `decision_points`, tests as validation evidence |
| `reading-results` | `reading-results.qmd` | How should I interpret what it produces, and what are the common misreadings? | outputs, `decision_points`, limits |
| `assumptions-limits` | `assumptions-limits.qmd` | What does it assume, where can it be wrong, and what is known not to work yet? | `assumptions`, evidence (translated) |
| `risks` | `risks.qmd` | What could go wrong, what is in place to prevent it, and what isn't? | assumptions, evidence, `dependencies`, project signals |
| `keeping-it-running` | `keeping-it-running.qmd` | What does it depend on, how actively is it maintained, and what does upkeep involve? | `dependencies`, project signals |
| `changing-it` | `changing-it.qmd` | What is easy or hard to change, and why? | the technical outline (coupling, extension points), evidence |
| `questions-to-ask` | `questions-to-ask.qmd` | What should I ask the development team? | everything above that's uncertain or important |
| `glossary` | `glossary.qmd` | — | `glossary` entries (written by the orchestrator, not a writer) |

## Page plans per preset

The pages appear in this order. `overview` and `glossary` are always included.

| Preset | Label | Reader | Pages (in order) |
|---|---|---|---|
| `stakeholder-decision-maker` | Decision-makers | Managers, funders and executives who decide whether to invest in, adopt or rely on it | overview · what-it-does · how-it-works · assumptions-limits · risks · keeping-it-running · questions-to-ask · glossary |
| `stakeholder-domain-expert` | Domain experts | Subject-matter experts (e.g. clinicians, analysts, policy staff) who must trust and sanity-check what it does in their field | overview · what-it-does · how-it-works · how-decisions-are-made · reading-results · assumptions-limits · glossary |
| `stakeholder-product-owner` | Product owners | People who steer the work: priorities, scope, what to build next | overview · what-it-does · how-it-works · information-flow · changing-it · assumptions-limits · questions-to-ask · glossary |
| `stakeholder-public` | Public | Lay readers and end users | overview · what-it-does · your-data · reading-results · assumptions-limits · glossary |

**Per-preset emphasis:**

- **Decision-makers**: value and outcomes, risk, dependency and maintenance signals. Keep "how it works" to one page of essentials. Be direct about unknowns, and put them in the questions.
- **Domain experts**: precise, in the reader's *domain* language rather than software language. In `how-decisions-are-made`, state every rule, threshold, default and formula the code applies, in words and with real values (e.g. "flags a reading above 140"). Explain how the reader can check it with a known example, and what automated checks exist (from `tests`). Don't oversimplify, because this reader knows their field better than the software does.
- **Product owners**: capabilities and their limits, and what's cheap or expensive to change, with reasons in plain terms (e.g. "this rule lives in one place, so changing it is small; the report layout is spread across several parts, so changing it is bigger"). In `questions-to-ask`, list questions that would help them prioritise.
- **Public**: the simplest language (aim for a reading age of about 12–14), second person ("you"), reassurance only when it's backed by the code, and no internal team concerns. On `your-data`, list **only** personal data the code visibly handles, and say clearly what couldn't be determined. Never state or imply legal compliance.

## Translating evidence

Known limitations come from `evidence.yaml` (markers, issues, rationale), restated in plain language. For example, a FIXME about late-registered handlers becomes "If a new kind of request is added while the system is running, it's ignored until a restart."

- Body text contains **no** issue numbers, commit IDs or file paths.
- `assumptions-limits` (and `risks`, where present) end with a collapsed callout:
  ```markdown
  ::: {.callout-note collapse="true" title="For the technical team"}
  - [Open issue: Router drops handlers registered late](https://github.com/owner/repo/issues/412)
  :::
  ```
- The known-issues note from `evidence.md` goes on the `overview` page (both variants), reworded plainly.

## `plain-outline.yaml` (written by `tutorial-plain-planner`)

```yaml
plain_summary: |                 # 2–4 plain sentences: what it is, who it's for, what it produces
  ...
components:                      # one per outline abstraction, in chapter order
  - id: query_processing         # outline abstraction id
    plain_name: the request handler
    plain_role: Receives each request and decides which part of the system should deal with it.
    technical_name: QueryProcessor (src/query/processor.py)   # glossary only
relationships:                   # outline relationships in plain words, for the flowchart
  - from: query_processing
    to: query_optimisation
    plain_label: passes requests to
data_flows:
  inputs:    [{what: "Uploaded spreadsheets of clinic readings", from: "staff upload", evidence: "src/io/upload.py:12"}]
  stages:    [{what: "Readings are checked for missing values", component: validation}]
  outputs:   [{what: "A summary report (PDF)", to: "downloaded by the user"}]
  storage:   [{what: "Uploaded files are kept in a local folder", retention: "not determined from the code"}]
  external:  [{what: "Email sent via an outside email service", evidence: "src/notify.py:30"}]
  personal_data: [{what: "Patient date of birth", evidence: "src/models.py:44"}]   # [] if none seen
decision_points:                 # rules, thresholds, calculations, defaults the code applies
  - plain: "A reading above 140 is flagged as high"
    evidence: "src/rules.py:18"
assumptions:
  - plain: "Assumes all readings are in the same units"
    evidence: "src/io/upload.py:40 (no unit conversion)"
dependencies:                    # outside services and major third-party components, in plain terms
  - plain: "An outside email service, used for notifications"
glossary:                        # every plain term used, plus unavoidable technical terms
  - term: the request handler
    definition: The part that receives each request and decides where it goes.
    technical_name: QueryProcessor
pages:                           # per stakeholder audience: the plan's pages and what feeds each
  stakeholder-domain-expert:
    - page: how-decisions-are-made
      focus: The three flagging rules and the averaging method.
      uses: [decision_points, components.validation, evidence.tests]
```

Every `data_flows`, `decision_points` and `assumptions` item carries an `evidence` location, so that the accuracy critic can check it. Items that can't be grounded are omitted, or recorded as "not determined from the code".

## Checks

- **`check_snippets.py --no-code --out <audience folder>`** fails on any non-mermaid code block, and warns on inline code, file-path-like text and identifier-like tokens outside `glossary.qmd`.
- **Clarity critic** (as the stakeholder reader) watches for:
  - jargon, and technical names leaking into body text
  - pages that don't answer their question
  - condescension, especially to domain experts
  - missing or unconvincing "In brief" callouts
  - pages over length
- **Accuracy critic** checks every plain claim against the evidence locations in `plain-outline.yaml`, and the code. It watches especially for:
  - simplifications that became false
  - overstated certainty
  - claims about data handling, security or accuracy that the code doesn't support
  - the same component described inconsistently across pages
