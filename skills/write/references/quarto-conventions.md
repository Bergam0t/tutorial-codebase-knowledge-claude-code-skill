# Quarto conventions

Every generated `.qmd` must render cleanly with `quarto render`, with **no warnings**. These rules apply to chapter writers, the orchestrator (for `index.qmd` and `glossary.qmd`), and the reviewer. All syntax here has been verified against Quarto 1.11.

Part 1 contains hard rules. Part 2 contains the recommended features that make the tutorial easier to use: use them wherever they help the reader.

# Part 1 — Hard rules

## Chapter titles

**book** format: the first line of the file is an H1 carrying the chapter's cross-reference id (`xref` in the outline). There is no front matter `title`. Quarto numbers chapters itself, so leave "Chapter N" out of the heading. The id is what lets other chapters write `@sec-query-processing`.
```markdown
# Query Processing {#sec-query-processing}
```

**website** format: there is no automatic numbering and no cross-page `@` references, so the title goes in front matter and includes the number. Don't put a `#` H1 in the body.
```markdown
---
title: "Chapter 3: Query Processing"
---
```
Always double-quote front matter titles and escape embedded `"` as `\"` (pun titles under a theme often contain `:`).

In both formats, body sections start at `##`. Give each major section an id so that other chapters can link to it: `## How routing works {#sec-query-processing-routing}`. The convention is the chapter's `xref` plus a short suffix.

### index.qmd and glossary.qmd

- **book**: `index.qmd` starts with `# Overview {.unnumbered}`, and `glossary.qmd` with `# Glossary {#sec-glossary}`. The glossary is listed under `appendices`, so it is labelled "Appendix A".
- **website**: both use front matter titles (`"Overview"`, `"Glossary"`) and have no body H1.

## Code blocks

Every code block (other than mermaid) is **exactly one** of two kinds, and must be marked as such. `check_snippets.py` enforces this mechanically.

### Verbatim excerpt

Contiguous lines copied **exactly** from a repo file: no edits, no `...`, no added comments. The only things you may change are removing uniform leading indentation, trimming leading/trailing blank lines, and appending code-annotation markers (see Part 2). The caption is the repo-relative path, ideally with the line range:

````markdown
```{.python filename="src/query/processor.py:42-58"}
def route(self, query):
    ...exact lines 42–58...
```
````

### Illustrative

Anything that is not an exact excerpt: simplified or elided code, code with added explanatory comments, usage examples, example output, shell commands, or pseudocode. Add the `.illustrative` class **and** a visible caption that tells the reader what it is:

````markdown
```{.python .illustrative filename="Simplified from src/query/processor.py"}
def route(self, query):
    # ... validation omitted ...
    return self.handlers[query.kind](query)
```
````

Suggested captions: `Simplified from <path>`, `Example usage`, `Example output`, `Shell`, `Pseudocode`. Illustrative code must still use real names and signatures from the repo, unless the prose makes clear that something is hypothetical.

### General

- Use the braced attribute form shown above. **Never** use ```` ```{python} ```` (without the dot), because Quarto would execute it. Never leave a plain ```` ```python ```` block with no caption, because it would be neither verbatim nor illustrative.
- Always include the language class (`.text` if nothing else fits).
- Never translate identifiers. Comments may be translated only in illustrative blocks.
- When in doubt, mark it illustrative. An honest "simplified" label is always better than a near-miss "verbatim" one.

### Included excerpts (only when `include-code-files` is enabled)

A third kind of block, **included**, is verbatim by construction: an empty block with `include="<path relative to this .qmd>" start-line=… end-line=…` plus the usual `filename="path:start-end"` caption. Its full syntax and rules are in `extensions.md`. Use it for verbatim excerpts **only** if `_work/extensions.md` lists the extension.

## Extensions

Use only the extensions listed in `_work/extensions.md` for this run, with exactly the syntax given there. Syntax from an extension that isn't installed either breaks the render (shortcodes) or silently does nothing (attributes and classes).

## Diagrams

- Mermaid diagrams use Quarto's cell syntax: ```` ```{mermaid} ````, **not** ```` ```mermaid ````.
- In `sequenceDiagram`, alias any participant with spaces: `participant QP as Query Processing`.
- Avoid unescaped double quotes and semicolons inside labels. Keep node and edge labels short.

## Links between chapters

