# Chapter writing guide

You are writing **one** chapter of a multi-chapter tutorial about a codebase. Other writers are producing the other chapters at the same time, and you cannot see their text. The chapter list, `builds_on`, and `introduces` tell you what the rest of the tutorial covers, so you can link to it instead of repeating it.

Apply the **style block** you were given throughout. Its numeric limits are what you aim for. `max_diagram_participants` is a hard limit. `max_code_block_lines` is a target: write blocks at or under it. The reviewer lets a block run up to 20% over (rounded down) rather than split it, but don't plan on using that.

Also follow `quarto-conventions.md`: it covers front matter, code fences, mermaid syntax, and links.

## Before writing

1. Read every file in your abstraction's `files` list. Focus on its `key_symbols`. Grep further if you need to see how the abstraction is called from elsewhere.
2. Only show code that exists. Each snippet is either a **verbatim** excerpt or explicitly marked **illustrative** (see `quarto-conventions.md`). Simplifying is encouraged where the style block asks for it, but a simplified snippet must be marked illustrative. Never invent APIs, parameters, or behaviour.

## Structure

The structure below is the default. If your style block has a **Structure** field, or **Extra sections** (the advanced presets do), apply those on top of it, as described under "Advanced chapters" at the end of this guide.

1. **Title**: use the abstraction name, formatted per `quarto-conventions.md` for the `format` you were given. In a book that is an H1 with your `xref` id; in a website it goes in front matter. Give every `##` section an id derived from your xref.

2. **Transition** (skip for chapter 1): a sentence or two linking back to the previous chapter by name, e.g. "In [Query Processing](#sec-query-processing) we saw…" (book) or "In [Query Processing](01_query_processing.qmd) we saw…" (website).

3. **Motivation**: what problem does this abstraction solve? Open with **one central, concrete use case**. The whole chapter should guide the reader to understanding how that use case is solved.

4. **Key concepts**: if the abstraction is complex, break it into key concepts and explain them one at a time. Do not re-explain anything listed under another chapter's `introduces`: link to that chapter instead.

5. **Using it**: show how to use the abstraction to solve the use case. Give example inputs and outputs for snippets. If the output isn't a value, describe at a high level what happens.

6. **Code blocks**: aim for each block to stay at or under `max_code_block_lines`. If a block would run more than a few lines over, split it into pieces and walk through them in turn: consecutive verbatim excerpts with their own line ranges work well for this. Using comments to skip unimportant details makes a block illustrative, so mark it so. Follow every code block immediately with an explanation pitched at the audience.

7. **Under the hood (walkthrough)**: first a non-code or code-light, step-by-step walkthrough of what happens when the abstraction is used. Include a simple `sequenceDiagram` with a dummy example, using at most `max_diagram_participants` participants. Alias participants that have spaces (`participant QP as Query Processing`).

8. **Under the hood (code)**: dive into the internal implementation with references to the real files (use `filename=` on code blocks). Keep it at the audience's level.

9. **Cross-references**: whenever you mention another core abstraction that has its own chapter, **always** reference it, using the link form for your format from `quarto-conventions.md` and only the xrefs and filenames in the chapter list. For things in `builds_on`, a brief reminder plus a reference beats re-explaining. For terms another chapter `introduces` that you only use in passing, add a margin definition the first time they appear.

10. **Diagrams**: beyond the sequence diagram, use mermaid wherever it genuinely clarifies a complex idea (flowcharts, state diagrams, class diagrams). Label and caption every diagram (`fig-<your xref stem>-…`) and refer to it in the prose by its `@fig-` reference.

11. **Analogies & examples**: use them as the style block directs.

12. **Conclusion**: briefly summarise what was learned, then hand off to the next chapter with a link, e.g. "Next, in [Query Optimisation](02_query_optimisation.qmd), we'll…". For the last chapter, close the tutorial warmly instead.

## Quarto features to use

Part 2 of `quarto-conventions.md` describes the recommended features. Use them as the style block directs:

- **Collapsible deep-dive callouts** for optional depth. Never put essentials in them.
- **Cross-references** (`@sec-…` in books) for every mention of another chapter or section.
- **Labelled, captioned diagrams** referenced as `@fig-…`.
- **Code annotations** for line-by-line walkthroughs, including on verbatim excerpts.
- **Simplified / Real code tabsets** (`group="code-view"`) when a simplified snippet has a meaningful real counterpart. This is the preferred way to keep beginner-friendly code honest.
- **Margin definitions** the first time a key term appears.
- **"View source" links** under verbatim excerpts, when `source_base_url` is provided.

Use them where they help the reader. Don't use every feature in every chapter.

## Advanced chapters (advanced presets)

These rules apply when your style block sets `uses_evidence: true`. Your brief then also includes `evidence.yaml` and `evidence.md`. Read both, and use the entry under your abstraction's id.

- **Compressed structure.** Keep the section order above, but:
  - make the motivation one paragraph, with the use case in a sentence
  - fold the key concepts into the internals
  - keep usage to one short, realistic example (a little more for `advanced-user`)
  - spend most of the chapter on internals and the **extra sections**
- **Extra sections.** Add the `##` sections your style block lists, in its order, after the code-level internals and before the conclusion. Give each an id derived from your xref, e.g. `{#sec-query-processing-sharp-edges}`.
  - Every extra section must be specific to this abstraction and grounded in its code or evidence. If there is genuinely nothing to say, write one honest sentence, e.g. "No known sharp edges beyond the error handling above." Don't pad.
- **Rationale.** For every claim about *why*, cite an evidence item when one exists (commit, doc, issue/PR, or a comment `path:line`). Otherwise phrase it as an inference ("the code suggests…"). Follow the citing rules in `evidence.md`.
- **Limitations and known issues.** Draw on `markers` (TODO/FIXME with `path:line`) and `issues` (linked, "open as of <gathered_on>"). End the section with the single issue-tracker line described in `evidence.md`.
- **Extending this** (`advanced-contributor`): name the concrete files and functions to change, what else must change with them, and the tests that cover the area. Take tests from the evidence `tests` and the outline's `tests`, and give the command to run them if the repo documents one.
- **Verbatim-first.** Real excerpts by default. Mark a block illustrative only for pseudocode, usage examples or example output.

## Learning aids (when `learning` is on)

If your brief says `learning: on`, read `learning.md` and add the section it prescribes for your audience (a self-test, or for `advanced-contributor` an exercise), directly before the Conclusion. Every question and answer must be verifiable from the chapter and the code: never invent output, and never put a new claim in an answer.

## Inside an existing site (integration mode)

When your brief includes a site profile, the chapter is one part of a larger documentation site. Follow `site-integration.md`:
- **Link to the API reference**, don't duplicate it. The chapter explains what a thing is for, how it fits with the rest, and what happens inside; the reference holds signatures and parameters.
- **Link your `related_pages`** where they already cover something ("If you haven't installed the package yet, see [Getting started](../get-started/overview.qmd)").
- **Match the house style** (front matter fields, voice) within the limits of the style block.

## Language

If the language is not English, write the **entire** chapter in that language: explanations, examples, technical prose, diagram labels where appropriate, and link text (using the translated chapter names from the list). Keep code syntax, identifiers, file paths, and required proper nouns unchanged. Translate code comments if practical. Otherwise keep them minimal.

## Output

- Write exactly one file: the output path you were given. Do not touch any other file.
- Run the snippet self-check command from your brief and fix every FAIL before returning: correct the excerpt, or mark it illustrative.
- Return a 2–3 line summary: the use case you chose, the diagrams you included, and anything you could not verify in the source.
