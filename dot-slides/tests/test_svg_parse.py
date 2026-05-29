"""collect_slides must:
  - find every cluster/node group with a numbered first <text>
  - sort by number, deduplicate, warn on dupes
  - NOT mistake later <text> children (like ordered-list rows) for slide markers
  - skip non-numbered groups silently
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from slides import Slide, SlideError, collect_slides, ensure_contiguous  # noqa: E402


def svg(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        + body
        + "</svg>"
    )


CLUSTER_AND_NODES = svg("""
  <g id="clust1" class="cluster">
    <title>cluster_a</title>
    <text>② Second slide</text>
  </g>
  <g id="node1" class="node">
    <title>NodeA</title>
    <text>① First slide</text>
    <text>Inner content row — no circled digit, so not a slide candidate</text>
  </g>
  <g id="node2" class="node">
    <title>NodeB</title>
    <text>Not numbered, ignored</text>
  </g>
  <g id="edge1" class="edge">
    <title>NodeA-&gt;NodeB</title>
    <text>③ edges-class groups are ignored entirely</text>
  </g>
""")


DUPLICATE_NUMBERS = svg("""
  <g id="n1" class="node"><title>A</title><text>① first</text></g>
  <g id="n2" class="node"><title>B</title><text>① duplicate</text></g>
""")


NESTED_GROUP_WRAPPER = svg("""
  <g id="n1" class="node">
    <title>Wrapped</title>
    <g transform="translate(10,10)">
      <text>③ Inside a transform-only wrapper</text>
    </g>
  </g>
""")


NESTED_CLUSTER_INSIDE_CLUSTER = svg("""
  <g id="outer" class="cluster">
    <title>cluster_outer</title>
    <text>④ Outer cluster label</text>
    <g id="inner" class="cluster">
      <title>cluster_inner</title>
      <text>⑤ Inner cluster label</text>
    </g>
  </g>
""")


class TestCollectSlides(unittest.TestCase):

    def test_sorted_and_first_text_only(self):
        slides = collect_slides(CLUSTER_AND_NODES)
        self.assertEqual(
            slides,
            [
                Slide(n=1, target="NodeA", label="① First slide"),
                Slide(n=2, target="cluster_a", label="② Second slide"),
            ],
        )

    def test_edges_are_ignored(self):
        slides = collect_slides(CLUSTER_AND_NODES)
        self.assertNotIn(3, [s.n for s in slides])

    def test_duplicates_raise(self):
        with self.assertRaises(SlideError) as ctx:
            collect_slides(DUPLICATE_NUMBERS)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_transform_wrapper_does_not_hide_text(self):
        slides = collect_slides(NESTED_GROUP_WRAPPER)
        self.assertEqual(
            slides,
            [Slide(n=3, target="Wrapped", label="③ Inside a transform-only wrapper")],
        )

    def test_nested_cluster_does_not_shadow_outer(self):
        # Graphviz emits clusters as flat siblings, but defensively we ignore nested
        # cluster/node groups when scanning the outer group's own <text> children.
        slides = collect_slides(NESTED_CLUSTER_INSIDE_CLUSTER)
        labels = {s.n: s.label for s in slides}
        self.assertEqual(labels[4], "④ Outer cluster label")
        self.assertEqual(labels[5], "⑤ Inner cluster label")

    def test_html_entities_unescaped_in_label(self):
        s = collect_slides(svg(
            '<g id="n1" class="node"><title>A</title>'
            '<text>① A &amp; B</text></g>'
        ))
        self.assertEqual(s, [Slide(n=1, target="A", label="① A & B")])

    def test_empty_svg(self):
        self.assertEqual(collect_slides(svg("")), [])

    def test_only_non_numbered(self):
        self.assertEqual(
            collect_slides(svg(
                '<g id="n1" class="node"><title>A</title><text>plain</text></g>'
            )),
            [],
        )


class TestEnsureContiguous(unittest.TestCase):

    def test_contiguous_ok(self):
        ensure_contiguous([Slide(1, "A", "a"), Slide(2, "B", "b"), Slide(3, "C", "c")])

    def test_single_slide_ok(self):
        ensure_contiguous([Slide(7, "A", "a")])

    def test_empty_ok(self):
        ensure_contiguous([])

    def test_gap_raises(self):
        with self.assertRaises(SlideError) as ctx:
            ensure_contiguous([Slide(1, "A", "a"), Slide(3, "B", "b")])
        self.assertIn("missing: 2", str(ctx.exception))

    def test_multiple_gaps(self):
        with self.assertRaises(SlideError) as ctx:
            ensure_contiguous([Slide(1, "A", "a"), Slide(5, "B", "b")])
        self.assertIn("2, 3, 4", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
