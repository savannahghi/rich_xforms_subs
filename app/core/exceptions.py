class RichXFormsSubsError(RuntimeError):
    """
    Base exception for all non-standard exceptions explicitly raised by the
    app.
    """
    ...


class TransportError(RuntimeError):
    """
    Exception raised to indicate that an error occurred during data transfer.
    """
    ...
