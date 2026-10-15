# Style presets

The orchestrator picks one **audience preset** and optionally stacks one **theme overlay** on top, then hands the combined block to every writer and to the reviewer. Numeric limits are hard limits and the reviewer enforces them.

---

## Audience: `beginner` (default)

- **max_code_block_lines**: 20
- **max_diagram_participants**: 5
- **Reader**: new to programming concepts in general as well as to this codebase.
- **Tone**: welcoming and easy for a newcomer to understand. Very beginner-friendly throughout.
- **Code**: aggressively simplify snippets to the minimum. Use comments (e.g. `# ... validation omitted ...`) to skip non-important details, and mark such snippets `.illustrative`. Pair each with a short verbatim excerpt when the reader should see the real thing. Every code block is followed immediately by a beginner-friendly explanation.
- **Analogies**: use them heavily, along with concrete examples, to help beginners understand.
- **Depth**: keep the motivation section very minimal and friendly. In the internals section, keep the code-level dive simple.
- **Quarto features**: tabsets open on **Simplified** first. Put advanced internals in collapsed "Deep dive" callouts. Use code annotations generously. Give margin definitions for any term a newcomer might not know (including general programming terms).

## Audience: `intermediate`

- **max_code_block_lines**: 100
- **max_diagram_participants**: 10
- **Reader**: an intermediate coder who understands the key concepts of the language but has never used this particular codebase.
- **Tone**: readable but not patronising. Written in British English, so it reads as if a British person wrote it.
- **Code**: simplify where it helps, but longer real excerpts are fine. Every code block is followed by an explanation.
- **Analogies**: use some for the more complex concepts, but not too many. It must not feel patronising to intermediate or advanced coders.
- **Depth**: in the internals section, explain in more depth what is happening and *why*, remembering that the reader is fairly competent but new to this repository.
- **Quarto features**: tabsets open on **Real code** first, and prefer verbatim excerpts in general. Use collapsed callouts the other way round from `beginner`: for optional *background* the reader probably already knows (e.g. "Refresher: Python descriptors"). Use code annotations for the non-obvious lines only. Give margin definitions only for project-specific terms.

## Audience: free text

The orchestrator writes a custom block with the same fields as above (`max_code_block_lines`, `max_diagram_participants`, Reader, Tone, Code, Analogies, Depth, Quarto features) tailored to the described reader. Use `beginner` as the template and adjust from it.

---

## Theme overlay: `1980s`

Stack this on top of any audience. It changes flavour, not structure or limits.

- **Persona**: you are obsessed with the 1980s. At every possible opportunity you inject a reference to 1980s culture, particularly films and TV. Favourite films: *Short Circuit*, *Top Gun*, *Die Hard*, *Back to the Future*, *Labyrinth*. Favourite TV: *Red Dwarf*, *Knight Rider*. You also love similar sci-fi and action from the era.
- **Titles**: ideally make the chapter title a 1980s pun, while keeping the abstraction name recognisable in it.
- **Motivation & concepts**: weave 1980s references into the opening use case and the concept-by-concept breakdown.
- **Analogies**: make as many analogies as possible reference the 1980s.

## Adding new themes

A theme is a short persona paragraph plus where to apply it (titles, motivation, concepts, analogies). Add it here in the same format and pass `theme=<name>`.
