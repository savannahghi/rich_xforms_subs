"""
ODK XForms Specification Models.
https://getodk.github.io/xforms-spec
"""
from abc import ABCMeta
from functools import cache
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar
)

from typing_inspect import is_optional_type

from .mixins import InitFromMapping, ToJson
from .types import (
    InstanceMetadataMapping,
    PrimaryInstanceMapping,
    QuestionMapping,
    SecondaryInstanceItemMapping,
    SecondaryInstanceMapping,
    XFormMapping
)

# =============================================================================
# TYPES
# =============================================================================

_SE = TypeVar("_SE", bound="AbstractXFormsItem")


# =============================================================================
# HELPERS
# =============================================================================

@cache
def _get_available_annotations(
        xforms_spec_type: Type[_SE]
) -> Mapping[str, Any]:
    return {
        field_name: field_type
        for klass in filter(
            lambda _klass: hasattr(_klass, "__annotations__"),
            xforms_spec_type.mro()
        )
        for field_name, field_type in klass.__annotations__.items()
    }


@cache
def _get_required_fields_names(xforms_spec_type: Type[_SE]) -> Sequence[str]:
    available_annotations: Mapping[str, Any] = _get_available_annotations(
        xforms_spec_type
    )
    return tuple(
        field_name
        for field_name, field_type in available_annotations.items()
        if not is_optional_type(field_type)
    )


# =============================================================================
# XFORM ELEMENTS DEFINITIONS
# =============================================================================

class AbstractXFormsItem(InitFromMapping, ToJson, metaclass=ABCMeta):

    def __init__(self, required_fields: Sequence[str], **kwargs):
        if any(set(required_fields).difference(set(kwargs.keys()))):
            raise ValueError(
                "The following values are required: %s" % ", ".join(
                    required_fields
                )
            )

        for valid_field in _get_available_annotations(self.__class__).keys():
            setattr(self, valid_field, kwargs.get(valid_field))


class XFormsNode(AbstractXFormsItem, metaclass=ABCMeta):
    """A node in an XLSForms Item."""

    def __init__(self, **kwargs):
        super().__init__(_get_required_fields_names(self.__class__), **kwargs)


class InstanceMetadata(XFormsNode):
    """Instance metadata"""
    instance_id: Optional[str]
    instance_name: Optional[str]

    def to_json(self) -> InstanceMetadataMapping:
        return {
            "instance_id": self.instance_id,
            "instance_name": self.instance_name
        }

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "InstanceMetadata":
        return cls(**mapping)


class Question(XFormsNode):
    """A question node in an xls form."""
    name: str
    question_type: str
    read_only: bool
    xpath: str
    label: Optional[str]
    required: Optional[bool]
    sub_questions: Mapping[str, "Question"]
    value: Optional[Any]
    tag: Optional[str]

    def to_json(self) -> QuestionMapping:
        _entry: Tuple[str, Question]
        return {
            "name": self.name,
            "question_type": self.question_type,
            "read_only": self.read_only,
            "xpath": self.xpath,
            "label": self.label,
            "required": self.required,
            "tag": self.tag,
            "sub_questions": dict(
                map(
                    lambda _entry: (_entry[0], _entry[1].to_json()),
                    self.sub_questions.items()
                )
            ) if self.sub_questions else None,
            "value": self.value
        }

    @classmethod
    def of_mapping(cls, mapping: QuestionMapping) -> "Question":
        _copy: Dict[str, Any] = dict(**mapping)
        sub_questions_mappings: Mapping[str, QuestionMapping] = _copy.pop(
            "sub_questions",
            dict()
        )
        _copy["sub_questions"] = dict(
            map(
                lambda _entry: (
                    _entry[0],
                    Question.of_mapping(_entry[1])
                ),
                sub_questions_mappings.items()
            )
        ) if sub_questions_mappings else {}
        return cls(**_copy)


