import json
import logging
from typing import Any, Callable

from app.core import AppData, Task, Transport
from app.lib import Consumer
from app.utils import ensure_not_none

# =============================================================================
# CONSTANTS
# =============================================================================

LOGGER = logging.getLogger(__name__)


# =============================================================================
# MAIN PIPELINE TASKS
# =============================================================================

class FetchForms(Task[AppData, AppData]):

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(self, an_input: AppData) -> AppData:
        LOGGER.info("Fetching forms")
        for form in self._transport.list_forms():
            an_input.add_form(form)
        return an_input


class AppDataToJson(Consumer[AppData]):

    def __init__(self, file_path: str = "all_forms.json", **json_kwargs):
        ensure_not_none(file_path, message='"file_path" MUST be provided.')
        _consume: Callable[[AppData], None] = (
            lambda _item: self._persist_to_json_file(
                app_data=self._forms_to_json(_item),
                file_path=file_path,
                **json_kwargs
            )
        )
        super().__init__(_consume)

    @staticmethod
    def _forms_to_json(app_data: AppData) -> Any:
        LOGGER.debug("Converting app data to json")
        return app_data.to_json()

    @staticmethod
    def _persist_to_json_file(
            app_data: Any,
            file_path: str,
            **json_kwargs
    ) -> None:
        LOGGER.debug('Persisting app data to the file="%s"', file_path)
        with open(file_path, "w") as json_output:
            json.dump(
                app_data,
                json_output,
                ensure_ascii=True,
                check_circular=True,
                indent=4,
                **json_kwargs
            )


class FetchSubmissions(Task[AppData, AppData]):

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(self, an_input: AppData) -> AppData:
        for _form_id in an_input.data:
            _form_versions = an_input.get_all_form_versions(_form_id)
            LOGGER.info('Fetching submissions for form with id="%s"', _form_id)
            _subs = self._transport.list_form_submissions(
                _form_id,
                _form_versions
            )
            for _version, _sub in _subs.items():
                an_input.add_form_submission(
                    form_id=_form_id,
                    form_version=_version,
                    submission=_sub
                )
        return an_input
