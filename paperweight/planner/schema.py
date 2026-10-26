from typing import Literal

from pydantic import BaseModel

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["route", "hold", "priv_open"]},
                    "params": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"},
                                "cite": {"type": "string"},
                            },
                            "required": ["name", "value", "cite"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["kind", "params"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["actions"],
    "additionalProperties": False,
}


class RawParam(BaseModel):
    name: str
    value: str
    cite: str


class RawAction(BaseModel):
    kind: Literal["route", "hold", "priv_open"]
    params: list[RawParam]


class RawPlan(BaseModel):
    actions: list[RawAction]
