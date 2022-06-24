import logging
from typing import Mapping, Optional
from lxml.etree import (
    _Element as Element,  # type: ignore
    _ElementTree as ElementTree  # type: ignore
)

from app.core import (
    PrimaryInstanceDocumentRoot,
    PrimaryInstanceMapping,
    Question,
    QuestionMapping,
    TransportError,
    XForm
)
from .load_xform import load_primary_instance_content


# =============================================================================
# CONSTANTS
# =============================================================================

LOGGER = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def _load_question_submission_data(
        question: Question,
        question_submission_data: QuestionMapping
) -> None:
    # Set the question value.
    question.value = question_submission_data.get("value")

    # If question has sub questions, then load the sub question values too.
    if question.sub_questions:
        assert question_submission_data["sub_questions"] is not None, (
            'The submission data for question "%s" should have '
            "sub-questions." % question_submission_data["name"]
        )

        subs_submissions_data = question_submission_data["sub_questions"]
        for _sub_question in question.sub_questions.values():
            _load_question_submission_data(
                _sub_question,
                subs_submissions_data[_sub_question.name]
            )


# =============================================================================
# SUBMISSIONS LOADER
# =============================================================================

def do_load_submission(
        submission_xml: ElementTree,
        form_versions: Mapping[str, XForm],
) -> PrimaryInstanceDocumentRoot:
    document_root: Element = submission_xml.getroot()
    submission_data: PrimaryInstanceMapping = load_primary_instance_content(
        document_root,
        document_root
    )
    # Ensure that the given form and submission data are of the same version
    submission_data_version: str = submission_data["version"]
    form: Optional[XForm] = form_versions.get(submission_data_version)
    if form is None:
        error_message: str = (
            'The given submission refers to a non-existent form version: "%s".'
            ' Available form versions are: "%s"'
            % (submission_data_version, ",".join(form_versions))
        )
        LOGGER.error(error_message)
        raise TransportError(error_message)
    submission = form.create_form_submission_template()
    LOGGER.debug(
        'Loading submission with id="%s", for form with title="%s", id="%s" '
        'and version="%s"',
        submission_data["meta"]["instance_id"],
        form.title,
        form.id,
        form.version
    )
    for _question in submission.questions.values():
        _load_question_submission_data(
            _question,
            submission_data["questions"][_question.name]
        )
    return submission
