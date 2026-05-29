# dot-slides

Turn a Graphviz **DOT** diagram into a browser-only **HTML zoom-presentation**.
Each numbered cluster/node becomes a slide; arrow keys animate the camera
from one to the next.

No build tools, no server, no install on the viewer's side — the output is
a small HTML file plus a shared `runtime.js` / `runtime.css`, which opens
straight from `file://` or via any static host.

## Quick start

```sh
# Render every presentations/*.dot to .svg + .html
python3 build_presentation.py

# Or just one
python3 build_presentation.py presentations/foo.dot
```

Requirements: **Python 3.10+** and **Graphviz** (`dot` on `$PATH`). The
generated HTML has zero runtime dependencies beyond `runtime.js` /
`runtime.css` (loaded via relative paths from `..`).

## Authoring

See **[AGENTS.md](./AGENTS.md)** for the full authoring guide — prefix
forms, where the slide number goes, build invariants, minimum viable
presentation, and common mistakes.

The short version: prefix the label of every cluster or node you want as
a slide with a circled digit (`①`–`⑳`), and the build orders slides by
that number.

## Project layout

```
dot-slides/
├── AGENTS.md                # authoring guide
├── build_presentation.py    # CLI orchestrator
├── slides.py                # pure functions: parse, collect, render
├── template.html            # HTML skeleton
├── runtime.js               # viewBox animation + navigation
├── runtime.css              # dark-theme chrome
├── tests/                   # unittest suite (no deps)
└── presentations/           # .dot sources + generated .svg/.html
```

## Keyboard & mouse

Linear decks:

| Key                              | Action          |
|----------------------------------|-----------------|
| `→` · `Space` · `↓` · `PgDn`     | next slide      |
| `←` · `↑` · `PgUp`               | previous slide  |
| `1`–`9`                          | jump to slide N |
| `Home` · `0` · `Esc`             | overview        |
| `End`                            | last slide      |
| `H`                              | hide overlay    |
| `F`                              | fullscreen      |
| click left / right half          | back / forward  |

Branched decks split spine and branch motion across the arrows:

| Key                              | Action                              |
|----------------------------------|-------------------------------------|
| `→` · `Space` · `PgDn`           | next spine slide                    |
| `←` · `PgUp`                     | previous spine slide                |
| `↓`                              | branch forward (DFS into sub-tree)  |
| `↑`                              | branch back (DFS reverse)           |
| `1`–`9`                          | jump to spine slide N               |
| `Home` · `0` · `Esc`             | overview                            |
| `End`                            | last slide                          |

See [AGENTS.md](./AGENTS.md#branched-dag-decks) for the branched
authoring conventions.

## How it validates itself — fail-fast

- `dot` exits non-zero → build aborts for that file (no stale HTML).
- `dot` runs with a 30-second timeout.
- Duplicate slide numbers → **build failure**.
- Non-contiguous slide numbers (`①, ②, ④`) → **build failure**.
- Missing top-level `label=` → note (title falls back to filename).
- Browser logs `presentation: N slides, M resolved, K missing` at load
  and shows an orange warning bar if any slide target's `<title>` is
  unresolved in the SVG.

## Tests

```sh
python3 -m unittest discover tests
```

Covers `parse_prefix`, `collect_slides`, `derive_title`, `render_html`,
and the lint helpers. No external dependencies (stdlib `unittest`).
