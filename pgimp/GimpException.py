# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT


class GimpException(Exception):
    """
    When pgimp encounters a gimp related exception, it will automatically map it onto
    :py:class:`~pgimp.GimpException` or a subtype so that you can easily handle gimp related errors.

    Example:

    >>> from pgimp.GimpScriptRunner import GimpScriptRunner
    >>> try:
    ...     GimpScriptRunner().execute('1/0')
    ... except Exception as e:
    ...     str(e).split('\\n')[-2]
    'ZeroDivisionError: integer division or modulo by zero'
    """
