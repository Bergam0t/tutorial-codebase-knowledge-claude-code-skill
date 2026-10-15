# Outline schema (`outline.yaml`)

The analyst writes this file and every later stage reads it. It replaces the PocketFlow `shared` store (`abstractions`, `relationships`, `chapter_order`).

```yaml
project_name: my-project

# 3–6 sentences explaining the project's purpose and main functionality, pitched at the
# target audience. Markdown allowed: use **bold** and *italic* to highlight key concepts.
summary: |
  **my-project** is a ...

abstractions:
  - id: query_processing          # short, stable snake_case id; never shown to readers
    name: Query Processing        # display name (in the target language)
    description: |                # ~100 words, includes one simple analogy (target language)
      Explains what the abstraction does.
      It's like a central dispatcher routing requests.
    files:                        # repo-relative paths that best show this abstraction
      - src/query/processor.py
      - src/query/router.py
    key_symbols:                  # classes/functions/config keys the chapter should focus on
      - QueryProcessor
      - route_query()
    tests:                        # advanced audiences only: test files that exercise this abstraction
      - tests/test_router.py

relationships:
  - from: query_processing        # abstraction id
    to: query_optimisation        # abstraction id
    label: Delegates plans        # a few words (target language)
  # Every abstraction must appear in at least one relationship, as from or to.

chapter_order:                    # every abstraction exactly once, foundational first
  - id: query_processing
    filename: 01_query_processing.qmd
    xref: sec-query-processing    # cross-reference id for the chapter heading
    one_line_summary: How a request enters the system and gets routed.
    introduces:                   # terms/concepts this chapter is the home of
      - query
      - router
    builds_on: []                 # ids of EARLIER chapters this one relies on
    # Integration mode only (omit otherwise):
    related_pages:                # existing site pages to link to rather than repeat (from site-profile)
      - get-started/overview.qmd
    api_refs:                     # documented objects this chapter should link (exact inventory names)
      - mypkg.Router
      - mypkg.route
  - id: query_optimisation
    filename: 02_query_optimisation.qmd
    xref: sec-query-optimisation
    one_line_summary: How plans are rewritten to run faster.
    introduces: [query plan, cost model]
    builds_on: [query_processing]
```

## Rules

- **Paths, not indices.** `files` are real repo-relative paths. Writers will open them.
- **Filenames**: `NN_<safe_name>.qmd`. `NN` is the 1-based position in `chapter_order`, zero-padded to 2 digits. `safe_name` is the `name` with every non-alphanumeric character replaced by `_`, lowercased (e.g. `Query Processing` → `query_processing`).
- **xref**: `sec-` + `safe_name` with `_` replaced by `-` (e.g. `sec-query-processing`). Section ids within a chapter extend it (`sec-query-processing-routing`).
- **related_pages / api_refs** (integration mode): paths must come from `existing_pages`, and names from `quartodoc.objects`, in the site profile, copied exactly.
- **introduces** terms also feed the glossary, so name them the way a reader would look them up.
- **Relationships** should be backed by one abstraction actually calling, configuring, or passing data to another. Keep only the important ones. Simple beats complete.
- **introduces / builds_on / one_line_summary** exist because chapters are written in parallel and cannot read each other. Together they give each writer a map of what has been explained and where. Keep `introduces` lists disjoint across chapters where possible.
- **Language**: `summary`, `name`, `description`, `label`, `one_line_summary`, and `introduces` are in the target language. `id`, `files`, and `key_symbols` stay as they appear in the code.
- Quote any YAML string containing `:` followed by a space, or a leading `#`, `*`, `&`, `!`, `[`, `{`.
