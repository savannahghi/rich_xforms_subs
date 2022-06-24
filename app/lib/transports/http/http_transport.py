import itertools
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
    cast
)

from requests.auth import AuthBase
from requests.models import PreparedRequest, Response
from requests.sessions import Session

from app.core import (
    PrimaryInstanceDocumentRoot,
    Transport,
    TransportError,
    TransportOptions,
    XForm
)
from app.utils import ensure_not_none
if TYPE_CHECKING:
    from .http_transport_adapter import HTTPTransportAdapter


# =============================================================================
# TYPES
# =============================================================================

class _OptionalAdapterRequestParams(TypedDict, total=False):
    data: Optional[Union[bytes, str, Mapping[str, Any]]]
    headers: Optional[Mapping[str, Optional[str]]]
    params: Optional[Mapping[str, Union[str, Sequence[str]]]]


class AdapterRequestParams(_OptionalAdapterRequestParams):
    expected_http_status_code: int
    method: str
    url: str


# =============================================================================
# CONSTANTS
# =============================================================================

LOGGER = logging.getLogger(__name__)


# =============================================================================
# HTTP TRANSPORT INTERFACE
# =============================================================================

class HTTPTransport(Transport):
    """
    Transport implementation that uses the HTTP/HTTPS protocol for data
    transmission between this app and an OpenRosa spec compliant server.

    This transport relies on an adapter(`HTTPTransportAdapter`) to perform
    server specific implementation details such as mapping to the correct API
    endpoints and translating responses to the correct domain objects.
    """

    def __init__(
            self,
            transport_adapter: "HTTPTransportAdapter",
            connect_timeout: Optional[float] = None,
            read_timeout: Optional[float] = None
    ):
        super().__init__()
        self._transport_adapter: "HTTPTransportAdapter" = ensure_not_none(
            transport_adapter,
            message='The "transport_adapter" parameter must be provided.'
        )
        self._timeout = (
            (connect_timeout, read_timeout)
            if connect_timeout is not None
            else connect_timeout
        )
        self._session: Session = Session()
        self._session.headers.update({
            "Accept": "*/*",
            "User-Agent": "XFormsRepack/1.0.0"
        })
        self._auth: AuthBase = self._authenticate()

    def flush(
            self,
            timeout: Optional[float] = None,
            callback: Optional[Callable[[bool, Optional[str]], None]] = None
    ) -> None:
        # Do nothing for this transport
        ...

    # FORM RETRIEVAL
    # -------------------------------------------------------------------------
    def get_form(
            self,
            form_id: str,
            version: str,
            **options: TransportOptions
    ) -> XForm:
        response: Response = self._make_request(
            self._transport_adapter.get_form_request(
                form_id,
                version,
                **options
            )
        )
        return self._transport_adapter.response_to_form(
            response.content,
            **options
        )

    def list_form_versions(
            self,
            form_id,
            **options: TransportOptions
    ) -> Sequence[XForm]:
        response: Response = self._make_request(
            self._transport_adapter.list_form_versions_request(
                form_id,
                **options
            )
        )
        versions_data: Union[Sequence[str], Sequence[XForm]]
        versions_data = self._transport_adapter.response_to_form_versions(
            response.content,
            **options
        )
        # If s sequence of XForms was returned, then return that sequence.
        result, values = self._as_xforms_if_possible(versions_data)
        if result:
            return values

        # Else, assume that the sequence is composed of strings(form ids).
        versions: Sequence[str] = cast(Sequence[str], versions_data)
        return tuple(
            map(
                lambda _version: self.get_form(form_id, _version, **options),
                versions
            )
        )

    def list_forms(self, **options: TransportOptions) -> Sequence[XForm]:
        response: Response = self._make_request(
            self._transport_adapter.list_forms_request(**options)
        )
        forms_data: Union[Sequence[str], Sequence[XForm]]
        forms_data = self._transport_adapter.response_to_forms(
            response.content,
            **options
        )
        # If s sequence of XForms was returned, then return that sequence.
        result, values = self._as_xforms_if_possible(forms_data)
        if result:
            return values

        # Else, assume that the sequence is composed of strings(form ids).
        forms_ids: Sequence[str] = cast(Sequence[str], forms_data)
        form_versions: Sequence[Sequence[XForm]] = tuple(
            map(
                lambda _f_id: self.list_form_versions(_f_id, **options),
                forms_ids
            )
        )
        return tuple(itertools.chain.from_iterable(form_versions))

    # SUBMISSION RETRIEVAL
    # -------------------------------------------------------------------------
    def get_submission(
            self,
            form_id: str,
            submission_id: str,
            form_versions: Mapping[str, XForm],
            **options: TransportOptions
    ) -> PrimaryInstanceDocumentRoot:
        LOGGER.info('Fetching submission with id="%s"', submission_id)
        response: Response = self._make_request(
            self._transport_adapter.get_submission_request(
                form_id,
                submission_id,
                **options
            )
        )
        return self._transport_adapter.response_to_submission(
            response.content,
            form_versions,
            **options
        )

    def list_form_submissions(
            self,
            form_id: str,
            form_versions: Mapping[str, XForm],
            **options: TransportOptions
    ) -> Mapping[str, PrimaryInstanceDocumentRoot]:
        LOGGER.info('Fetching submissions for form with id="%s"', form_id)
        response: Response = self._make_request(
            self._transport_adapter.list_form_submissions_request(
                form_id,
                **options
            )
        )
        submissions_data: Union[Sequence[str], Sequence[PrimaryInstanceDocumentRoot]]
        submissions_data = self._transport_adapter.response_to_submissions(
            response.content,
            form_versions,
            **options
        )
        # If the first element is an XForm, an assumption is made that the
        # sequence only contains XForm elements. No further attempt is made to
        # check the type of the other elements.
        submissions: Sequence[PrimaryInstanceDocumentRoot]
        if len(submissions_data) == 0 or isinstance(
                submissions_data[0],
                PrimaryInstanceDocumentRoot
        ):
            submissions = cast(
                Sequence[PrimaryInstanceDocumentRoot],
                submissions_data
            )
        else:
            # Else, assume that the sequence is composed of strings(form ids).
            submissions_data_ids: Sequence[str] = cast(
                Sequence[str],
                submissions_data
            )
            submissions = tuple(
                map(
                    lambda _s_id: self.get_submission(
                        form_id,
                        _s_id,
                        form_versions
                    ),
                    submissions_data_ids
                )
            )
        return {
            _submission.version: _submission
            for _submission in submissions
        }

    # OTHER HELPERS
    # -------------------------------------------------------------------------
    def _authenticate(self) -> AuthBase:
        LOGGER.info("Authenticating HTTP transport on data source")
        request: AdapterRequestParams = self._transport_adapter.authenticate()
        response: Response = self._session.request(
            data=request.get("data"),
            headers=request.get("headers"),
            method=request["method"],
            params=request.get("params"),
            url=request["url"],
            timeout=self._timeout  # type: ignore
        )

        # If authentication was unsuccessful, there is not much that can be
        # done, just log it and raise an exception.
        if response.status_code != request["expected_http_status_code"]:
            error_message: str = (
                "Unable to authenticate HTTP client on data source. Server "
                'says: "%s"' % response.text
            )
            LOGGER.error(error_message)
            raise TransportError(error_message)
        return _HTTPTransportAuth(
            auth_headers=self._transport_adapter.response_to_auth(
                response_content=response.content
            )
        )

    def _make_request(self, request: AdapterRequestParams) -> Response:
        request_message: str = "HTTP Request (%s | %s)" % (
            request["method"],
            request["url"]
        )
        LOGGER.info(request_message)
        response: Response = self._session.request(
            data=request.get("data"),
            headers=request.get("headers"),
            method=request["method"],
            params=request.get("params"),
            url=request["url"],
            auth=self._auth,
            timeout=self._timeout  # type: ignore
        )
        if response.status_code != request["expected_http_status_code"]:
            LOGGER.debug(
                (
                    'Got an unexpected HTTP status, expected="%d", but got'
                    ' "%d" instead'
                ),
                request["expected_http_status_code"],
                response.status_code
            )
            # If the received response status was not what was expected, check
            # if the status is among the re-authentication trigger status and
            # if so, re-authenticate and then retry this request.
            if response.status_code in self._transport_adapter.authentication_trigger_statuses:  # noqa
                LOGGER.debug(
                    (
                        'Encountered an authentication trigger status("%d"), '
                        're-authenticating'
                    ),  # noqa
                    response.status_code
                )
                self._auth = self._authenticate()
                LOGGER.debug(
                    "Re-authentication successful, retrying the request."
                )
                # FIXME: This could lead into a stack overflow, revisit this.
                return self._make_request(request)

            # If not, then an error has occurred, log the error the raise an
            # exception.
            error_message: str = (
                "%s : Failed. Expected response status %d, but got %d" %
                (
                    request_message,
                    request["expected_http_status_code"],
                    response.status_code
                )
            )
            LOGGER.error(error_message)
            raise TransportError(error_message)
        return response

    @staticmethod
    def _as_xforms_if_possible(
            values: Union[Sequence[str], Sequence[XForm]]
    ) -> Tuple[bool, Sequence[XForm]]:
        # If the first element is an XForm, an assumption is made that the
        # sequence only contains XForm elements. No further attempt is made to
        # check the type of the other elements.
        # An empty sequence is also assumed to contain XForms.
        if len(values) == 0 or isinstance(values[0], XForm):
            return True, cast(Sequence[XForm], values)

        return False, tuple()


# =============================================================================
# HTTP TRANSPORT AUTH
# =============================================================================

class _HTTPTransportAuth(AuthBase):

    def __init__(self, auth_headers: Mapping[str, str]):
        self._auth_headers = auth_headers

    def __call__(self, r: PreparedRequest, *args, **kwargs) -> PreparedRequest:
        r.headers.update(self._auth_headers)
        return r
