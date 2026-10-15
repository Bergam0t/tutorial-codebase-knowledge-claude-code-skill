# Integrating with an existing Quarto / quartodoc site

This applies when the skill runs with `docs=<path>`: the tutorial is added to an existing Quarto project (often a quartodoc API-reference site) instead of becoming a standalone project. Everything else in the pipeline is unchanged. This file covers only what is different.

Patterns marked **(tested)** were verified with Quarto 1.11 and quartodoc 0.11 (with griffe 1.9).

## Principles

- **The site belongs to the user. Only add to it.** Build around what is there, and never restructure it.
- **Files you may create**: anything under `<docs>/<section>/` (default `section=tutorial`).
- **The only existing file you may edit**: `<docs>/_quarto.yml`. Insert text minimally and keep its comments, ordering and formatting. **Never** load and re-dump it with a YAML library, because that strips comments and reorders keys.
- **Never touch**: existing pages, the `quartodoc:` block, the generated reference directory (including `_sidebar.yml`, which quartodoc regenerates), `objects.json`, `_extensions/`, themes, or `metadata-files`.
- If `<docs>/<section>/` already exists and isn't empty, **stop and ask the user** whether to replace it or use a different section name.
- `format` is forced to the project's type (`website` or `book`). Ignore any `format=` argument and say so.

## Site profile (`_work/site-profile.yaml`)

The `tutorial-site-surveyor` writes this file. Every later stage reads it.

```yaml
docs_dir: docs                       # relative to the target repo
project_type: website                # website | book
section_dir: tutorial                # where the tutorial will live, relative to docs_dir
git_tracked: true                    # is docs/_quarto.yml tracked by git?

navigation:
  pattern: multi-sidebar             # multi-sidebar | single-sidebar | navbar-only | book
  details: |
    navbar.left has Get started, Reference. Sidebars come from reference/_sidebar.yml
    via metadata-files (a list with ids); _quarto.yml itself has no website.sidebar key.
  insertion_plan: |                  # exact text to insert, and where (quote the anchor lines)
    After the line "        text: Reference" in navbar.left, insert:
          - href: tutorial/index.qmd
            text: Tutorial
    Then, directly under "website:" children (after the navbar block), insert:
      sidebar:
        - id: tutorial
          title: Tutorial
          contents: [<filled in by the orchestrator>]

existing_pages:                      # hand-written pages only (not the generated reference)
  - path: get-started/overview.qmd
    title: Overview
    summary: Installing the package and a first query.
    covers: [installation, basic query]

house_style:
  front_matter_fields: [title, description]   # fields existing pages use
  callouts: sparing, mostly callout-note
  code: executable {python} cells with freeze   # we still never emit executable cells
  notes: Second person, short paragraphs, British spelling.

quartodoc:
  present: true
  package: mypkg
  reference_dir: reference
  reference_built: true              # are the reference .qmd files present?
  reference_tracked_in_git: false
  inventory: objects.json            # path relative to docs_dir, or null if absent
  interlinks_filter: true            # "interlinks" listed under filters
  link_style: interlinks             # interlinks | relative | none (see "API links" below)
  objects:                           # every documented object, exact inventory names
    - name: mypkg.Router
      page: reference/Router.qmd
    - name: mypkg.route
      page: reference/route.qmd

tools:
  quarto: "1.11.0"
  quartodoc_installed: false
```

## Navigation wiring

All edits are additive text insertions into `<docs>/_quarto.yml`. Back up the file to `_work/_quarto.yml.orig` first.

**Website, multi-sidebar (the quartodoc default) (tested)**: quartodoc's sidebar lives in `reference/_sidebar.yml` as a list of sidebars with ids, merged in through `metadata-files`. To add the tutorial:
1. Add a navbar item `- href: <section>/index.qmd` / `text: Tutorial` at the end of `website.navbar.left`.
2. Add a sidebar with its own id. If `_quarto.yml` has no `website.sidebar`, add one as a **list**:
   ```yaml
     sidebar:
       - id: tutorial
         title: Tutorial
         contents:
           - tutorial/index.qmd
           - tutorial/01_router.qmd
           - tutorial/glossary.qmd
   ```
   If `website.sidebar` is already a list, append this item to it. Quarto merges it with the metadata-file sidebars, and the reference sidebar keeps working (tested).

