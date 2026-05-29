"""Pure functions for the dot-slides build pipeline.

No I/O, no subprocess, no sys.exit — everything in here takes strings/objects
and returns strings/objects (or raises SlideError on invalid input). The
orchestrator in build_presentation.py handles file reads, the `dot` call,
and exit codes; this module owns the *meaning* of the pipeline.

Two deck modes coexist:

* **Linear** — circled-digit prefix `①..⑳` on cluster/node labels. Slides
  form a flat ordered list. (The original mode; see `collect_slides`.)
* **Branched** — nodes carry `class="slide"`, edges carry `class="spine"`
  (top-level path) or `class="branch"` (sub-tree entry). Numbers like
  `1`, `1.1`, `1.1.2` are derived from the graph. (See
  `collect_branched_slides`.)

`is_branched_svg(svg_text)` picks the mode for a given file.
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from typing import Iterable

SVG_NS = "http://www.w3.org/2000/svg"
_SVG = f"{{{SVG_NS}}}"


class SlideError(Exception):
    """Raised when the slide set is structurally invalid (duplicate, non-contiguous)."""


# ─────────────────────────── slide model ───────────────────────────

@dataclass(frozen=True)
class Slide:
    n: int
    target: str  # SVG <title> text; the runtime resolves this to a <g>
    label: str   # human-readable, prefix kept


# ─────────────────────────── prefix parsing ───────────────────────────
#
# One notation, on purpose: circled digits ①..⑳. Any other shape (ASCII
# "1.", negative-circled, etc.) is silently ignored at scan time and will
# produce a "no numbered slides found" error if you used it everywhere.

_CIRCLED_1_20 = 0x2460  # ord('①')
PREFIX_RE = re.compile(r"^\s*([①-⑳])\s+")


def parse_prefix(text: str) -> int | None:
    """Return the slide number embedded as a circled-digit prefix, or None."""
    m = PREFIX_RE.match(text)
    if not m:
        return None
    return ord(m.group(1)) - _CIRCLED_1_20 + 1


# ─────────────────────────── SVG inspection ───────────────────────────

def _has_class(elem: ET.Element, name: str) -> bool:
    cls = elem.get("class") or ""
    return name in cls.split()


def _first_text_of_group(group: ET.Element) -> str | None:
    """First <text> directly painted by this group.

    "Directly painted" means: walk the group's descendants but stop at any
    nested <g class="cluster"|"node"> — those belong to a different slide.
    Graphviz normally emits clusters as flat siblings, but ignoring nested
    cluster/node groups keeps us correct against future format shifts.
    """
    for elem in _iter_own(group):
        if elem.tag == f"{_SVG}text":
            text = "".join(elem.itertext())
            return text.strip() if text else None
    return None


def _iter_own(group: ET.Element) -> Iterable[ET.Element]:
    """Depth-first descendants of `group`, skipping into nested cluster/node groups."""
    for child in group:
        if child.tag == f"{_SVG}g" and (
            _has_class(child, "cluster") or _has_class(child, "node")
        ):
            continue
        yield child
        yield from _iter_own(child)


def _group_target(group: ET.Element) -> str | None:
    """Graphviz emits <title>X</title> as the first child of every cluster/node group."""
    t = group.find(f"{_SVG}title")
    if t is None or t.text is None:
        return None
    return t.text.strip()


def collect_slides(svg_text: str) -> list[Slide]:
    """Find numbered cluster/node groups in the SVG and return them sorted by number.

    Raises SlideError if two groups share a slide number — duplicates are a
    structural authoring bug, not a recoverable warning.
    """
    root = ET.fromstring(svg_text)
    candidates: list[Slide] = []
    for g in root.iter(f"{_SVG}g"):
        if not (_has_class(g, "cluster") or _has_class(g, "node")):
            continue
        target = _group_target(g)
        if not target:
            continue
        first = _first_text_of_group(g)
        if first is None:
            continue
        n = parse_prefix(html.unescape(first))
        if n is None:
            continue
        candidates.append(Slide(n=n, target=target, label=html.unescape(first)))

    candidates.sort(key=lambda s: s.n)
    by_n: dict[int, Slide] = {}
    for s in candidates:
        if s.n in by_n:
            other = by_n[s.n]
            raise SlideError(
                f"duplicate slide number {s.n}: {other.target!r} and {s.target!r}"
            )
        by_n[s.n] = s
    return list(by_n.values())


def ensure_contiguous(slides: list[Slide]) -> None:
    """Raise SlideError if slide numbers have a gap. No-op for <2 slides."""
    if len(slides) < 2:
        return
    ns = sorted(s.n for s in slides)
    missing = [i for i in range(ns[0], ns[-1] + 1) if i not in set(ns)]
    if missing:
        raise SlideError(
            f"non-contiguous slide numbering, missing: {', '.join(str(m) for m in missing)}"
        )


# ─────────────────────────── DOT inspection ───────────────────────────

_DIGRAPH_LABEL_RE = re.compile(r"\blabel\s*=\s*\"([^\"]+)\"\s*;?")


def derive_title(dot_text: str, fallback: str) -> str:
    """Return the digraph's top-level `label=` value, or `fallback`.

    Only labels appearing *before* the first `subgraph` count — that prevents
    a cluster's label from being mistaken for the whole-page title.
    """
    head = dot_text.split("subgraph", 1)[0]
    m = _DIGRAPH_LABEL_RE.search(head)
    if m:
        return html.unescape(m.group(1))
    return fallback


# ─────────────────────────── HTML emission ───────────────────────────

_SVG_PREAMBLE_RES = (
    re.compile(r"<\?xml[^?]*\?>\s*"),
    re.compile(r"<!DOCTYPE[^>]*>\s*"),
    re.compile(r"<!--.*?-->", re.DOTALL),
)


def strip_svg_wrapper(svg_text: str) -> str:
    """Drop the <?xml?>, <!DOCTYPE>, and Graphviz comments so the SVG inlines cleanly."""
    for pat in _SVG_PREAMBLE_RES:
        svg_text = pat.sub("", svg_text)
    return svg_text.strip()


def slides_to_json(slides: list[Slide]) -> str:
    """Serialise linear slides as the runtime expects: bookended by Overview entries."""
    payload: list[dict] = [{"kind": "overview", "label": "Overview"}]
    payload += [{"kind": "linear", "target": s.target, "label": s.label} for s in slides]
    payload.append({"kind": "overview", "label": "Overview"})
    return json.dumps({"mode": "linear", "slides": payload}, ensure_ascii=False)


def render_html(
    template: str,
    svg_text: str,
    slides: list,
    page_title: str,
    runtime_prefix: str = "../",
) -> str:
    """Fill the HTML template. Placeholders are {{TOKEN}} strings.

    `slides` may be `list[Slide]` (linear deck) or `list[BranchedSlide]`
    (branched deck). The serialiser is picked by type; an empty list is
    treated as linear (matches the legacy behaviour).

    `runtime_prefix` is the relative path from the generated HTML back to the
    directory holding `runtime.{js,css}`. Each presentation lives in its own
    subdirectory (`presentations/<name>/<name>.html`), so the default is the
    two-level `../../` computed by the build for that depth.
    """
    if slides and isinstance(slides[0], BranchedSlide):
        slides_json = branched_slides_to_json(slides)
    else:
        slides_json = slides_to_json(slides)
    return (
        template
        .replace("{{TITLE_HTML}}", html.escape(page_title))
        .replace("{{TITLE_JSON}}", json.dumps(page_title, ensure_ascii=False))
        .replace("{{SLIDES_JSON}}", slides_json)
        .replace("{{SVG}}", strip_svg_wrapper(svg_text))
        .replace("{{RUNTIME_PREFIX}}", runtime_prefix)
    )


# ─────────────────────────── branched (DAG) decks ───────────────────────────
#
# Slide-eligible groups: `class="slide"` (Graphviz appends to its own
# "node"/"cluster" class, so SVG ends up as `class="node slide"` etc.).
# Edge classes:
#   "spine"  — connects consecutive top-level slides (the spine `1 → 2 → 3`).
#   "branch" — connects a parent slide to one of its branch children. Spine
#              nodes can sprout branches; branches can nest further.
# Numbers are derived: spine = "1", "2", …; child #k of node N = "N.k"; etc.
# Slides are emitted in render order: each spine node followed by a DFS of
# its branch sub-tree.

@dataclass(frozen=True)
class BranchedSlide:
    target: str               # SVG <title> for the group
    label: str                # raw label text (no derived number)
    number: str               # derived, e.g. "1.1.2"
    is_spine: bool
    spine_prev: str | None    # target of previous spine slide, or None
    spine_next: str | None    # target of next spine slide, or None
    branch_prev: str | None   # previous in DFS chain (head=spine slide → None)
    branch_next: str | None   # next in DFS chain, or None at tail


def is_branched_svg(svg_text: str) -> bool:
    """True iff the SVG has at least one `class="slide"` group.

    Cheap mode detector used by build_presentation.py. Does not validate
    structure; just decides which parser to invoke.
    """
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return False
    for g in root.iter(f"{_SVG}g"):
        if _has_class(g, "slide"):
            return True
    return False


def _collect_slide_groups(root: ET.Element) -> dict[str, str]:
    """Map each `class="slide"` group's <title> to its first <text> label."""
    out: dict[str, str] = {}
    for g in root.iter(f"{_SVG}g"):
        if not _has_class(g, "slide"):
            continue
        target = _group_target(g)
        if not target:
            continue
        if target in out:
            raise SlideError(f"duplicate slide target {target!r}")
        label = _first_text_of_group(g) or ""
        out[target] = html.unescape(label)
    return out


