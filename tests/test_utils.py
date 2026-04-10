from __future__ import annotations

from utils import dedupe


class TestDedupe:
    def test_removes_duplicates(self):
        assert dedupe(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_preserves_insertion_order(self):
        assert dedupe(["c", "a", "b"]) == ["c", "a", "b"]

    def test_removes_blank_strings(self):
        assert dedupe(["a", "", "  ", "b"]) == ["a", "b"]

    def test_strips_whitespace_before_comparing(self):
        assert dedupe(["  a  ", "a"]) == ["a"]

    def test_empty_input(self):
        assert dedupe([]) == []

    def test_all_duplicates(self):
        assert dedupe(["x", "x", "x"]) == ["x"]
