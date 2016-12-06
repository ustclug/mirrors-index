#!/usr/bin/env python3

"""Common code used by mirrors-index. Mostly logging."""

import logging

def init_logger() -> logging.Logger:
    l = logging.getLogger('mirrors-genindex')
    l.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))

    l.addHandler(ch)

    return l

logger = init_logger()
