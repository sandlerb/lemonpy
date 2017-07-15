#
# Lemonpy exceptions
#


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