- **book**: refer to chapters and sections with cross-references: `@sec-query-processing` renders as "Chapter 2", and `@sec-query-processing-routing` as "Section 2.3". To use the chapter name as link text, write `[Query Processing](#sec-query-processing)`: Quarto resolves `#sec-…` anchors across book chapters. **Never** write `[text](@sec-…)`, because it renders as a silently broken link. Use only ids from the chapter list you were given, and ids of sections you can see exist.
- **website**: `@sec` references do **not** resolve across pages, so use Markdown links to the file, with an anchor where useful: `[Query Processing](02_query_processing.qmd)` or `[routing](02_query_processing.qmd#sec-query-processing-routing)`. `@sec`/`@fig` references to things *on the same page* are fine.
- In either format, `.qmd` links are rewritten to `.html`. Never invent a filename or id.

## Misc

- No raw HTML unless it is unavoidable.
- No trailing attribution footer in chapter files. It lives in `_quarto.yml` `page-footer`.
- Files are UTF-8.

# Part 2 — Recommended features

Use these where they genuinely help. The style block says which ones to lean on for the audience. Each item below shows the verified syntax.

## 1. Collapsible deep-dive callouts

These let one tutorial serve readers at more than one level: optional depth stays hidden until someone wants it.

```markdown
::: {.callout-note collapse="true" title="Deep dive: why routing is lazy"}
Detail that the main thread of the chapter doesn't need...
:::
```

Use `callout-tip` for analogies and `callout-warning` for gotchas (both are usually expanded, so leave out `collapse`). **Never hide something the rest of the chapter depends on** inside a collapsed callout. Aim for one to three callouts per chapter.

## 2. Cross-references

See "Links between chapters" above. In books, prefer `@sec-…` over hand-written links: Quarto numbers them, and the reviewer catches broken ones as render warnings.

## 3. Figure labels and captions on diagrams

````markdown
```{mermaid}
%%| label: fig-query-processing-flow
%%| fig-cap: "What happens when a query arrives"
sequenceDiagram
  ...
```
````

Then refer to it in the prose as `@fig-query-processing-flow` ("Figure 2.1"). Start labels with `fig-` followed by the chapter's xref stem, so they are unique across the book. Caption every diagram that the prose refers to.

## 4. Code annotations

These suit walkthroughs: numbered markers in the code, with explanations underneath (or shown on hover). Append the marker as a comment in the block's language at the **end** of a line, and follow the block immediately with a numbered list:

````markdown
```{.python filename="src/query/processor.py:42-44"}
def route(self, query):                      # <1>
    handler = self.handlers[query.kind]      # <2>
    return handler(query)
```
1. Every query enters here.
2. The handler is picked by the query's `kind`, which is the dispatch table from @sec-query-processing-routing.
````

Annotation markers are allowed on verbatim excerpts: `check_snippets.py` ignores them. `_quarto.yml` sets `code-annotations: hover`. Use annotations instead of a separate prose explanation when the block is mostly about "what does each line do". Keep a short prose sentence after the list saying what the block achieves overall.

## 5. Simplified / Real code tabsets

These pair an illustrative snippet with the verbatim original:

````markdown
::: {.panel-tabset group="code-view"}
### Simplified
```{.python .illustrative filename="Simplified from src/query/processor.py"}
...
```

### Real code
```{.python filename="src/query/processor.py:42-71"}
...exact lines...
```
:::
````

- Always use `group="code-view"` with the tab names exactly `Simplified` and `Real code`. Tabsets that share a group stay in sync, so readers who prefer the real code only have to choose once.
- The tab order sets the default: the first tab opens first. The style block says which tab goes first.
- The "Real code" tab may exceed `max_code_block_lines` up to **3×** the limit, because it is opt-in. The "Simplified" tab must respect the limit.
- The tab headings must be one level below the section they are in.

## 6. Glossary and margin definitions

- The orchestrator builds `glossary.qmd` from every chapter's `introduces` terms, using a definition list that links back to the home chapter:
  ```markdown
  Query plan
  : The ordered steps chosen to answer a query. See @sec-query-optimisation.
  ```
- In chapters, give a quick definition in the margin the **first** time a key term appears, especially terms from another chapter's `introduces` that this chapter only uses in passing:
  ```markdown
  ::: {.column-margin}
  **Query plan**: the ordered steps chosen to answer a query. See the [glossary](glossary.qmd).
  :::
  ```
  Keep margin notes to one or two sentences each, and at most a handful per chapter.

## 7. Links to the source

- `_quarto.yml` adds a "Source code" link to the sidebar that points at the repository (set by the orchestrator).
- If the brief gives a `source_base_url` (a permalink to the exact commit), put a small source link directly under each **verbatim** excerpt whose caption has a line range:
  ```markdown
  [View source](<source_base_url>src/query/processor.py#L42-L58){.small}
  ```
  Use `#L42-L58` for GitHub/GitLab-style hosts. If `source_base_url` is "none", leave these links out. Do not guess URLs.
