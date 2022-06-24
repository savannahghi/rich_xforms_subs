from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Mapping, Optional, Sequence

from .xforms_spec import PrimaryInstanceDocumentRoot, XForm


TransportOptions = Mapping[str, Any]


class Transport(metaclass=ABCMeta):
    """This interface represents a flow of data from a data source to the app.

    Data in this context refers to forms and form submissions for the most part
    and data source can be anything that contains forms or submissions.
    """

    @abstractmethod
    def flush(
            self,
            timeout: Optional[float] = None,
            callback: Optional[Callable[[bool, Optional[str]], None]] = None
    ) -> None:
        ...

    # FORM RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_form(
            self,
            form_id: str,
            version: str,
            **options: TransportOptions
    ) -> XForm:
        ...

    @abstractmethod
    def list_form_versions(
            self,
            form_id,
            **options: TransportOptions
    ) -> Sequence[XForm]:
        ...

    @abstractmethod
    def list_forms(self, **options: TransportOptions) -> Sequence[XForm]:
        ...

    # SUBMISSION RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_submission(
            self,
            form_id: str,
            submission_id: str,
            form_versions: Mapping[str, XForm],
            **options: TransportOptions
    ) -> PrimaryInstanceDocumentRoot:
        ...

    @abstractmethod
    def list_form_submissions(
            self,
            form_id: str,
            form_versions: Mapping[str, XForm],
            **options: TransportOptions
    ) -> Mapping[str, PrimaryInstanceDocumentRoot]:
        ...
