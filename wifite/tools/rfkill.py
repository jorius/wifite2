#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dependency import Dependency
from ..util.process import Process

import re


class Rfkill(Dependency):
    '''
    Wrapper around `rfkill`.

    Wireless cards are frequently left *soft*-blocked (by NetworkManager, a
    previous session, or the saved hardware state). While blocked, bringing the
    interface up fails with:

        SIOCSIFFLAGS: Operation not possible due to RF-kill

    which breaks monitor-mode setup. wifite clears any soft block before
    enabling monitor mode so the user doesn't have to run `rfkill unblock`
    by hand. A *hard* block (physical switch / BIOS) cannot be cleared in
    software; callers warn when the radio is still hard-blocked afterwards.
    '''
    dependency_required = False
    dependency_name = 'rfkill'
    dependency_url = 'apt install rfkill'

    @classmethod
    def exists(cls):
        return Process.exists('rfkill')

    @classmethod
    def unblock_wifi(cls):
        '''Clear soft rfkill blocks on wireless devices. No-op if rfkill is missing.'''
        if not cls.exists():
            return False
        Process(['rfkill', 'unblock', 'wifi']).wait()
        return True

    @staticmethod
    def _parse_blocks(output):
        '''
        Parse `rfkill list` text into aggregated block state for wireless-LAN
        devices, e.g.:

            1: phy0: Wireless LAN
                Soft blocked: yes
                Hard blocked: no

        Returns {'soft': bool, 'hard': bool}.
        '''
        soft = hard = False
        in_wifi = False
        for line in output.split('\n'):
            header = re.match(r'^\s*\d+:\s+\S+:\s+(.*)$', line)
            if header:
                desc = header.group(1).lower()
                in_wifi = 'wireless lan' in desc or 'wlan' in desc or 'wifi' in desc
                continue
            if in_wifi:
                low = line.strip().lower()
                if low.startswith('soft blocked:'):
                    soft = soft or low.endswith('yes')
                elif low.startswith('hard blocked:'):
                    hard = hard or low.endswith('yes')
        return {'soft': soft, 'hard': hard}

    @classmethod
    def wifi_blocked(cls):
        '''Return {'soft': bool, 'hard': bool} for wireless devices.'''
        if not cls.exists():
            return {'soft': False, 'hard': False}
        return cls._parse_blocks(Process(['rfkill', 'list']).stdout())
