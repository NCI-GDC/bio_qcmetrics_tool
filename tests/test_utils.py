"""Tests for the `bio_qcmetrics_tool.utils.parse` module."""
import unittest

from bio_qcmetrics_tool.utils.parse import parse_type


class TestUtils(unittest.TestCase):
    def test_parse_type(self):
        val = parse_type(None)
        self.assertIsNone(val)

        val = parse_type(None, na="NA")
        self.assertEqual(val, "NA")

        val = parse_type("1.3")
        self.assertEqual(float("1.3"), val)

        val = parse_type("1")
        self.assertEqual(int("1"), val)

        val = parse_type("abc")
        self.assertEqual("abc", val)