**Website, single sidebar** (`website.sidebar` is a mapping with `contents`): append a section to its `contents`, and don't convert the mapping to a list:
```yaml
      - section: "Tutorial"
        contents:
          - tutorial/index.qmd
          - ...
```

**Website, navbar only**: use the multi-sidebar recipe (navbar item plus a new sidebar list).

**Book**: append a part to `book.chapters`, before `appendices` if present. Put the glossary inside the part, not in `appendices`, so that the user's appendices stay untouched:
```yaml
    - part: "Tutorial"
      chapters:
        - tutorial/index.qmd
        - tutorial/01_router.qmd
        - tutorial/glossary.qmd
```
Book chapter numbering continues from the existing chapters. That's fine, because book titles carry no number.

## Links

- **Within the tutorial**: as in `quarto-conventions.md`.
- **To existing pages**: relative paths from the tutorial file, e.g. `[Getting started](../get-started/overview.qmd)`. Only link pages listed in `existing_pages`. When an existing page already explains something, link to it instead of re-explaining (tested).
- **API links (quartodoc)**: choose by `link_style`:
  - `interlinks` (the filter is configured) **(tested)**:
    - `` [](`~mypkg.Router`) `` renders as `Router`
    - `` [](`mypkg.route`) `` renders as `mypkg.route`
    - `` [the router class](`mypkg.Router`) `` gives custom text
    - `` [](`~mypkg.Router.dispatch`) `` links a member
  - `relative` (no filter, but the reference is built): `[Router](../reference/Router.qmd)`, using the `page` from the profile.
  - `none`: write the name as inline code, with no link. Never guess a link.
- Use **exact inventory names** from `quartodoc.objects`. An interlink to an unknown name renders **silently** as plain code with no warning (tested), which is why `check_links.py` verifies interlinks against `objects.json`.
- Link the **first** mention of each public symbol in a chapter. Don't reproduce parameter tables or full signatures. The tutorial explains concepts and flow; the reference documents the API. "See [](`~mypkg.Router`) for every option" is the pattern.
- Objects missing from `quartodoc.objects` are internals. Show them in code if useful, but describe them as internal details rather than as API.

## House style

Follow `house_style` wherever it doesn't conflict with the hard rules:
- include the same front matter fields (e.g. a `description:`)
- callout habits
- voice notes, where they are compatible with the audience preset (the preset wins on depth and limits)

**Always emit non-executable code blocks**, even if the site executes cells: the tutorial must not depend on the site's runtime or slow its build.

## Verification

Run from the target repo:
- `check_snippets.py --repo <target> --out <docs>/<section>`
- `check_links.py --out <docs>/<section> --project <docs>` (it finds `<docs>/objects.json` automatically)
- **quartodoc build**: needed only if `reference_built` is false or `inventory` is null, and then only if quartodoc is installed and the reference directory is **not** tracked in git (otherwise you would rewrite committed files). Run `quartodoc build` from `<docs>` with the package importable (installed, or on `PYTHONPATH`). If it can't run, say so: interlinks then can't be verified, and the reference pages they point to won't exist yet.
- **Render (tested)**: `quarto render <docs>/<section>` renders only the tutorial pages, using the site's config, and doesn't execute other pages' code. Don't run a full-site render. Instead, tell the user to run `quarto render <docs>` (or `quarto preview <docs>`).
- Delete `<docs>/_site` (or `_book`) afterwards only if it didn't exist before.
- Report the `_quarto.yml` change as a diff (`git diff -- <docs>/_quarto.yml` if tracked, otherwise compared with the backup). Keep the backup next to the original as `_quarto.yml.pre-tutorial.bak` if the file isn't tracked in git.
