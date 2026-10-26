from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

type RuleId = Literal[
    "action-in-task",
    "citation-mismatch",
    "privileged-operator-only",
    "routing-operator-only",
    "scene-slot-domain",
    "slot-conflict",
    "reasoning-check",
]
type Severity = Literal["hold", "deny"]


class RuleHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule: RuleId
    severity: Severity
    reason: str


class Allow(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["allow"] = "allow"


class Hold(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["hold"] = "hold"
    rule: RuleId
    reason: str
    hits: tuple[RuleHit, ...]


class Deny(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["deny"] = "deny"
    rule: RuleId
    reason: str
    hits: tuple[RuleHit, ...]


type Verdict = Annotated[Allow | Hold | Deny, Field(discriminator="kind")]
