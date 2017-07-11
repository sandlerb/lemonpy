#
# Python wrapper around lemonbar
#

# Need to clean up system resources in __del__
# Maybe add a contextmanager interface?


# Design notes:
#       Want to be able to create a lemonbar and then look up existing lemonbars, something like:
#       ```
#       # Client side
#       bar_content = build_lemonbar_content()
#       lc = LemonbarClient(service=os.env['LEMONBAR_SERVICE'], bar=os.env['LEMONBAR_NAME'])
#       lc.update(bar_content)

#       # need a way to trigger shutdown
#       ````
#
#       ```
#       # Service side
#
#       lb = LemonBar.from_yaml('config.yml')
#       ls = LemonbarService()
#       ls.register(lb)
#
#       ls.wait_for_shutdown()
#       ```
#
#       So to do this we need a server/service/manager running in the background and a way to
#       connect to it
#
#       Need to reorganize files
#       - lemonbar.py - shared constants, etc
#       - bar.py - LemonBar
#       - service.py - LemonbarService
#       - client - LemonbarClient.py
#
#       Objects:
#       - Lemonbar - representes a lemonbar instance
#       - LemonbarManager - manages a group of lemonbar instances
#           - is this necessary or can we roll it into the Service
#       - LemonbarService - persistent background service that owns a LemonbarManager
#       - LemonbarClient - connects to a LemonbarService and provides an API for interacting with
#                          existing Lemonbar instances
#       - LemonbarTransport - IPC


import shutil
import subprocess
import time


DEFAULT_BINARY_NAME = 'lemonbar'

DEFAULT_PROC_TERMINATE_WAIT_S = 1.0


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


class Lemonbar(object):
    """
    Python wrapper of an instance of Lemonbar.

    By default this class will respect lemonbar's defaults, however the user can override them
    at initialization.
    """
    def __init__(self, binary_path=None, geometry=None, bottom=None,
                 force_docking=None, font=None, clickable_areas=None, permanent=None, wm_name=None,
                 underline_width_px=None, bg_color=None, fg_color=None, vertical_offset=None,
                 underline_color=None):
        # TODO use pythonic args, convert to cli options
        self._geometry = geometry
        self._bottom = bottom
        self._force_docking = force_docking
        self._font = font
        self._clickable_areas = clickable_areas
        self._permanent = permanent
        self._wm_name = wm_name
        self._underline_width_px = underline_width_px
        self._bg_color = bg_color
        self._fg_color = fg_color
        self._vertical_offset = vertical_offset
        self._underline_color = underline_color

        self._binary_path = binary_path or shutil.which(DEFAULT_BINARY_NAME)

        # Is this instance managed by a LemonbarManager?
        self.managed = False

        args = [self._binary_path] + self._build_cli_option_string()
        self._proc = subprocess.Popen(args=args, stdin=subprocess.PIPE)

    def __del__(self):
        try:
            self.close()
        except LemonpyError as le:
            # TODO log error
            print(le)
            pass

    def close(self, kill=False, timeout_s=DEFAULT_PROC_TERMINATE_WAIT_S):
        """
        Close the lemonbar instance.

        If the user sets kill=True, this method will still try to terminate before resorting to a kill.
        """
        def _wait():
            closed = False
            start = time.time()
            while (time.time() - start) < timeout_s:
                if self._proc.poll() is not None:
                    closed = True
                    break
                else:
                    # TODO this isn't safe, want a floor
                    time.sleep(timeout_s / 10.0)

            if not closed:
                raise LemonbarError('Failed to close lemonbar')

        def _try_and_wait(func):
            func()
            try:
                _wait()
            except LemonbarError:
                raise LemonbarError('Could not stop the lemonbar process lemonbar')

        if self._proc and self._proc.poll() is None:
            # Always try to terminate before killing
            try:
                _try_and_wait(self._proc.terminate)
            except LemonbarError:
                # TODO log
                if kill:
                    _try_and_wait(self._proc.kill)
                else:
                    raise

    def _build_cli_option_string(self):
        opts = [_option_if_option('-g', self._geometry),
                _option_flag('-b', self._bottom),
                _option_flag('-d', self._force_docking),
                _option_if_option('-f', self._font),
                _option_if_option('-a', self._clickable_areas),
                _option_flag('-p', self._permanent),
                _option_if_option('-n', self._wm_name),
                _option_if_option('-u', self._underline_width_px),
                _option_if_option('-B', self._bg_color),
                _option_if_option('-F', self._fg_color),
                _option_if_option('-o', self._vertical_offset),
                _option_if_option('-U', self._underline_color)]

        # TODO gotta be a cleaner way to do this
        return [x for x in opts if x is not None]


def _option_if_option(switch, option):
    if option is None:
        return None

    return ' ' + switch + ' ' + option


def _option_flag(switch, arg):
    if arg is None:
        return None

    return switch