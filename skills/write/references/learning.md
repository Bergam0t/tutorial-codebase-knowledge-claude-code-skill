# Learning aids (`learning=on`)

Opt-in. When `learning=on`, every chapter-based audience gets a short self-test or exercise at the end of each chapter, and the overview pages gain reading paths (and, for contributors, a "first contribution" list). Stakeholder (`stakeholder-*`) pages are unaffected: they have their own question-led pages.

Patterns marked **(tested)** were rendered with Quarto 1.11.

## The section in each chapter

Add one section, `## <heading> {#sec-<xref>-check}`, directly **before** the chapter's Conclusion. The heading and contents depend on the audience:

| Audience | Heading | Contents |
|---|---|---|
| `beginner` | Check your understanding | 3 questions: one recall ("what is X for?"), one reasoning ("what would happen if…?"), one tracing the chapter's central use case step by step |
| `intermediate` | Check your understanding | 3 questions: predict the behaviour of a shown snippet, name an edge case and where it is handled, and "where would you look to change …?" (a file and symbol) |
| `advanced-contributor` | Try it | **One hands-on exercise** (below), plus 2 short "where would you look?" questions |
| `advanced-architect` | Design questions | 3 scenario questions: what happens under a stated load, failure or change, and why the design copes or doesn't |
| `advanced-user` | Check your setup | 3 scenario questions about configuring or using this part: what an option does, what to do for a stated goal, how to tell it worked |
| free text | Check your understanding | Follow the closest preset above |

## Questions and answers **(tested)**

Write each question in bold with a number, then its answer in its own **collapsed** callout directly after it, so a reader can try each one first:

````markdown
**1. Why does the router use a dispatch table?**

::: {.callout-note collapse="true" title="Answer"}
So plugins can add handlers without editing the router. See [Routing](#sec-routing).
:::
````

(In a website, link to the chapter file instead of `#sec-`.)

Rules:
- **Only ask what this chapter teaches.** Every question must be answerable from the chapter or the code it shows or cites. No trick questions, no trivia about names or line numbers, no concepts introduced in later chapters.
- **Answers are short** (1–3 sentences for beginner and intermediate, a little more for advanced), and point back to the section that covers it.
- **Answers are verified.** If a question asks for a result or behaviour, derive it from the code. Never invent output. If the repo doesn't determine the answer, don't ask the question.
- **No new facts in answers.** An answer may not introduce a claim the chapter doesn't support.
- Code in a question follows the usual verbatim / illustrative rules and the style block's length limit.
- Don't make the section longer than about 15% of the chapter.

## The exercise (`advanced-contributor`)

One realistic change a contributor might make in this area, grounded in the code and its tests, written as:

````markdown
## Try it {#sec-<xref>-try}

**Goal.** One sentence: what to change or add (e.g. "Make the router reject duplicate paths.").

**Where to work.** The real files and symbols involved (`src/router.py`, `Router.add`), plus the tests that cover the area.

::: {.callout-tip collapse="true" title="Hint 1: where to start"}
…
:::

::: {.callout-tip collapse="true" title="Hint 2: the shape of the change"}
…
:::

**How to check.** The test command (from the repo's docs or evidence), or the sentence "The repository doesn't document a test command for this area." when none is determined.

::: {.callout-note collapse="true" title="Solution sketch"}
The outline of a change, naming the same files and symbols. This is a sketch, not tested code.
:::
````

Rules for exercises:
- The goal must be achievable by changing the code the chapter covers, and consistent with the "Extending this" section.
- Name only files, symbols and tests that exist.
- Never claim the solution was run or tested. A solution sketch is described in words, or in an illustrative block (marked `.illustrative`).
- Skip the exercise, and use a third "where would you look?" question, if no change is both realistic and verifiable from the code.
- Give the exercise the id `sec-<xref>-try` and the two questions the `-check` id, so both sections can coexist.

## Reading paths (on `index.qmd` of each chapter-based audience)

After the chapter list, add `## Reading paths`: two to four short paths, each a bold goal, one sentence of why, and an ordered list of chapter links (3–5 chapters).
- Goals come from what readers of this audience will actually want. For example: "New to the project" (the first chapters in order), "Adding a new <kind of thing>" (the chapters that cover the extension points), "Debugging a failure" (the chapters on the flow and its error handling).
- Each path must respect prerequisites: before listing a chapter, include the chapters in its `builds_on` that aren't already earlier in the path.
- Only list chapters that exist; use the chapter's filename or `@sec-` xref as usual.

## First contribution (`advanced-contributor` index only)

If `evidence.yaml` has `starter_issues` and `github.status` is `checked`, add `## Your first contribution` after the reading paths, with:
- up to 5 open issues labelled as good for newcomers (title, link, and the chapter that covers the area, if known), described in your own words
- a pointer to `CONTRIBUTING.md` (or the contributing doc in `repo_docs`) when one exists
- the "as of <gathered_on>" date, because issues change

If there are none, or GitHub wasn't checked, omit the section; the Known issues callout already covers it. Never name issue authors.

## Checks

- Clarity critic: does the self-test teach or merely quiz? Are questions answerable from the chapter alone? Is any answer padded or condescending?
- Accuracy critic: every answer, and every exercise's file, symbol and test, is verified against the repo.
- Reviewer: the section exists exactly once per chapter, before the Conclusion, with the right id; answers sit in collapsed callouts; every `starter_issues` link exists in `evidence.yaml`.
