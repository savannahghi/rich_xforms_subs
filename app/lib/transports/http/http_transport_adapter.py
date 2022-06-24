from abc import ABCMeta, abstractmethod
from typing import Mapping, Sequence, Union

from app.core import PrimaryInstanceDocumentRoot, TransportOptions, XForm
from .http_transport import AdapterRequestParams


# =============================================================================
# HTTP TRANSPORT ADAPTER INTERFACE
# =============================================================================

class HTTPTransportAdapter(metaclass=ABCMeta):
    """
    This interface acts as a bridge between the `HTTPTransport` and the
    different OpenRosa server implementations.
    """

    # AUTHENTICATION
    # -------------------------------------------------------------------------
    @property
    @abstractmethod
    def authentication_trigger_statuses(self) -> Sequence[int]:
        # An empty sequence should cause authentication to happen on each
        # request.
        ...

    @abstractmethod
    def authenticate(
            self,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def response_to_auth(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Mapping[str, str]:
        # Return authentication headers to include on every request.
        ...

    # FORM RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_form_request(
            self,
            form_id: str,
            version: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def list_form_versions_request(
            self,
            form_id,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def list_forms_request(
            self,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def response_to_form(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> XForm:
        ...

    @abstractmethod
    def response_to_form_versions(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[XForm]]:
        ...

    @abstractmethod
    def response_to_forms(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[XForm]]:
        ...

    # SUBMISSION RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_submission_request(
            self,
            form_id: str,
            submission_id: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def list_form_submissions_request(
            self,
            form_id: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        ...

    @abstractmethod
    def response_to_submission(
            self,
            response_content: bytes,
            form_version: Mapping[str, XForm],
            **options: TransportOptions
    ) -> PrimaryInstanceDocumentRoot:
        ...

    @abstractmethod
    def response_to_submissions(
            self,
            response_content: bytes,
            form_version: Mapping[str, XForm],
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[PrimaryInstanceDocumentRoot]]:
        ...
