#! /usr/bin/env python

from lemonpy.lemonbar import Lemonbar
from lemonpy.server import LemonbarServer

import time

lb = Lemonbar(permanent=True)
lb.update('hello world')
time.sleep(0.5)
lb.close()

l1 = Lemonbar(permanent=True)
l1.update('l1')
l2 = Lemonbar(permanent=True)
l1.update('l2')
l3 = Lemonbar(permanent=True)
l1.update('l3')

ls = LemonbarServer()

ls.register('l1', l1)
ls.register('l2', l2)
ls.register('l3', l3)

time.sleep(0.5)

ls.close()
