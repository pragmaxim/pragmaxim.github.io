"""Branched-deck parsing: collect_branched_slides + branched_slides_to_json."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from slides import (  # noqa: E402
    BranchedSlide,
    SlideError,
    branched_slides_to_json,
    collect_branched_slides,
    is_branched_svg,
)


# ─── SVG fixtures ────────────────────────────────────────────────────────
# Minimal hand-rolled SVGs that mimic what Graphviz emits for branched
# decks. Real builds run `dot -Tsvg`; here we skip the renderer.

_NS = 'xmlns="http://www.w3.org/2000/svg"'


def _svg(*groups: str) -> str:
    return (
        f'<svg {_NS} viewBox="0 0 100 100">'
        + "".join(groups)
        + "</svg>"
    )


def _node(target: str, label: str = "", extra_classes: str = "") -> str:
    classes = ("node " + extra_classes).strip()
    return (
        f'<g class="{classes}">'
        f'<title>{target}</title>'
        f'<text>{label}</text>'
        f'</g>'
    )


def _edge(src: str, tgt: str, extra_classes: str = "") -> str:
    classes = ("edge " + extra_classes).strip()
    return f'<g class="{classes}"><title>{src}-&gt;{tgt}</title></g>'


# Tree under test (matches the example in the design spec):
#   1 ── 2 ── 3 ── 4         (spine)
#   ├── 1.1 ── 1.1.1
#   │       ── 1.1.2
#   └── 1.2
def _example_branched_svg() -> str:
    return _svg(
        # Slide nodes
        _node("N1", "Intro", "slide"),
        _node("N11", "First branch", "slide"),
        _node("N111", "Deep one", "slide"),
        _node("N112", "Deep two", "slide"),
        _node("N12", "Second branch", "slide"),
        _node("N2", "Second", "slide"),
        _node("N3", "Third", "slide"),
        _node("N4", "Fourth", "slide"),
        # Spine
        _edge("N1", "N2", "spine"),
        _edge("N2", "N3", "spine"),
        _edge("N3", "N4", "spine"),
        # Branches off N1
        _edge("N1", "N11", "branch"),
        _edge("N1", "N12", "branch"),
        # Sub-branches off N11
        _edge("N11", "N111", "branch"),
        _edge("N11", "N112", "branch"),
    )


# ─── Tests ───────────────────────────────────────────────────────────────


class TestIsBranchedSvg(unittest.TestCase):

    def test_detects_class_slide(self):
        svg = _svg(_node("A", "x", "slide"))
        self.assertTrue(is_branched_svg(svg))

    def test_returns_false_for_linear(self):
        svg = _svg(_node("A", "① x"))
        self.assertFalse(is_branched_svg(svg))

    def test_returns_false_on_unparseable(self):
        self.assertFalse(is_branched_svg("not xml"))


class TestCollectBranchedSlides(unittest.TestCase):

    def test_numbering_and_order(self):
        slides = collect_branched_slides(_example_branched_svg())
        # Render order: spine, then DFS of branches per spine node
        numbers_by_target = {s.target: s.number for s in slides}
        self.assertEqual(numbers_by_target["N1"], "1")
        self.assertEqual(numbers_by_target["N11"], "1.1")
        self.assertEqual(numbers_by_target["N111"], "1.1.1")
        self.assertEqual(numbers_by_target["N112"], "1.1.2")
        self.assertEqual(numbers_by_target["N12"], "1.2")
        self.assertEqual(numbers_by_target["N2"], "2")
        self.assertEqual(numbers_by_target["N3"], "3")
        self.assertEqual(numbers_by_target["N4"], "4")

    def test_render_order(self):
        slides = collect_branched_slides(_example_branched_svg())
        self.assertEqual(
            [s.target for s in slides],
            ["N1", "N11", "N111", "N112", "N12", "N2", "N3", "N4"],
        )

    def test_spine_links(self):
        slides = collect_branched_slides(_example_branched_svg())
        by = {s.target: s for s in slides}
        self.assertEqual(by["N1"].spine_prev, None)
        self.assertEqual(by["N1"].spine_next, "N2")
        self.assertEqual(by["N2"].spine_prev, "N1")
        self.assertEqual(by["N2"].spine_next, "N3")
        self.assertEqual(by["N4"].spine_next, None)

    def test_branch_chain_for_n1(self):
        slides = collect_branched_slides(_example_branched_svg())
        by = {s.target: s for s in slides}
        # DFS chain rooted at N1: N1 → N11 → N111 → N112 → N12
        self.assertEqual(by["N1"].branch_prev, None)
        self.assertEqual(by["N1"].branch_next, "N11")
        self.assertEqual(by["N11"].branch_prev, "N1")
        self.assertEqual(by["N11"].branch_next, "N111")
        self.assertEqual(by["N111"].branch_prev, "N11")
        self.assertEqual(by["N111"].branch_next, "N112")
        self.assertEqual(by["N112"].branch_prev, "N111")
        self.assertEqual(by["N112"].branch_next, "N12")
        self.assertEqual(by["N12"].branch_prev, "N112")
        self.assertEqual(by["N12"].branch_next, None)

    def test_spine_node_without_branches(self):
        slides = collect_branched_slides(_example_branched_svg())
        by = {s.target: s for s in slides}
        # N2/N3/N4 have no branches → chain is just themselves
        for t in ("N2", "N3", "N4"):
            self.assertIsNone(by[t].branch_prev)
            self.assertIsNone(by[t].branch_next)

    def test_is_spine_flag(self):
        slides = collect_branched_slides(_example_branched_svg())
        spine = [s.target for s in slides if s.is_spine]
        branches = [s.target for s in slides if not s.is_spine]
        self.assertEqual(spine, ["N1", "N2", "N3", "N4"])
        self.assertEqual(sorted(branches), ["N11", "N111", "N112", "N12"])


class TestErrors(unittest.TestCase):

    def test_no_slide_groups(self):
        svg = _svg(_node("A"))  # no class="slide"
        with self.assertRaises(SlideError):
            collect_branched_slides(svg)

    def test_multiple_roots(self):
        svg = _svg(
            _node("A", "", "slide"),
            _node("B", "", "slide"),
            # No edges → both A and B are roots
        )
        with self.assertRaises(SlideError) as cm:
            collect_branched_slides(svg)
        self.assertIn("multiple root", str(cm.exception))

    def test_spine_branching(self):
        svg = _svg(
            _node("A", "", "slide"),
            _node("B", "", "slide"),
            _node("C", "", "slide"),
            _edge("A", "B", "spine"),
            _edge("A", "C", "spine"),  # ambiguous spine
        )
        with self.assertRaises(SlideError) as cm:
            collect_branched_slides(svg)
        self.assertIn("multiple spine successors", str(cm.exception))

    def test_dangling_edge(self):
        svg = _svg(
            _node("A", "", "slide"),
            _edge("A", "GHOST", "branch"),
        )
        with self.assertRaises(SlideError):
            collect_branched_slides(svg)

    def test_unreachable_slide(self):
        # B exists but is not connected by spine or branch edges from A
        svg = _svg(
            _node("A", "", "slide"),
            _node("B", "", "slide"),
            _node("C", "", "slide"),
            _edge("A", "C", "spine"),
            # B is dangling — multiple roots, will fail
        )
        with self.assertRaises(SlideError):
            collect_branched_slides(svg)

    def test_branch_with_spine_edge_inside(self):
        # Branch nodes are not allowed to have spine edges
        svg = _svg(
            _node("A", "", "slide"),
            _node("X", "", "slide"),
            _node("Y", "", "slide"),
            _edge("A", "X", "branch"),
            _edge("X", "Y", "spine"),  # X is a branch node, can't sprout spine
        )
        with self.assertRaises(SlideError):
            collect_branched_slides(svg)


class TestBranchedJson(unittest.TestCase):

    def test_wrapper_and_bookends(self):
        slides = collect_branched_slides(_example_branched_svg())
        wrap = json.loads(branched_slides_to_json(slides))
        self.assertEqual(wrap["mode"], "branched")
        payload = wrap["slides"]
        self.assertEqual(payload[0]["kind"], "overview")
        self.assertEqual(payload[-1]["kind"], "overview")
        self.assertEqual(len(payload), len(slides) + 2)

    def test_index_pointers(self):
        slides = collect_branched_slides(_example_branched_svg())
        wrap = json.loads(branched_slides_to_json(slides))
        payload = wrap["slides"]

        # Slide indices in the payload (1-based after overview at index 0):
        #   1 → N1, 2 → N11, 3 → N111, 4 → N112, 5 → N12, 6 → N2, 7 → N3, 8 → N4
        idx = {entry["target"]: i for i, entry in enumerate(payload)
               if entry["kind"] != "overview"}

        # N1 → next spine N2 (index 6)
        self.assertEqual(payload[idx["N1"]]["spineNext"], idx["N2"])
        self.assertEqual(payload[idx["N1"]]["branchNext"], idx["N11"])
        # N111 ↓ to N112
        self.assertEqual(payload[idx["N111"]]["branchNext"], idx["N112"])
        # N112 ↑ to N111
        self.assertEqual(payload[idx["N112"]]["branchPrev"], idx["N111"])
        # First spine slide's spinePrev should point at the first overview (0)
        self.assertEqual(payload[idx["N1"]]["spinePrev"], 0)
        # Last spine slide's spineNext should point at the last overview
        self.assertEqual(payload[idx["N4"]]["spineNext"], len(payload) - 1)

    def test_labels_get_derived_number(self):
        slides = collect_branched_slides(_example_branched_svg())
        wrap = json.loads(branched_slides_to_json(slides))
        labels = {e["target"]: e["label"] for e in wrap["slides"]
                  if e["kind"] != "overview"}
        self.assertEqual(labels["N1"], "1. Intro")
        self.assertEqual(labels["N111"], "1.1.1. Deep one")
        self.assertEqual(labels["N4"], "4. Fourth")


if __name__ == "__main__":
    unittest.main()
