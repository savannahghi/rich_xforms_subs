import io
import json
from typing import Any, Mapping, Optional, Union, Sequence

from lxml import etree

from app.core import PrimaryInstanceDocumentRoot, TransportOptions, XForm
from app.loaders.load_submission import do_load_submission
from app.loaders.load_xform import do_load_form
from app.utils import ensure_not_none_nor_empty as not_empty

from .http_transport_adapter import AdapterRequestParams, HTTPTransportAdapter


# =============================================================================
# CONSTANTS
# =============================================================================

_GET_METHOD: str = "GET"
_POST_METHOD: str = "POST"


# =============================================================================
# ADAPTER
# =============================================================================

class ODKCentralHTTPTransportAdapter(HTTPTransportAdapter):
    """A `HTTPTransportAdapter` to an ODK Central instance.

    Note: Each `ODKCentralHTTPTransportAdapter` works within the context of a
        single ODK Central project.
    """

    def __init__(
            self,
            instance_host_url: str,
            project_id: str,
            email: str,
            password: str,
            api_version: Optional[str]
    ):
        self._instance_host_url: str = not_empty(
            instance_host_url,
            message='"instance_host_url" MUST be provided.'
        )
        self._project_id: str = not_empty(
            project_id,
            message='"project_id" MUST be provided.'
        )
        self._email: str = not_empty(
            email,
            message='"email" MUST be provided.'
        )
        self._password: str = not_empty(
            password,
            message='"password" MUST be provided.'
        )
        self._api_version: str = api_version or "v1"
        self._base_url: str = "%s/%s/projects/%s" % (
            self._instance_host_url,
            self._api_version,
            self._project_id
        )
        self._authentication_trigger_statuses: Sequence[int] = (400,)

    # AUTHENTICATION
    # -------------------------------------------------------------------------
    @property
    def authentication_trigger_statuses(self) -> Sequence[int]:
        return self._authentication_trigger_statuses

    def authenticate(
            self,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "data": json.dumps({
                "email": self._email,
                "password": self._password
            }),
            "expected_http_status_code": 200,
            "method": _POST_METHOD,
            "url": "%s/%s/sessions" % (
                self._instance_host_url,
                self._api_version
            )
        }

    def response_to_auth(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Mapping[str, str]:
        token: str = json.loads(response_content).get("token", "")
        return {"Authorization": "Bearer %s" % token}

    # FORM RETRIEVAL
    # -------------------------------------------------------------------------
    def get_form_request(
            self,
            form_id: str,
            version: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/xml"
            },
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/forms/%s/versions/%s.xml" % (
                self._base_url, form_id, version
            )
        }

    def list_form_versions_request(
            self,
            form_id: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/json"
            },
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/forms/%s/versions" % (self._base_url, form_id)
        }

    def list_forms_request(
            self,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/json"
            },
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/forms" % self._base_url
        }

    def response_to_form(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> XForm:
        return XForm.of_mapping(
            do_load_form(etree.parse(io.BytesIO(response_content)))
        )

    def response_to_form_versions(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[XForm]]:
        versions_data: Sequence[Mapping[str, Any]] = json.loads(
            response_content
        )
        return tuple(
            _version_data["version"]
            for _version_data in versions_data
            # FIXME: THIS IS A HACK !!!!
            #  A filter to get the latest version
            if _version_data["enketoId"] is not None
        )

    def response_to_forms(
            self,
            response_content: bytes,
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[XForm]]:
        forms_data: Sequence[Mapping[str, Any]] = json.loads(response_content)
        return tuple((_form_data["xmlFormId"] for _form_data in forms_data))

    # SUBMISSION RETRIEVAL
    # -------------------------------------------------------------------------
    def get_submission_request(
            self,
            form_id: str,
            submission_id: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/xml"
            },
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/forms/%s/submissions/%s.xml" % (
                self._base_url,
                form_id,
                submission_id
            )
        }

    def list_form_submissions_request(
            self,
            form_id: str,
            **options: TransportOptions
    ) -> AdapterRequestParams:
        return {
            "headers": {
                "Accept": "application/json"
            },
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/forms/%s/submissions" % (
                self._base_url,
                form_id
            )
        }

    def response_to_submission(
            self,
            response_content: bytes,
            form_version: Mapping[str, XForm],
            **options: TransportOptions
    ) -> PrimaryInstanceDocumentRoot:
        return do_load_submission(
            etree.parse(io.BytesIO(response_content)),
            form_version
        )

    def response_to_submissions(
            self,
            response_content: bytes,
            form_version: Mapping[str, XForm],
            **options: TransportOptions
    ) -> Union[Sequence[str], Sequence[PrimaryInstanceDocumentRoot]]:
        submission_data: Sequence[Mapping[str, Any]] = json.loads(
            response_content
        )
        return tuple((
            _submission_data["instanceId"]
            for _submission_data in submission_data
        ))
