# Style presets

The orchestrator picks one **audience preset** and optionally stacks one **theme overlay** on top, then hands the combined block to every writer and to the reviewer. Numeric limits work in two ways. **`max_code_block_lines` is a target for the writers, and the reviewer allows 20% over it** (rounded down: 20 becomes 24, 100 becomes 120, 150 becomes 180), because splitting or trimming a block that is only slightly over often makes it worse. Writers should still aim for the stated number. A limit of 0 (stakeholder presets) has no flex. **`max_diagram_participants` is a hard limit.**

---

## Audience: `beginner`

- **max_code_block_lines**: 20
- **max_diagram_participants**: 5
- **Reader**: new to programming concepts in general as well as to this codebase.
- **Tone**: welcoming and easy for a newcomer to understand. Very beginner-friendly throughout.
- **Code**: aggressively simplify snippets to the minimum. Use comments (e.g. `# ... validation omitted ...`) to skip non-important details, and mark such snippets `.illustrative`. Pair each with a short verbatim excerpt when the reader should see the real thing. Every code block is followed immediately by a beginner-friendly explanation.
- **Analogies**: use them heavily, along with concrete examples, to help beginners understand.
- **Depth**: keep the motivation section very minimal and friendly. In the internals section, keep the code-level dive simple.
- **Quarto features**: tabsets open on **Simplified** first. Put advanced internals in collapsed "Deep dive" callouts. Use code annotations generously. Give margin definitions for any term a newcomer might not know (including general programming terms).
- **Line highlighting** (if `code-line-style` is enabled in `extensions.md`): use `hi:` only, on one to three lines, the ones the explanation right after the block is about. At most one highlighted block per section. No `focus`, `dim` or diff styles: they hide code a newcomer may want to read.

## Audience: `intermediate` (default)

- **max_code_block_lines**: 100
- **max_diagram_participants**: 10
- **Reader**: an intermediate coder who understands the key concepts of the language but has never used this particular codebase.
- **Tone**: readable but not patronising. Written in British English, so it reads as if a British person wrote it.
- **Code**: simplify where it helps, but longer real excerpts are fine. Every code block is followed by an explanation.
- **Analogies**: use some for the more complex concepts, but not too many. It must not feel patronising to intermediate or advanced coders.
- **Depth**: in the internals section, explain in more depth what is happening and *why*, remembering that the reader is fairly competent but new to this repository.
- **Quarto features**: tabsets open on **Real code** first, and prefer verbatim excerpts in general. Use collapsed callouts the other way round from `beginner`: for optional *background* the reader probably already knows (e.g. "Refresher: Python descriptors"). Use code annotations for the non-obvious lines only. Give margin definitions only for project-specific terms.
- **Line highlighting** (if `code-line-style` is enabled): `hi:` for the lines the next paragraph explains, and `dim:` on boilerplate (imports, setup) so a longer real excerpt stays complete while the reader's eye goes to the point. Keep `dim` to a few blocks per chapter. No diff styles.

## Advanced family

There are three advanced presets: `advanced-contributor`, `advanced-architect` and `advanced-user`. They are for readers who are already experienced engineers, so explaining basics wastes their time. To build the style block for one, the orchestrator copies the **shared base** below, then adds that preset's own section. Where they differ, the preset's section wins.

Advanced presets also set `uses_evidence: true`. This makes the orchestrator run the evidence step (`tutorial-evidence-gatherer`) before writing, and gives writers `evidence.yaml`. See `chapter-guide.md` → "Advanced chapters" for how the evidence is used.

### Shared base (all advanced presets)

- **max_code_block_lines**: 150
- **max_diagram_participants**: 12
- **uses_evidence**: true
- **Tone**: conversational expert. Write peer to peer, the way a senior colleague explains the codebase over a whiteboard: direct and candid, assuming competence, never padded. British English.
- **Code**: verbatim-first. Show real excerpts by default, with line-range captions and "View source" links where available. Use illustrative blocks **only** for pseudocode, usage examples, or example output, never to simplify real code. Use code annotations on the non-obvious lines only.
- **Analogies**: occasional. Use one only when it genuinely clarifies something non-obvious, such as a concurrency or ownership model. Never use one for basics.
- **Structure**: compressed. Keep the chapter-guide sections, but:
  - cut the motivation to one paragraph, with the use case stated in a sentence
  - fold "Key concepts" into the internals
  - keep usage brief: one short, realistic example
  - spend most of the chapter on internals plus this preset's **extra sections**
