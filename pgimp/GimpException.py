class GimpException(Exception):
    """
    When pgimp encounters a gimp related exception, it will automatically map it onto
    :py:class:`~pgimp.GimpException` or a subtype so that you can easily handle gimp related errors.

    Example:

    >>> from pgimp.GimpScriptRunner import GimpScriptRunner
    >>> try: # doctest: +ELLIPSIS
    ...     GimpScriptRunner().execute('1/0')
    ... except Exception as e:
    ...     str(e)
    '...\\nZeroDivisionError: integer division or modulo by zero\\n'
    """
    pass
