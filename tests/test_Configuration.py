#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '..')

import unittest
from unittest.mock import patch

from wifite.config import Configuration


class TestConfiguration(unittest.TestCase):
    '''
    get_monitor_mode_interface() must randomize the MAC whenever --random-mac
    is set -- both when it auto-selects the interface and when the interface
    was supplied with -i. rfkill unblocking is stubbed out in all cases.
    '''

    def setUp(self):
        # random_mac is only set once Configuration.initialize() runs; default
        # it here so these unit tests don't depend on full initialization.
        self._saved = (getattr(Configuration, 'interface', None),
                       getattr(Configuration, 'random_mac', False))

    def tearDown(self):
        Configuration.interface, Configuration.random_mac = self._saved

    @patch('wifite.tools.rfkill.Rfkill.wifi_blocked', return_value={'soft': False, 'hard': False})
    @patch('wifite.tools.rfkill.Rfkill.unblock_wifi')
    @patch('wifite.tools.macchanger.Macchanger.random')
    def test_random_mac_fires_with_explicit_interface(self, mock_random, _unblock, _blocked):
        Configuration.interface = 'wlan0'
        Configuration.random_mac = True
        Configuration.get_monitor_mode_interface()
        mock_random.assert_called_once()

    @patch('wifite.tools.rfkill.Rfkill.wifi_blocked', return_value={'soft': False, 'hard': False})
    @patch('wifite.tools.rfkill.Rfkill.unblock_wifi')
    @patch('wifite.tools.macchanger.Macchanger.random')
    @patch('wifite.tools.airmon.Airmon.ask', return_value='wlan0mon')
    def test_random_mac_fires_on_autoselect(self, mock_ask, mock_random, _unblock, _blocked):
        Configuration.interface = None
        Configuration.random_mac = True
        Configuration.get_monitor_mode_interface()
        mock_ask.assert_called_once()
        mock_random.assert_called_once()

    @patch('wifite.tools.rfkill.Rfkill.wifi_blocked', return_value={'soft': False, 'hard': False})
    @patch('wifite.tools.rfkill.Rfkill.unblock_wifi')
    @patch('wifite.tools.macchanger.Macchanger.random')
    def test_no_random_mac_leaves_mac_untouched(self, mock_random, _unblock, _blocked):
        Configuration.interface = 'wlan0'
        Configuration.random_mac = False
        Configuration.get_monitor_mode_interface()
        mock_random.assert_not_called()

    @patch('wifite.tools.rfkill.Rfkill.wifi_blocked', return_value={'soft': False, 'hard': False})
    @patch('wifite.tools.rfkill.Rfkill.unblock_wifi')
    def test_rfkill_unblocked_before_interface_setup(self, mock_unblock, _blocked):
        Configuration.interface = 'wlan0'
        Configuration.random_mac = False
        Configuration.get_monitor_mode_interface()
        mock_unblock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