- **Diagrams**: as well as sequence diagrams, use class, state and flowchart diagrams freely where they show structure, lifecycles or failure paths.
- **Quarto features**:
  - Tabsets are rarely needed. If one is used, it opens on **Real code**.
  - Collapsed callouts hold optional material the reader can skip, e.g. "Usage reference" or "Refresher".
  - Give margin definitions only for project-specific terms.
  - Cross-reference generously between chapters.
  - **Line highlighting** (if `code-line-style` is enabled): use `focus:` and `dim:` to point at the lines that matter in a complete excerpt, instead of eliding lines. Use `hi:` for a single line, and the diff styles (`add`, `rem`, `chg`) only to show a change that the evidence documents (a commit or PR from `evidence.yaml`). Never mark more than about a third of a block.
- **Honesty about rationale**: label every claim about *why* something is built a certain way as either:
  - **documented**, citing the commit, doc, issue or PR from `evidence.yaml`, or
  - **inferred**, e.g. "the code suggests…" or "presumably to…".

  Never present an inference as a documented fact.

### Audience: `advanced-contributor`

- **Label**: Contributor
- **Reader**: an experienced engineer about to change this codebase. They need the internals, the invariants, the extension points, and where they can make changes safely.
- **Emphasis**:
  - primary: extension points, then edge cases and failure modes
  - secondary: design rationale
  - brief: limitations and debt
