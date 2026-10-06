#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..util.color import Color
from ..tools.airodump import Airodump
from ..util.input import raw_input, xrange
from ..model.target import Target, WPSState
from ..config import Configuration

from time import sleep, time

class Scanner(object):
    ''' Scans wifi networks & provides menu for selecting targets '''

    # Console code for moving up one line
    UP_CHAR = '\x1B[1F'

    def __init__(self):
        '''
        Scans for targets via Airodump.
        Loops until scan is interrupted via user or config.
        Note: Sets this object's `targets` attrbute (list[Target]) upon interruption.
        '''
        self.previous_target_count = 0
        self.targets = []
        self.target = None # Target specified by user (based on ESSID/BSSID)

        max_scan_time = Configuration.scan_time

        self.err_msg = None

        # Loads airodump with interface/channel/etc from Configuration
        try:
            with Airodump() as airodump:
                # Loop until interrupted (Ctrl+C)
                scan_start_time = time()

                while True:
                    if airodump.pid.poll() is not None:
                        return  # Airodump process died

                    self.targets = airodump.get_targets(old_targets=self.targets)

                    if self.found_target():
                        return  # We found the target we want

                    if airodump.pid.poll() is not None:
                        return  # Airodump process died

                    for target in self.targets:
                        if target.bssid in airodump.decloaked_bssids:
                            target.decloaked = True

                    # Cap the live list to the terminal height so it refreshes
                    # in place instead of scrolling; the full list is shown on
                    # Ctrl+C for selection.
                    self.print_targets(max_targets=Scanner.max_display_targets())

                    target_count = len(self.targets)
                    client_count = sum(len(t.clients) for t in self.targets)

                    outline = '\r{+} Scanning'
                    if airodump.decloaking:
                        outline += ' & decloaking'
                    outline += '. Found'
                    outline += ' {G}%d{W} target(s),' % target_count
                    outline += ' {G}%d{W} client(s).' % client_count
                    outline += ' {O}Ctrl+C{W} when ready '
                    Color.clear_entire_line()
                    Color.p(outline)

                    if max_scan_time > 0 and time() > scan_start_time + max_scan_time:
                        return

                    sleep(1)

        except KeyboardInterrupt:
            pass


    def found_target(self):
        '''
        Detect if we found a target specified by the user (optional).
        Sets this object's `target` attribute if found.
        Returns: True if target was specified and found, False otherwise.
        '''
        bssid = Configuration.target_bssid
        essid = Configuration.target_essid

        if bssid is None and essid is None:
            return False  # No specific target from user.

        for target in self.targets:
            if Configuration.wps_only and target.wps not in [WPSState.UNLOCKED, WPSState.LOCKED]:
                continue
            if bssid and target.bssid and bssid.lower() == target.bssid.lower():
                self.target = target
                break
            if essid and target.essid and essid.lower() == target.essid.lower():
                self.target = target
                break

        if self.target:
            Color.pl('\n{+} {C}found target{G} %s {W}({G}%s{W})'
                % (self.target.bssid, self.target.essid))
            return True

        return False


    def print_targets(self, max_targets=None):
        '''Prints targets selection menu (1 target per row).

        When `max_targets` is set (the live scan), only the strongest
        `max_targets` targets are shown, with a "...N more" footer, so the list
        refreshes in place instead of scrolling past the top of the terminal.
        When it is None (final selection) every target is shown.
        '''
        if len(self.targets) == 0:
            Color.p('\r')
            return

        shown, hidden = Scanner._visible_targets(self.targets, max_targets)

        # Variable rows printed below the header + separator: the target rows
        # plus the optional "...N more" footer. Drives the in-place cursor math.
        displayed_rows = len(shown) + (1 if hidden else 0)

        if self.previous_target_count > 0:
            # We need to 'overwrite' the previous list of targets.
            if Configuration.verbose <= 1:
                # Don't clear screen buffer in verbose mode.
                if self.previous_target_count > displayed_rows or \
                   Scanner.get_terminal_height() < displayed_rows + 3:
                    # Either we now print fewer rows than before (can't overwrite
                    # the old ones) or the block won't fit; clear and reprint.
                    from ..util.process import Process
                    Process.call('clear')
                else:
                    # Fits: move cursor up to print over the previous list.
                    Color.pl(Scanner.UP_CHAR * (3 + self.previous_target_count))

        self.previous_target_count = displayed_rows

        # First row: columns. Clear each line before (over)writing so stale,
        # longer content from a previous refresh leaves no tail behind.
        Color.clear_entire_line()
        Color.p('{W}{D}   NUM')
        Color.p('                      ESSID')
        if Configuration.show_bssids:
            Color.p('              BSSID')
        Color.pl('   CH  ENCR  POWER  WPS?  CLIENT')

        # Second row: separator
        Color.clear_entire_line()
        Color.p('   ---')
        Color.p('  -------------------------')
        if Configuration.show_bssids:
            Color.p('  -----------------')
        Color.pl('  ---  ----  -----  ----  ------{W}')

        # Remaining rows: targets
        for idx, target in enumerate(shown, start=1):
            Color.clear_entire_line()
            Color.p('   {G}%s  ' % str(idx).rjust(3))
            Color.pl(target.to_str(Configuration.show_bssids))

        if hidden:
            Color.clear_entire_line()
            Color.pl('   {D}... and %d more '
                     '(strongest shown; {O}Ctrl+C{D} to list & select all){W}' % hidden)

    @staticmethod
    def get_terminal_height():
        import shutil
        # shutil checks $LINES/$COLUMNS then the tty, with a safe fallback --
        # more robust than parsing `stty size`, which throws when stdout isn't
        # a tty (e.g. piped output).
        return shutil.get_terminal_size(fallback=(80, 25)).lines

    @staticmethod
    def get_terminal_width():
        import shutil
        return shutil.get_terminal_size(fallback=(80, 25)).columns

    @staticmethod
    def max_display_targets():
        '''
        How many target rows the live scan list may show so the table refreshes
        in place instead of scrolling. Reserves rows for the header, separator,
        the "...N more" footer, the "Scanning..." status line and a small
        margin.
        '''
        return max(1, Scanner.get_terminal_height() - 6)

    @staticmethod
    def _visible_targets(targets, max_targets):
        '''
        Apply the live-scan display cap. Returns (shown, hidden_count): the
        first `max_targets` targets and how many were hidden. `max_targets` of
        None (final selection) shows everything.
        '''
        if max_targets is not None and len(targets) > max_targets:
            return targets[:max_targets], len(targets) - max_targets
        return targets, 0

    def select_targets(self):
        '''
        Returns list(target)
        Either a specific target if user specified -bssid or --essid.
        Otherwise, prompts user to select targets and returns the selection.
        '''

        if self.target:
            # When user specifies a specific target
            return [self.target]

        if len(self.targets) == 0:
            if self.err_msg is not None:
                Color.pl(self.err_msg)

            # TODO Print a more-helpful reason for failure.
            # 1. Link to wireless drivers wiki,
            # 2. How to check if your device supporst monitor mode,
            # 3. Provide airodump-ng command being executed.
            raise Exception('No targets found.'
                + ' You may need to wait longer,'
                + ' or you may have issues with your wifi card')

        # Return all targets if user specified a wait time ('pillage').
        if Configuration.scan_time > 0:
            return self.targets

        # Ask user for targets. The live scan showed only a terminal-capped
        # list, so clear and reset the in-place state to print the full list
        # once -- this avoids the stale-cursor double-print on Ctrl+C.
        from ..util.process import Process
        Process.call('clear')
        self.previous_target_count = 0
        self.print_targets()
        Color.clear_entire_line()

        if self.err_msg is not None:
            Color.pl(self.err_msg)

        input_str  = '{+} select target(s)'
        input_str += ' ({G}1-%d{W})' % len(self.targets)
        input_str += ' separated by commas, dashes'
        input_str += ' or {G}all{W}: '

        chosen_targets = []

        for choice in raw_input(Color.s(input_str)).split(','):
            choice = choice.strip()
            if choice.lower() == 'all':
                chosen_targets = self.targets
                break
            if '-' in choice:
                # User selected a range
                (lower,upper) = [int(x) - 1 for x in choice.split('-')]
                for i in xrange(lower, min(len(self.targets), upper + 1)):
                    chosen_targets.append(self.targets[i])
            elif choice.isdigit():
                choice = int(choice) - 1
                chosen_targets.append(self.targets[choice])

        return chosen_targets


if __name__ == '__main__':
    # 'Test' script will display targets and selects the appropriate one
    Configuration.initialize()
    try:
        s = Scanner()
        targets = s.select_targets()
    except Exception as e:
        Color.pl('\r {!} {R}Error{W}: %s' % str(e))
        Configuration.exit_gracefully(0)
    for t in targets:
        Color.pl('    {W}Selected: %s' % t)
    Configuration.exit_gracefully(0)