def _collect_branched_edges(
    root: ET.Element,
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Return (spine_out, branch_out) keyed by source target.

    `spine_out[src] = tgt` — at most one spine successor per node.
    `branch_out[src] = [tgt, …]` — branch children in source order.

    Raises if a node has two outgoing spine edges (ambiguous spine).
    """
    spine_out: dict[str, str] = {}
    branch_out: dict[str, list[str]] = {}
    for g in root.iter(f"{_SVG}g"):
        if not _has_class(g, "edge"):
            continue
        title = _group_target(g)
        if not title or "->" not in title:
            continue
        src, _, tgt = title.partition("->")
        src, tgt = src.strip(), tgt.strip()
        if _has_class(g, "spine"):
            if src in spine_out:
                raise SlideError(
                    f"node {src!r} has multiple spine successors "
                    f"({spine_out[src]!r}, {tgt!r}); the spine must be a single chain"
                )
            spine_out[src] = tgt
        elif _has_class(g, "branch"):
            branch_out.setdefault(src, []).append(tgt)
    return spine_out, branch_out


def _walk_spine(
    start: str,
    spine_out: dict[str, str],
    slides_by_target: dict[str, str],
) -> list[str]:
    """Follow spine edges from `start` until exhaustion. Detects cycles."""
    spine = [start]
    seen = {start}
    while spine[-1] in spine_out:
        nxt = spine_out[spine[-1]]
        if nxt in seen:
            raise SlideError(f"spine cycle detected at {nxt!r}")
        if nxt not in slides_by_target:
            raise SlideError(
                f"spine edge {spine[-1]!r} -> {nxt!r} targets non-slide node"
            )
        spine.append(nxt)
        seen.add(nxt)
    return spine


def collect_branched_slides(svg_text: str) -> list[BranchedSlide]:
    """Parse a branched-mode SVG into a flat slide list in render order.

    Render order = spine node 1, all of its branch sub-tree in DFS, spine
    node 2, its sub-tree, … This is also the order ↓/↑ traverse within a
    spine subtree.
    """
    root = ET.fromstring(svg_text)
    slides_by_target = _collect_slide_groups(root)
    if not slides_by_target:
        raise SlideError(
            'branched mode: no `class="slide"` groups found in SVG'
        )

    spine_out, branch_out = _collect_branched_edges(root)

    # Edge endpoints must all be slide-eligible.
    for src, tgt in spine_out.items():
        if src not in slides_by_target:
            raise SlideError(f"spine edge from non-slide {src!r}")
        if tgt not in slides_by_target:
            raise SlideError(f"spine edge to non-slide {tgt!r}")
    for src, tgts in branch_out.items():
        if src not in slides_by_target:
            raise SlideError(f"branch edge from non-slide {src!r}")
        for tgt in tgts:
            if tgt not in slides_by_target:
                raise SlideError(f"branch edge to non-slide {tgt!r}")

    # The root is the unique slide with no incoming spine OR branch edge.
    incoming: set[str] = set(spine_out.values())
    for tgts in branch_out.values():
        incoming.update(tgts)
    roots = sorted(t for t in slides_by_target if t not in incoming)
    if not roots:
        raise SlideError(
            "no root slide: every slide has an incoming edge (cycle?)"
        )
    if len(roots) > 1:
        raise SlideError(
            f"multiple root slides {roots!r}; exactly one slide must have "
            "no incoming spine/branch edge"
        )
    start = roots[0]

    spine = _walk_spine(start, spine_out, slides_by_target)
    spine_set = set(spine)

    # Spine edges may only originate from spine nodes.
    for src in spine_out:
        if src not in spine_set:
            raise SlideError(
                f"spine edge originates from non-spine node {src!r}; "
                "branches cannot have spine edges"
            )

    # Build slides in render order with numbering derived from the walk.
    visited: set[str] = set(spine_set)
    ordered: list[BranchedSlide] = []
    chain_by_anchor: dict[str, list[str]] = {}  # spine target → DFS chain (head=spine)

    for i, spine_target in enumerate(spine, start=1):
        spine_prev = spine[i - 2] if i >= 2 else None
        spine_next = spine[i] if i < len(spine) else None
        chain = [spine_target]
        chain_by_anchor[spine_target] = chain
        ordered.append(BranchedSlide(
            target=spine_target,
            label=slides_by_target[spine_target],
            number=str(i),
            is_spine=True,
            spine_prev=spine_prev,
            spine_next=spine_next,
            branch_prev=None,    # filled below as chain head
            branch_next=None,
        ))

        def walk(parent: str, parent_number: str) -> None:
            for k, child in enumerate(branch_out.get(parent, []), start=1):
                if child in visited:
                    raise SlideError(
                        f"branch cycle or diamond: {child!r} reached more than once"
                    )
                visited.add(child)
                child_number = f"{parent_number}.{k}"
                ordered.append(BranchedSlide(
                    target=child,
                    label=slides_by_target[child],
                    number=child_number,
                    is_spine=False,
                    spine_prev=None,
                    spine_next=None,
                    branch_prev=None,
                    branch_next=None,
                ))
                chain.append(child)
                walk(child, child_number)

        walk(spine_target, str(i))

    unreachable = set(slides_by_target) - visited
    if unreachable:
        raise SlideError(
            f"unreachable slides: {sorted(unreachable)!r}; every slide must "
            "be reachable from the root via spine/branch edges"
        )

    # Wire branch_prev/branch_next from per-anchor DFS chains, then merge
    # back into the render-ordered list.
    by_target: dict[str, BranchedSlide] = {s.target: s for s in ordered}
    for chain in chain_by_anchor.values():
        for i, t in enumerate(chain):
            bp = chain[i - 1] if i > 0 else None
            bn = chain[i + 1] if i + 1 < len(chain) else None
            by_target[t] = replace(by_target[t], branch_prev=bp, branch_next=bn)

    return [by_target[s.target] for s in ordered]


def branched_slides_to_json(slides: list[BranchedSlide]) -> str:
    """Serialise branched slides for the runtime.

    Wraps `{mode: "branched", slides: [...]}` so the runtime can pick its
    code path. Overview bookends carry `spineNext`/`spinePrev` so → / ←
    flow naturally from the overview into the spine.
    """
    if not slides:
        return json.dumps(
            {"mode": "branched", "slides": []}, ensure_ascii=False
        )

    # Resolve target → array index. Slides occupy indices 1..N (index 0 =
    # first overview, index N+1 = last overview).
    idx_by_target = {s.target: i + 1 for i, s in enumerate(slides)}

    def idx(target: str | None) -> int | None:
        return idx_by_target[target] if target is not None else None

    first_spine_idx = next(
        (i + 1 for i, s in enumerate(slides) if s.is_spine), None
    )
    last_spine_idx = next(
        (len(slides) - i for i, s in enumerate(reversed(slides)) if s.is_spine),
        None,
    )

    payload: list[dict] = [{
        "kind": "overview",
        "label": "Overview",
        "spinePrev": None,
        "spineNext": first_spine_idx,
        "branchPrev": None,
        "branchNext": None,
    }]

    overview_first_idx = 0
    overview_last_idx = len(slides) + 1

    for s in slides:
        payload.append({
            "kind": "spine" if s.is_spine else "branch",
            "target": s.target,
            "label": f"{s.number}. {s.label}" if s.label else s.number,
            "number": s.number,
            "spinePrev": (
                idx(s.spine_prev)
                if s.is_spine and s.spine_prev is not None
                else (overview_first_idx if s.is_spine else None)
            ),
            "spineNext": (
                idx(s.spine_next)
                if s.is_spine and s.spine_next is not None
                else (overview_last_idx if s.is_spine else None)
            ),
            "branchPrev": idx(s.branch_prev),
            "branchNext": idx(s.branch_next),
        })

    payload.append({
        "kind": "overview",
        "label": "Overview",
        "spinePrev": last_spine_idx,
        "spineNext": None,
        "branchPrev": None,
        "branchNext": None,
    })

    return json.dumps(
        {"mode": "branched", "slides": payload}, ensure_ascii=False
    )


