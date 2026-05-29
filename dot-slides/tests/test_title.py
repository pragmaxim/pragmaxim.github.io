"""derive_title pulls the digraph's top-level label= — and ONLY the top-level one.

A cluster's label= must not be mistaken for the whole-page title.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from slides import derive_title  # noqa: E402


class TestDeriveTitle(unittest.TestCase):

    def test_top_level_label_wins(self):
        dot = 'digraph X { label="My Title"; subgraph c { label="Cluster A"; } }'
        self.assertEqual(derive_title(dot, fallback="x"), "My Title")

    def test_label_inside_subgraph_ignored(self):
        # No top-level label= before the first subgraph — fallback should win.
        dot = 'digraph X { rankdir=TD; subgraph c { label="Cluster A"; } }'
        self.assertEqual(derive_title(dot, fallback="fallback"), "fallback")

    def test_label_with_escaped_entities(self):
        dot = 'digraph X { label="A &amp; B"; subgraph c { } }'
        self.assertEqual(derive_title(dot, fallback="x"), "A & B")

    def test_no_label_anywhere(self):
        dot = 'digraph X { rankdir=TD; A -> B; }'
        self.assertEqual(derive_title(dot, fallback="My Fallback"), "My Fallback")

    def test_label_with_semicolon(self):
        dot = 'digraph X { label="Hello"; A -> B; }'
        self.assertEqual(derive_title(dot, fallback="x"), "Hello")


if __name__ == "__main__":
    unittest.main()
