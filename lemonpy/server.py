from .exceptions import LemonpyError

import uuid


class DuplicateBarId(LemonpyError):
    """
    The requested bar ID (name, PID, etc) already exists
    """
    pass


class AlreadyManaged(LemonpyError):
    """
    The lemonbar instance is already managed by a LemonbarServer
    """
    pass


class LemonbarServer(object):
    def __init__(self,):
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
            raise LemonpyError('{} is not a managed lemonbar name')
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
