#! /usr/bin/env python

from lemonpy.ipc import LemonpyServer, LemonpyClient
from lemonpy.lemonbar import Lemonbar
from lemonpy.manager import LemonpyManager

import time

SOCKET_NAME = 'lemonpy_socket'

l1 = Lemonbar(permanent=True)
time.sleep(0.5)
l1.update('l1')

lm = LemonpyManager()
lm.register('l1', l1)

ls = LemonpyServer(SOCKET_NAME, lm)
ls.run()

lc = LemonpyClient(SOCKET_NAME)
