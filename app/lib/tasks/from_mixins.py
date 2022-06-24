from typing import (
    Any,
    Generic,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    cast
)

from app.core import InitFromMapping, Task, ToJson

# =============================================================================
# TYPES
# =============================================================================

_FM = TypeVar("_FM", bound=InitFromMapping, covariant=True)


# =============================================================================
# ITEM PROCESSORS
# =============================================================================

class ItemFromMapping(
    Generic[_FM],
    Task[Tuple[Type[_FM], Mapping[Any, Any]], _FM]
):

    def execute(self, item: Tuple[Type[_FM], Mapping[Any, Any]]) -> _FM:
        return cast(_FM, item[0].of_mapping(item[1]))


class ItemToJson(Task[ToJson, Any]):

    def execute(self, item: ToJson) -> Any:
        return item.to_json()
