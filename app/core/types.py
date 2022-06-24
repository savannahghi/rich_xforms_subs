from typing import (
    Any,
    Mapping,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
)


AssessmentToolType = Literal["ABOVE SITE", "SITE"]


DATIMDataType = Literal[
    "BOOLEAN",
    "INTEGER",
    "INTEGER_ZERO_OR_POSITIVE",
    "LONG_TEXT",
    "NUMBER"
]


PARENT_QUESTION_TYPES: Tuple[str, ...] = (
    "A-NUM",
    "COMM",
    "NA",
    "PERC",
    "RESP",
    "SCORE",
    "T-NUM"
)


class InstanceMetadataMapping(TypedDict):
    instance_id: Optional[str]
    instance_name: Optional[str]


class PrimaryInstanceMapping(TypedDict):
    id: str
    version: str
    questions: Mapping[str, "QuestionMapping"]
    meta: InstanceMetadataMapping
    prefix: Optional[str]
    delimiter: Optional[str]


class QuestionMapping(TypedDict):
    name: str
    question_type: str
    read_only: bool
    xpath: str
    label: Optional[str]
    required: Optional[bool]
    tag: Optional[str]
    sub_questions: Optional[Mapping[str, "QuestionMapping"]]
    value: Optional[Any]


class SecondaryInstanceItemMapping(TypedDict):
    name: str
    label: str
    extras: Optional[Mapping[str, str]]


class SecondaryInstanceMapping(TypedDict):
    id: str
    items: Sequence[SecondaryInstanceItemMapping]


class XFormMapping(TypedDict):
    title: str
    primary_instance: PrimaryInstanceMapping
    secondary_instances: Mapping[str, SecondaryInstanceMapping]
    xforms_version: str
