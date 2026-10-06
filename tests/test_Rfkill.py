#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '..')

from wifite.tools.rfkill import Rfkill

import unittest


class TestRfkill(unittest.TestCase):
    def test_parse_soft_blocked(self):
        out = '''0: hci0: Bluetooth
\tSoft blocked: no
\tHard blocked: no
1: phy0: Wireless LAN
\tSoft blocked: yes
\tHard blocked: no
'''
        blocks = Rfkill._parse_blocks(out)
        assert blocks == {'soft': True, 'hard': False}, blocks

    def test_parse_hard_blocked(self):
        out = '''1: phy0: Wireless LAN
\tSoft blocked: no
\tHard blocked: yes
'''
        blocks = Rfkill._parse_blocks(out)
        assert blocks == {'soft': False, 'hard': True}, blocks

    def test_parse_unblocked(self):
        out = '''1: phy0: Wireless LAN
\tSoft blocked: no
\tHard blocked: no
'''
        blocks = Rfkill._parse_blocks(out)
        assert blocks == {'soft': False, 'hard': False}, blocks

    def test_parse_ignores_non_wifi(self):
        # A soft-blocked Bluetooth device must not count as a wifi block.
        out = '''0: hci0: Bluetooth
\tSoft blocked: yes
\tHard blocked: no
'''
        blocks = Rfkill._parse_blocks(out)
        assert blocks == {'soft': False, 'hard': False}, blocks


if __name__ == '__main__':
    unittest.main()
