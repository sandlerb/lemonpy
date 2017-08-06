#
# IPC utilities for Lemonbar
#

import json
import os
import queue
import socket
import threading
import uuid

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


class DuplicateBarId(LemonpyError):
    """
    The requested bar ID (name, PID, etc) already exists
    """
    pass


class AlreadyManaged(LemonpyError):
    """
    The lemonbar instance is already managed by a LemonpyManager
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
    def __init__(self, socket_name, lemonpy_dir=None, bars=None):
        self._lemonpy_dir = lemonpy_dir or default_lemonpy_dir()
        self._manager = _Manager()
        self._cmd_queue = queue.Queue()
        self._run = True

        for name, bar in bars.items():
            self._manager.register(name, bar)

        if not os.path.exists(self._lemonpy_dir):
            os.mkdir(self._lemonpy_dir)

        self._socket_path = _socket_path(self._lemonpy_dir, socket_name, raise_if_exists=True)
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(self._socket_path)
        self._socket.settimeout(5)

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, *args):
        self.close()

    def register(self, name, bar):
        self._manager.register(name, bar)

    def close(self):
        # TODO need a context manager interface so the user doesn't have to atexit
        self._stop()
        self._socket.settimeout(0.1)
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


class _Manager(object):
    def __init__(self):
        # Map of local IDs to actual lemonbar instances
        self._bar_map = dict()

        # Map of user provided names to local IDs
        self._name_map = dict()

    def close(self, close_owned_bars=True):
        for _, bar in self._bar_map.items():
            bar.close()

    def close_bar(self, name):
        bar = self._bar_from_name(name)
        bar.close()

    def _bar_from_name(self, name):
        bar = self._bar_map.get(self._name_map.get(name))
        if bar is None:
            raise LemonpyError('{} is not a managed lemonbar name'.format(name))
        return bar

    def update_bar(self, name, content):
        bar = self._bar_from_name(name)
        bar.update(content)

    def register(self, name, bar):
        """
        Register a lemonbar instance with this server.
        """
        # May want to register by name, pid, or otherwise, so use separate maps in case those
        # namespaces conflict
        if self._key_exists(name, self._name_map):
            raise DuplicateBarId('A lemonbar with the name {} is already being managed'.format(name))

        local_id = uuid.uuid4()
        self._name_map.update({name: local_id})

        self._register_by_id(local_id, bar)

    def _register_by_id(self, local_id, bar):
        if self._bar_is_managed(bar):
            raise AlreadyManaged('Lemonbar instance is already managed (pid: {})'.format(bar.bar_pid))

        self._bar_map.update({local_id: bar})
        bar.managed = True

    def _key_exists(self, key, dictionary):
        return True if dictionary.get(key, None) is not None else False

    def _bar_is_managed(self, bar):
        return bar.managed
