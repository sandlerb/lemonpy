#! /usr/bin/env python

from lemonpy.lemonbar import Lemonbar

import time

lb = Lemonbar(permanent=True)
lb.update('hello world')
time.sleep(0.5)
lb.close()
