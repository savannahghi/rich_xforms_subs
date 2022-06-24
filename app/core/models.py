from typing import Any, Dict, List, Mapping, Optional, Tuple, TypedDict
from .exceptions import RichXFormsSubsError
from .mixins import ToJson
from .xforms_spec import PrimaryInstanceDocumentRoot, XForm


# =============================================================================
# TYPES
# =============================================================================

class _FormAndSubmissions(TypedDict):
    form: XForm
    submissions: List[PrimaryInstanceDocumentRoot]


_AppData = Dict[str, Dict[str, _FormAndSubmissions]]


# =============================================================================
# APP MODELS
# =============================================================================

class AppData(ToJson):

    def __init__(self):
        self._data: _AppData = dict()

    @property
    def data(self) -> _AppData:
        # Return a copy of the current data
        return dict(self._data)

    def add_form(self, form: XForm) -> None:
        form_versions: Dict[str, _FormAndSubmissions] = self._data.setdefault(
            form.id, dict()
        )
        form_versions[form.version] = {"form": form, "submissions": []}

    def add_form_submission(
            self,
            form_id: str,
            form_version: str,
            submission: PrimaryInstanceDocumentRoot
    ) -> None:
        try:
            self._data[form_id][form_version]["submissions"].append(submission)
        except KeyError as exp:
            raise RichXFormsSubsError(
                'A form with id="%s" or version="%s" was not found on the app.'
                % (form_id, form_version)
            ) from exp

    def get_all_form_versions(self, form_id: str) -> Mapping[str, XForm]:
        form_versions: Dict[str, _FormAndSubmissions] = self._data.setdefault(
            form_id, dict()
        )
        _entry: Tuple[str, _FormAndSubmissions]
        return dict(
            map(
                lambda _entry: (_entry[0], _entry[1]["form"]),
                form_versions.items()
            )
        )

    def get_form(self, form_id: str, version: str) -> Optional[XForm]:
        form_versions: Dict[str, _FormAndSubmissions] = self._data.get(
            form_id, dict()
        )
        return form_versions.get(version, dict()).get("form", None)

    def to_json(self) -> Any:
        def _form_and_subs_to_json(form_and_subs: _FormAndSubmissions) -> Any:
            return {
                "form": form_and_subs["form"].to_json(),
                "submissions": [
                    _sub.to_json()
                    for _sub in form_and_subs["submissions"]
                ]
            }

        def _app_data_to_json(
                entry: Tuple[str, Dict[str, _FormAndSubmissions]]
        ) -> Any:
            return (
                entry[0],
                dict(
                    map(
                        lambda _entry: (
                            _entry[0],
                            _form_and_subs_to_json(_entry[1])
                        ),
                        entry[1].items()
                    )
                )
            )
        return dict(map(_app_data_to_json, self._data.items()))  # noqa
