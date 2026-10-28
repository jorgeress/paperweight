from typing import Literal

from pydantic import BaseModel, Field

type ParcelCondition = Literal["intact", "damaged", "wet", "open"]

PERCEPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["label_field", "free_text", "object"]},
                    "field": {"type": ["string", "null"]},
                    "text": {"type": "string"},
                    "bbox": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
                },
                "required": ["kind", "field", "text", "bbox"],
                "additionalProperties": False,
            },
        },
        "parcel_condition": {"enum": ["intact", "damaged", "wet", "open"]},
    },
    "required": ["observations", "parcel_condition"],
    "additionalProperties": False,
}


class RawObservation(BaseModel):
    kind: Literal["label_field", "free_text", "object"]
    field: str | None
    text: str
    bbox: list[int] = Field(min_length=4, max_length=4)


class RawPerception(BaseModel):
    observations: list[RawObservation]
    parcel_condition: ParcelCondition
