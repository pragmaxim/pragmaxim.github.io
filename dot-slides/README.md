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
| `Z`                              | zoom out to whole deck (toggle) |
| `Home` · `0` · `Esc`             | overview        |
| `End`                            | last slide      |
| `H`                              | hide overlay    |
| `F`                              | fullscreen      |
| click left / right half          | back / forward  |

Branched (DAG) decks split spine and branch motion across the arrows —
`→`/`←` walk the spine, `↓`/`↑` walk into and back out of a branch. The
full key table and authoring conventions live in
[AGENTS.md](./AGENTS.md#branched-dag-decks).

## How it validates itself — fail-fast

The build aborts a file rather than emit stale HTML — `dot` errors,
duplicate or non-contiguous slide numbers, and the like are all build
failures. See [AGENTS.md](./AGENTS.md#build-invariants--fail-fast) for the
full contract.

At runtime the browser logs `presentation: N slides, M resolved, K missing`
at load and shows an orange warning bar if any slide target's `<title>` is
unresolved in the SVG.

## Tests

```sh
python3 -m unittest discover tests
```

Covers `parse_prefix`, `collect_slides`, `derive_title`, `render_html`,
and the lint helpers. No external dependencies (stdlib `unittest`).
