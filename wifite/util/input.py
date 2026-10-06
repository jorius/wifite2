#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Importing readline transparently enables line editing (left/right arrows,
# Home/End, word-erase and history) for every input() prompt. It is optional:
# on platforms without it (e.g. some Windows setups) prompts still work.
try:
    import readline  # noqa: F401
except ImportError:
    pass

# Fix for raw_input on python3: https://stackoverflow.com/a/7321970
try:
    input = raw_input
except NameError:
    pass

raw_input = input

try:
    range = xrange
except NameError:
    pass

xrange = range
