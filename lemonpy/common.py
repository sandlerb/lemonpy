#
# Common lemonpy functionality
#

import os
import tempfile

LEMONPY_DIR = 'lemonpy'


class LemonpyError(Exception):
    """
    Base exception type.
    """
    pass


class OptionError(LemonpyError):
    """
    Bad lemonbar option.
    """
    pass


class LemonbarError(LemonpyError):
    """
    Error in or with lemonbar.
    """
    pass


def default_lemonpy_dir():
    user_service_dir = os.path.join('/', 'run', 'user', str(os.geteuid()))
    if os.path.exists(user_service_dir):
        return os.path.join(user_service_dir, LEMONPY_DIR)
    else:
        user = os.environ.get('USER')
        return os.path.join(tempfile.gettempdir(), LEMONPY_DIR, user)
