from typing import Dict, Optional, Sequence, cast
from lxml.etree import (
    _Element as Element,  # type: ignore
    _ElementTree as ElementTree,  # type: ignore
    QName,
    XPath
)

from app.core import (
    PrimaryInstanceMapping,
    QuestionMapping,
    SecondaryInstanceItemMapping,
    SecondaryInstanceMapping,
    XFormMapping
)
from app.utils import ensure_not_none


# =============================================================================
# CONSTANTS
# =============================================================================

NAMESPACES: Dict[str, str] = {
    "default": "http://www.w3.org/2002/xforms",
    "html": "http://www.w3.org/1999/xhtml",
    "jr": "http://openrosa.org/javarosa",
    "orx": "http://openrosa.org/xforms"
}

UNKNOWN: str = "UNKNOWN"


# =============================================================================
# HELPERS
# =============================================================================

get_primary_instance = XPath(
    path="/html:html/html:head/default:model/default:instance[not(@id)]",
    namespaces=NAMESPACES
)

get_secondary_instances = XPath(
    path="/html:html/html:head/default:model/default:instance[@id]",
    namespaces=NAMESPACES
)


# =============================================================================
# LOADERS
# =============================================================================

def do_load_form(form_xml: ElementTree) -> XFormMapping:
    root: Element = form_xml.getroot()
    secondary_instances_mappings: Sequence[SecondaryInstanceMapping] = tuple((
        load_secondary_instance(_instance)
        for _instance in cast(Sequence[Element], get_secondary_instances(root))
    ))
    return {
        "title": ensure_not_none(
            root.findtext(
                "./html:head/html:title",
                namespaces=NAMESPACES
            )
        ),
        "primary_instance": load_primary_instance(
            primary_instance_xml=cast(
                Sequence[Element],
                get_primary_instance(root)
            )[0],
            xml_root=root
        ),
        "secondary_instances": dict(
            map(
                lambda _si: (_si["id"], _si),
                secondary_instances_mappings
            )
        ),
        "xforms_version": "1.0.0"
    }


def load_primary_instance(
        primary_instance_xml: Element,
        xml_root: Element
) -> PrimaryInstanceMapping:
    document_root: Element = primary_instance_xml[0]
    return load_primary_instance_content(document_root, xml_root)


def load_primary_instance_content(
        document_root: Element,
        xml_root: Element
) -> PrimaryInstanceMapping:
    document_root_name: str = QName(document_root).localname
    question_elements: Sequence[Element] = cast(
        Sequence[Element],
        document_root.xpath(
            "./*[local-name() != 'meta']",
            namespaces=NAMESPACES
        )
    )
    questions_mappings: Sequence[QuestionMapping] = [
        load_question(_qe, xml_root, "/%s" % document_root_name)
        for _qe in question_elements
    ]
    return {
        "id": cast(str, document_root.attrib["id"]),
        "version": cast(str, document_root.attrib["version"]),
        "questions": dict(
            map(
                lambda _question: (_question["name"], _question),
                questions_mappings
            )
        ),
        "meta": {
            "instance_id": document_root.findtext(
                "./default:meta/default:instanceID",
                namespaces=NAMESPACES
            ),
            "instance_name": document_root.findtext(
                "./default:meta/default:instanceName",
                namespaces=NAMESPACES
            )
        },
        "prefix": None,
        "delimiter": None
    }


def load_question(
        xml_element: Element,
        xml_root: Element,
        parent_question_ref: str
) -> QuestionMapping:
    question_name = QName(xml_element.tag).localname
    question_ref = "%s/%s" % (parent_question_ref, question_name)
    is_compound_question: bool = len(xml_element) > 0
    question_kwargs: QuestionMapping = {
        "name": question_name,
        "label": UNKNOWN,
        "question_type": UNKNOWN,
        "read_only": False,
        "sub_questions": dict() if is_compound_question else None,
        "xpath": question_ref,
        "required": False,
        "value": (xml_element.text or "").strip() or None,
        "tag": None
    }

    # Extract the presentational details of a question
    question_presentation_xml: Optional[Element] = xml_root.find(
        "./html:body//*[@ref='%s']" % question_ref,
        namespaces=NAMESPACES
    )
    if question_presentation_xml is not None:
        question_kwargs["question_type"] = QName(question_presentation_xml.tag).localname
        question_kwargs["label"] = question_presentation_xml.findtext(
            path="./default:label",
            namespaces=NAMESPACES
        ) or UNKNOWN

    _sub_question_xml: Element
    for _sub_question_xml in xml_element:
        sub_question = load_question(
            _sub_question_xml,
            xml_root,
            question_ref
        )
        question_kwargs["sub_questions"][sub_question["name"]] = sub_question  # type: ignore
    return question_kwargs


def load_secondary_instance(xml_element: Element) -> SecondaryInstanceMapping:
    secondary_instance_items: Sequence[Element] = xml_element[0].findall(
        path="./default:item",
        namespaces=NAMESPACES
    )
    return {
        "id": cast(str, xml_element.attrib["id"]),
        "items": cast(
            Sequence[SecondaryInstanceItemMapping],
            tuple(
                map(
                    lambda _item: {
                        "name": _item.findtext(
                            "./default:name",
                            namespaces=NAMESPACES
                        ),
                        "label": _item.findtext(
                            "./default:label",
                            namespaces=NAMESPACES
                        )
                    },
                    secondary_instance_items
                )
            )
        ),
    }