class PrimaryInstanceDocumentRoot(XFormsNode):
    """The document root of a primary instance."""
    id: str
    version: str
    questions: Mapping[str, Question]
    meta: InstanceMetadata
    prefix: Optional[str]
    delimiter: Optional[str]

    def to_json(self) -> PrimaryInstanceMapping:
        return {
            "id": self.id,
            "version": self.version,
            "questions": dict(
                map(
                    lambda _entry: (_entry[0], _entry[1].to_json()),
                    self.questions.items()
                )
            ),
            "meta": self.meta.to_json(),
            "prefix": None,
            "delimiter": None
        }

    @classmethod
    def of_mapping(
            cls,
            mapping: PrimaryInstanceMapping
    ) -> "PrimaryInstanceDocumentRoot":
        _copy: Dict[str, Any] = dict(**mapping)
        meta_mappings: InstanceMetadataMapping = _copy.pop("meta")
        questions_mappings: Mapping[str, QuestionMapping] = _copy.pop(
            "questions"
        )
        _copy["meta"] = InstanceMetadata.of_mapping(meta_mappings)
        _copy["questions"] = dict(
            map(
                lambda _entry: (_entry[0], Question.of_mapping(_entry[1])),
                questions_mappings.items()
            )
        )
        return cls(**_copy)


class PrimaryInstance(XFormsNode):
    """A form's primary instance."""
    document_root: PrimaryInstanceDocumentRoot

    def to_json(self) -> PrimaryInstanceMapping:
        return self.document_root.to_json()

    @classmethod
    def of_mapping(cls, mapping: PrimaryInstanceMapping) -> "PrimaryInstance":
        return cls(
            document_root=PrimaryInstanceDocumentRoot.of_mapping(mapping)
        )


class SecondaryInstanceItem(XFormsNode):
    """An item instance a secondary instance."""
    name: str
    label: str
    extras: Optional[Mapping[str, str]]

    def to_json(self) -> SecondaryInstanceItemMapping:
        return {
            "name": self.name,
            "label": self.label,
            "extras": self.extras
        }

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "SecondaryInstanceItem":
        return cls(**mapping)


class SecondaryInstanceDocumentRoot(XFormsNode):
    items: Sequence[SecondaryInstanceItem]

    def to_json(self) -> Sequence[SecondaryInstanceItemMapping]:
        _item: SecondaryInstanceItem
        return tuple(map(lambda _item: _item.to_json(), self.items))

    @classmethod
    def of_mapping(
        cls,
        mapping: SecondaryInstanceMapping
    ) -> "SecondaryInstanceDocumentRoot":
        _item_mapping: SecondaryInstanceItemMapping
        return cls(**{
            "items": tuple(
                map(
                    lambda _item_mapping: (
                        SecondaryInstanceItem.of_mapping(_item_mapping)
                    ),
                    mapping["items"]
                )
            )
        })


class SecondaryInstance(XFormsNode):
    id: str
    document_root: SecondaryInstanceDocumentRoot

    def to_json(self) -> SecondaryInstanceMapping:
        return {
            "id": self.id,
            "items": self.document_root.to_json()
        }

    @classmethod
    def of_mapping(
            cls,
            mapping: SecondaryInstanceMapping
    ) -> "SecondaryInstance":
        return cls(**{
            "id": mapping["id"],
            "document_root": SecondaryInstanceDocumentRoot.of_mapping(mapping)
        })


class XForm(AbstractXFormsItem):
    title: str
    primary_instance: PrimaryInstance
    secondary_instances: Mapping[str, SecondaryInstance]
    xforms_version: str

    @property
    def id(self) -> str:
        return self.primary_instance.document_root.id

    @property
    def version(self) -> str:
        return self.primary_instance.document_root.version

    def create_form_submission_template(self) -> PrimaryInstanceDocumentRoot:
        # Create a copy of this form's primary instance document root.
        return PrimaryInstanceDocumentRoot.of_mapping(
            self.primary_instance.document_root.to_json()
        )

    def to_json(self) -> XFormMapping:
        _entry: Tuple[str, SecondaryInstance]
        return {
            "title": self.title,
            "primary_instance": self.primary_instance.to_json(),
            "secondary_instances": dict(
                map(
                    lambda _entry: (_entry[0], _entry[1].to_json()),
                    self.secondary_instances.items()
                )
            ),
            "xforms_version": self.xforms_version
        }

    @classmethod
    def of_mapping(cls, mapping: XFormMapping) -> "XForm":
        _copy: Dict[str, Any] = {
            **mapping,
            "primary_instance": PrimaryInstance.of_mapping(
                mapping["primary_instance"]
            ),
            "secondary_instances": dict(
                map(
                    lambda _entry: (
                        _entry[0],
                        SecondaryInstance.of_mapping(_entry[1])
                    ),
                    mapping["secondary_instances"].items()
                )
            )
        }
        return cls(**_copy)

    def __init__(self, **kwargs):
        super().__init__(_get_required_fields_names(self.__class__), **kwargs)