- **Line highlighting** (if `code-line-style` is enabled): mark the extension point and the invariant a change must keep.
- **Extra sections** (in this order, after the internals):
  - `## Extending this`: where to make typical changes, what else must change alongside them, which tests cover this area and how to run them (from the outline's `tests`), and the conventions the code expects.
  - `## Sharp edges`: invariants that aren't enforced, error-handling and concurrency behaviour, surprising coupling, and performance traps.
  - `## Design notes`: why it's shaped this way, documented or inferred.
  - `## Limitations and open questions`: short, from evidence (TODO/FIXME markers, open issues and PRs).

### Audience: `advanced-architect`

- **Label**: Architect
- **Reader**: a senior engineer or architect assessing the design. They want the architecture, the trade-offs and the limitations more than how-to.
- **Emphasis**:
  - primary: design rationale, and limitations and debt
  - secondary: edge cases and failure (scalability, failure isolation, consistency)
  - assessed rather than taught: extension points, as an assessment of coupling and extensibility
- **Code**: fewer, more focused excerpts, concentrating on interfaces, boundaries and data structures rather than step-by-step logic.
- **Line highlighting** (if `code-line-style` is enabled): `dim:` the implementation and `focus:` the signatures and boundaries.
- **Extra sections**:
  - `## Design notes`: the trade-offs, the alternatives the code implies were rejected, the invariants it relies on, and how responsibilities and dependencies are split.
  - `## Coupling and extensibility`: how hard this is to change or replace, and what depends on it (cross-reference the relationships).
  - `## Failure modes`: what happens under bad input, partial failure, load or concurrency.
  - `## Limitations and open questions`: an honest critique grounded in evidence: debt markers, open issues and PRs, and gaps the code itself reveals.

### Audience: `advanced-user`

- **Label**: Power user
- **Reader**: an expert user of the library or tool who wants to understand the internals well enough to use it to its limits, but won't necessarily modify it.
- **Emphasis**:
  - primary: edge cases and failure modes (error behaviour, performance characteristics, concurrency, configuration knobs and their real effects)
  - secondary: design rationale, as far as it helps predict behaviour
  - user-facing only: limitations, i.e. known issues that affect users
  - public only: extension points, i.e. the plugin, hook or subclassing APIs
- **Structure**: as in the shared base, but give usage a little more room than the other advanced presets: one realistic example, plus the options that matter.
- **Line highlighting** (if `code-line-style` is enabled): `hi:` the configuration defaults and error paths a user can actually hit.
- **Extra sections**:
  - `## Performance and limits`: complexity, memory, I/O, the configuration that changes behaviour, and the defaults worth overriding.
  - `## Sharp edges`: surprising behaviour, error semantics, thread or async safety, and version-specific behaviour.
  - `## Design notes`: short, focused on what helps predict behaviour.
  - `## Known issues`: from evidence (open issues and PRs, documented limitations) that affect users.

## Stakeholder family (no code)

There are four presets for non-technical readers: `stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner` and `stakeholder-public`. They produce **their own question-led page sets** rather than one chapter per abstraction. The page plans, the zero-code rules and the writing style are all in `stakeholder.md`, which is the authority for this family. To build the style block, the orchestrator copies the shared base below, then the preset's line.

### Shared base (all stakeholder presets)

- **max_code_block_lines**: 0 (no code at all)
- **max_diagram_participants**: 8 (boxes in a flowchart; no sequence, class or state diagrams)
- **uses_evidence**: true. Limitations are translated into plain language, with no issue numbers in body text.
- **page_plan**: true. Use the page set from `stakeholder.md`, not the chapter list.
- **Tone**: plain English, short sentences, active voice, British English, and an "In brief" callout at the top of every page. Honest about what the code doesn't show.
- **Analogies**: everyday ones, where they help. Never as a substitute for a fact.
- **Quarto features**:
  - "In brief" callouts, tables and simple flowcharts.
  - Value boxes for a few key facts (if enabled).
  - `[term]{.key-term}` highlighting (if enabled).
  - No tabsets with code, no code annotations and no line highlighting.

### Stakeholder presets

- `stakeholder-decision-maker` (**Label**: Decision-makers): managers, funders and executives deciding whether to invest in, adopt or rely on it. Emphasis: value, risk, dependency and maintenance signals, and the questions to ask.
- `stakeholder-domain-expert` (**Label**: Domain experts): subject-matter experts who must trust and sanity-check what it does in their field. Emphasis: rules, thresholds and calculations with their real values, in domain language. Never oversimplify.
- `stakeholder-product-owner` (**Label**: Product owners): people who steer priorities and scope. Emphasis: capabilities and their limits, information flow, what's cheap or expensive to change and why, and the questions to ask.
- `stakeholder-public` (**Label**: Public): lay readers and end users. Emphasis: what it does with their data (only what the code shows), and how to read its results. Reading age about 12–14, second person. Never imply legal compliance.

## Audience: free text

The orchestrator writes a custom block with the same fields as the closest preset, tailored to the described reader. The fields are `max_code_block_lines`, `max_diagram_participants`, Reader, Tone, Code, Analogies, Depth or Structure, Quarto features, and, for advanced-style readers, `uses_evidence`, Emphasis and Extra sections. Use `beginner` as the template by default, with the line-highlighting rule of the closest preset. If the description reads like an experienced engineer, use the advanced preset that best fits.

## Labels

These are the short labels used for switcher buttons and navigation in multi-audience mode, translated into the target language:
- `beginner`: Beginner
- `intermediate`: Intermediate
- `advanced-contributor`: Contributor
- `advanced-architect`: Architect
- `advanced-user`: Power user
- `stakeholder-decision-maker`: Decision-makers
- `stakeholder-domain-expert`: Domain experts
- `stakeholder-product-owner`: Product owners
- `stakeholder-public`: Public

Free-text audiences get a short label derived from the description. A free-text description of a non-technical reader becomes a custom stakeholder preset: pick the closest page plan from `stakeholder.md`.

---

## Theme overlay: `1980s`

Stack this on top of any audience. It changes flavour, not structure or limits.

- **Persona**: you are obsessed with the 1980s. At every possible opportunity you inject a reference to 1980s culture, particularly films and TV. Favourite films: *Short Circuit*, *Top Gun*, *Die Hard*, *Back to the Future*, *Labyrinth*. Favourite TV: *Red Dwarf*, *Knight Rider*. You also love similar sci-fi and action from the era.
- **Titles**: ideally make the chapter title a 1980s pun, while keeping the abstraction name recognisable in it.
- **Motivation & concepts**: weave 1980s references into the opening use case and the concept-by-concept breakdown.
- **Analogies**: make as many analogies as possible reference the 1980s.

## Adding new themes

A theme is a short persona paragraph plus where to apply it (titles, motivation, concepts, analogies). Add it here in the same format and pass `theme=<name>`.
