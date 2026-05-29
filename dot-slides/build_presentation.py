#!/usr/bin/env python3
"""dot-slides build pipeline — orchestrator.

For each DOT file:
  1. Re-render the SVG with `dot -Tsvg`.
  2. Scan the SVG for numbered cluster/node groups.
  3. Emit <name>.html that loads the shared runtime.{js,css} from `..`.

All parsing/templating lives in slides.py; this file only does I/O and
diagnostics.

Usage:
    python3 build_presentation.py                                # all presentations/*/*.dot
    python3 build_presentation.py presentations/foo/foo.dot ...  # specific files
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import slides as S

HERE = Path(__file__).resolve().parent
PRESENTATIONS = HERE / "presentations"
TEMPLATE_PATH = HERE / "template.html"
DOT_TIMEOUT_SECONDS = 30


def _discover_dots(args: list[str]) -> list[Path]:
    if args:
        return [Path(a).resolve() for a in args]
    if not PRESENTATIONS.is_dir():
        sys.exit(f"no presentations/ directory at {PRESENTATIONS}")
    # Each presentation lives in its own subdirectory:
    # presentations/<name>/<name>.dot (+ generated .svg/.html, optional img/).
    dots = sorted(PRESENTATIONS.glob("*/*.dot"))
    if not dots:
        sys.exit(f"no */*.dot files in {PRESENTATIONS}")
    return dots


def _render_svg(dot_path: Path) -> Path:
    svg_path = dot_path.with_suffix(".svg")
    # Run `dot` with CWD = the .dot file's directory so that relative IMG
    # references like `img/foo.png` resolve to siblings of the .dot file
    # (e.g. `presentations/foo/img/foo.png`). That same relative path is then
    # carried verbatim into the SVG, where the runtime resolves it relative
    # to the HTML at `presentations/foo/foo.html` — same location, same path.
    try:
        result = subprocess.run(
            ["dot", "-Tsvg", dot_path.name, "-o", svg_path.name],
            cwd=dot_path.parent,
            timeout=DOT_TIMEOUT_SECONDS,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        if not svg_path.exists():
            sys.exit("error: `dot` not installed and no pre-built SVG to fall back on")
        print(f"  warning: `dot` not installed; using existing {svg_path.name}")
        return svg_path
    except subprocess.TimeoutExpired:
        sys.exit(f"error: `dot` timed out after {DOT_TIMEOUT_SECONDS}s on {dot_path.name}")

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n",
                  file=sys.stderr)
        sys.exit(f"error: `dot` exited {result.returncode} on {dot_path.name}")
    return svg_path


def _note(msg: str) -> None:
    """Informational diagnostic; printed to stdout so order matches execution."""
    print(f"  {msg}")


def _build_one(dot_path: Path, template: str) -> int:
    rel = dot_path.relative_to(HERE) if dot_path.is_relative_to(HERE) else dot_path
    print(f"▸ {rel}")
    if not dot_path.exists():
        _note("ERROR: file not found")
        return 1

    svg_path = _render_svg(dot_path)
    svg_text = svg_path.read_text()
    dot_text = dot_path.read_text()

    branched = S.is_branched_svg(svg_text)
    try:
        slides = (
            S.collect_branched_slides(svg_text) if branched
            else S.collect_slides(svg_text)
        )
    except S.SlideError as e:
        _note(f"ERROR: {e}")
        return 1

    if not slides:
        if branched:
            _note('ERROR: no class="slide" groups parsed in branched deck.')
        else:
            _note("ERROR: no numbered slides found. "
                  "Prefix a cluster/node label with a circled digit ①..⑳.")
        return 1

    if not branched:
        try:
            S.ensure_contiguous(slides)
        except S.SlideError as e:
            _note(f"ERROR: {e}")
            return 1

    fallback_title = dot_path.stem.replace("-", " ").replace("_", " ").title()
    page_title = S.derive_title(dot_text, fallback=fallback_title)
    if page_title == fallback_title:
        _note(f"note: no top-level label= found; using filename-derived title {page_title!r}")

    if branched:
        _note(f"branched mode: {len(slides)} slide(s)")
        for s in slides:
            kind = "spine " if s.is_spine else "branch"
            print(f"    ✓ {s.number:<8} {kind}  {s.target:<22} {s.label}")
    else:
        for s in slides:
            print(f"    ✓ {s.n:>2}. {s.target:<22} {s.label}")

    # Relative path from the generated HTML back to runtime.{js,css}, which
    # live at the dot-slides root. For presentations/<name>/<name>.html that
    # is two levels up; computed from depth so nesting stays correct.
    if dot_path.parent.is_relative_to(HERE):
        depth = len(dot_path.parent.relative_to(HERE).parts)
        runtime_prefix = "../" * depth if depth else "./"
    else:
        runtime_prefix = "../"

    html_path = dot_path.with_suffix(".html")
    html_path.write_text(
        S.render_html(template, svg_text, slides, page_title, runtime_prefix)
    )
    print(
        f"  → {svg_path.name} ({svg_path.stat().st_size} bytes), "
        f"{html_path.name} ({html_path.stat().st_size} bytes)"
    )
    return 0


def main(argv: list[str]) -> int:
    template = TEMPLATE_PATH.read_text()
    dots = _discover_dots(argv[1:])
    failures = 0
    for d in dots:
        failures += _build_one(d, template)
        print()
    if failures:
        print(f"{failures} file(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
