#! /usr/bin/env python

from lemonpy.ipc import LemonpyServer, LemonpyClient
from lemonpy.lemonbar import Lemonbar

import time

SOCKET_NAME = 'lemonpy_socket'

l1 = Lemonbar(permanent=True)
time.sleep(0.5)
l1.update('l1')

ls = LemonpyServer(SOCKET_NAME, bars={'l1': l1})
ls.run()

lc = LemonpyClient(SOCKET_NAME)
