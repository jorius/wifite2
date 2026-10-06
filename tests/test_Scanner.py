#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '..')

import unittest
from unittest.mock import patch

from wifite.util.scanner import Scanner


class TestScanner(unittest.TestCase):
    def test_visible_targets_no_cap(self):
        targets = list(range(5))
        shown, hidden = Scanner._visible_targets(targets, None)
        assert shown == targets
        assert hidden == 0

    def test_visible_targets_under_cap(self):
        targets = list(range(5))
        shown, hidden = Scanner._visible_targets(targets, 10)
        assert shown == targets
        assert hidden == 0

    def test_visible_targets_over_cap(self):
        targets = list(range(50))
        shown, hidden = Scanner._visible_targets(targets, 20)
        assert shown == targets[:20]
        assert len(shown) == 20
        assert hidden == 30

    def test_max_display_targets_reserves_rows(self):
        with patch.object(Scanner, 'get_terminal_height', return_value=30):
            assert Scanner.max_display_targets() == 24  # 30 - 6 reserved

    def test_max_display_targets_minimum_one(self):
        # Tiny terminal still shows at least one row rather than zero/negative.
        with patch.object(Scanner, 'get_terminal_height', return_value=3):
            assert Scanner.max_display_targets() == 1

    def test_get_terminal_height_has_safe_fallback(self):
        # Must return a positive int even when the size can't be determined.
        assert isinstance(Scanner.get_terminal_height(), int)
        assert Scanner.get_terminal_height() > 0


if __name__ == '__main__':
    unittest.main()
