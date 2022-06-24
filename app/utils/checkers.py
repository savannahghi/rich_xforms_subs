from typing import Optional, Sized, TypeVar

_S = TypeVar("_S", bound=Sized)
_T = TypeVar("_T")


def ensure_not_none(
        value: Optional[_T],
        message: str = '"value" cannot be None.'
) -> _T:
    """Check that given value is not None.

    If the value is None, then an assertion error is raised.

    :param value: The value to check.
    :param message: An optional error message to be shown when value is None.

    :return: The given value if the value isn't None.

    :raise AssertionError: If the given value is None.
    """
    assert value is not None, message
    return value


def ensure_not_none_nor_empty(
        value: _S,
        message: str = '"value" cannot be None or empty.'
) -> _S:
    """
    Check that a sized value is not None or empty(has a size of zero).

    If the value is None or empty, then an assertion error is raised.

    :param value: The value to check.
    :param message: An optional error message to be shown when value is None or
           empty.

    :return: The given value if it isn't None or empty.

    :raise AssertionError: If the given value is None or empty.
    """
    assert len(ensure_not_none(value, message=message)) > 0, message
    return value
