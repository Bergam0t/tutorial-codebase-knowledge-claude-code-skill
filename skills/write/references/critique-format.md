# Critique findings format

Each critic is **read-only on the tutorial**. It writes one findings file and edits nothing else. The reviewer applies the findings afterwards in a single pass, so three critics never edit the same file concurrently.

Write YAML to the path you were given (e.g. `<output>/_work/critique/clarity.yaml`):

```yaml
critic: clarity            # clarity | code-fidelity | accuracy
summary: |
  2–4 sentences: overall verdict and the most important themes.
scores:                    # optional, per chapter, 1 (poor) – 5 (excellent)
  01_query_processing.qmd: 4
findings:
  - id: CL-1               # prefix: CL (clarity), CF (code-fidelity), AC (accuracy)
    file: 01_query_processing.qmd
    location: "## Under the hood – 2nd paragraph"   # heading + position, or a short exact quote
    severity: must-fix     # must-fix | should-fix | nit
    issue: What is wrong, in one or two sentences.
    evidence: |            # quote from the chapter and/or source path:line references
      Chapter says "retries three times"; src/net/client.py:88 sets MAX_RETRIES = 5.
    fix: |                 # concrete and directly applicable: replacement text, exact code, or a precise action
      Change "three times" to "up to five times (MAX_RETRIES in client.py)".
```

## Severity

- **must-fix**: wrong, misleading, broken, or a reader would get stuck. This includes every non-illustrative snippet that does not match the source, every false claim, and any concept used before it is explained without a link.
- **should-fix**: it works, but it is noticeably confusing, inconsistent, or weaker than it should be.
- **nit**: polish. The reviewer may skip these.

## Rules

- One finding per distinct problem. Do not bundle.
- `fix` must be specific enough that someone who has not read the source could apply it.
- Do not report problems that the style block deliberately causes (e.g. 1980s references under that theme, or British spelling for `intermediate`).
- If you find nothing at a severity level, that is fine. Do not pad.
