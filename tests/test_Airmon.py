#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '..')

from wifite.tools.airmon import Airmon

import unittest

class TestAirmon(unittest.TestCase):
    def test_airmon_start(self):
        # From https://github.com/derv82/wifite2/issues/67
        stdout = '''
PHY    Interface    Driver        Chipset

phy0    wlan0        iwlwifi        Intel Corporation Centrino Ultimate-N 6300 (rev 3e)

        (mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)
        (mac80211 station mode vif disabled for [phy0]wlan0)
'''
        mon_iface = Airmon._parse_airmon_start(stdout)
        assert mon_iface == 'wlan0mon', 'Expected monitor-mode interface to be "wlan0mon" but got "{}"'.format(mon_iface)

    def test_is_bad_driver_rtw89_family(self):
        # Realtek in-tree rtw89 family (e.g. built-in RTL8852BE) must use the
        # manual type-switch path, not airmon-ng's monitor vif.
        assert Airmon._is_bad_driver('rtw89_8852be') is True
        assert Airmon._is_bad_driver('rtw89_8922ae') is True

    def test_is_bad_driver_legacy_exact(self):
        assert Airmon._is_bad_driver('rtl8821au') is True

    def test_is_bad_driver_good_drivers(self):
        # Well-behaved drivers go through airmon-ng as usual.
        assert Airmon._is_bad_driver('iwlwifi') is False
        assert Airmon._is_bad_driver('ath9k_htc') is False

    def test_is_bad_driver_unknown(self):
        # Missing/blank driver (undetectable) must not be treated as bad.
        assert Airmon._is_bad_driver(None) is False
        assert Airmon._is_bad_driver('') is False

