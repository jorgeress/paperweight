from typing import Literal

from pydantic import BaseModel, ConfigDict

OPERATOR = "operator"
# note: perception adds one object observation with this field, holding the parcel condition
CONDITION_FIELD = "condition"

type ObservationKind = Literal["label_field", "free_text", "object"]


class Observation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: ObservationKind
    field: str | None = None
    text: str
    bbox: tuple[int, int, int, int]


class CitedValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str
    # note: either OPERATOR or the id of an observation from the same frame
    cite: str


def find_observation(cite: str, observations: list[Observation]) -> Observation | None:
    return next((o for o in observations if o.id == cite), None)
