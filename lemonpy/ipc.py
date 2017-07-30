#
# IPC utilities for Lemonbar
#

import json
import os
import queue
import socket
import threading

from .common import LemonpyError, default_lemonpy_dir

from enum import Enum


class SocketExists(LemonpyError):
    """
    Socket already exists.
    """
    pass


class SocketDoesNotExist(LemonpyError):
    """
    Socket does not exist.
    """
    pass


class Command(Enum):
    CLOSE_BAR = 1
    CLOSE_SERVER = 2
    LIST_BARS = 3
    UPDATE = 4


def _socket_path(directory, name, raise_if_exists=False):
    addr = os.path.join(directory, name)
    if raise_if_exists and os.path.exists(addr):
        raise SocketExists('{} already exists'.format(name))
    return addr


class LemonpyClient(object):
    def __init__(self, socket_name, lemonpy_dir=None):
        self._lemonpy_dir = lemonpy_dir or default_lemonpy_dir()
        self._socket_path = _socket_path(self._lemonpy_dir, socket_name)

    def update_bar(self, name, content):
        cmd = {'cmd': Command.UPDATE.name, 'bar': name, 'content': content}
        self._send(cmd)

    def _send(self, cmd):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self._socket_path)
            sock.send(json.dumps(cmd).encode('utf-8'))
        finally:
            sock.close()


class LemonpyServer(object):
    def __init__(self, socket_name, manager, lemonpy_dir=None):
        self._lemonpy_dir = lemonpy_dir or default_lemonpy_dir()
        self._manager = manager
        self._cmd_queue = queue.Queue()
        self._run = True

        if not os.path.exists(self._lemonpy_dir):
            os.mkdir(self._lemonpy_dir)

        self._socket_path = _socket_path(self._lemonpy_dir, socket_name, raise_if_exists=True)
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(self._socket_path)
        self._socket.settimeout(5)

    def close(self):
        # TODO need a context manager interface so the user doesn't have to atexit
        self._stop()
        self._rx_thread.join()
        self._worker_thread.join()
        self._manager.close()

        if os.path.exists(self._socket_path):
            os.remove(self._socket_path)

    def run(self):
        self._rx_thread = threading.Thread(target=self._receive_command)
        self._worker_thread = threading.Thread(target=self._handle_command)

        self._rx_thread.start()
        self._worker_thread.start()

    def _receive_command(self):
        self._socket.listen()
        while self._run:
            try:
                conn, _ = self._socket.accept()
                try:
                    cmd = conn.recv(1024)
                    if len(cmd) > 0:
                        self._cmd_queue.put(cmd)
                finally:
                    conn.close()
            except socket.timeout:
                pass

    def _handle_command(self):
        while self._run:
            try:
                cmd = self._cmd_queue.get(timeout=5)
                decoded = json.loads(cmd.decode('utf-8'))
                self._manager.update_bar(decoded['bar'], decoded['content'])
            except queue.Empty:
                pass

    def _stop(self):
        """
        Stop the server.
        """
        self._run = False
