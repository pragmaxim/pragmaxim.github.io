"""parse_prefix is the smallest unit of meaning in the build pipeline.

Only circled digits ①..⑳ are accepted — every other shape is silently
ignored at scan time. If it gets a slide number right, the rest of the
system is mostly orchestration.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from slides import parse_prefix  # noqa: E402


class TestParsePrefix(unittest.TestCase):

    # ── Accepted: circled digits ──────────────────────────────────────
    def test_circled_one(self):    self.assertEqual(parse_prefix("① Step"), 1)
    def test_circled_two(self):    self.assertEqual(parse_prefix("② Step"), 2)
    def test_circled_ten(self):    self.assertEqual(parse_prefix("⑩ Tenth"), 10)
    def test_circled_eleven(self): self.assertEqual(parse_prefix("⑪ Eleventh"), 11)
    def test_circled_twenty(self): self.assertEqual(parse_prefix("⑳ Twentieth"), 20)

    # ── Whitespace ─────────────────────────────────────────────────────
    def test_leading_whitespace(self): self.assertEqual(parse_prefix("   ① Indented"), 1)

    # ── Rejected forms ─────────────────────────────────────────────────
    def test_no_prefix(self):
        self.assertIsNone(parse_prefix("No number here"))

    def test_prefix_mid_string(self):
        self.assertIsNone(parse_prefix("Step ① something"))

    def test_circled_without_trailing_space(self):
        self.assertIsNone(parse_prefix("①Step"))

    def test_ascii_dot_rejected(self):
        # ASCII "1. " is intentionally NOT accepted — one notation only.
        self.assertIsNone(parse_prefix("1. Hello"))

    def test_ascii_paren_rejected(self):
        self.assertIsNone(parse_prefix("2) Hello"))

    def test_negative_circled_rejected(self):
        # ⓫..⓴ is no longer accepted; use ⑪..⑳ instead.
        self.assertIsNone(parse_prefix("⓫ Eleventh"))

    def test_empty(self):
        self.assertIsNone(parse_prefix(""))


if __name__ == "__main__":
    unittest.main()
