from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from paperweight.provenance.text_match import is_same_value

type Bin = Literal["A", "B", "C"]
type ActionKind = Literal["route", "hold", "priv_open"]


class Slot(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    # note: None means open, any value read from a label field fits
    domain: frozenset[str] | None = None

    def admits(self, value: str) -> bool:
        return self.domain is None or any(is_same_value(d, value) for d in self.domain)


class Grant(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ActionKind
    params: dict[str, str]


class OperatorTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    allowed_actions: frozenset[ActionKind]
    privileged_actions: frozenset[ActionKind] = frozenset()
    slots: tuple[Slot, ...]
    route_slot: str
    routing: dict[str, Bin]
    routing_default: Bin | None = None
    # note: one-shot authorizations typed in the console; the caller consumes them
    grants: tuple[Grant, ...] = ()
    # note: parcel conditions that only allow hold, checked by the policy instead of trusted to the planner
    hold_conditions: frozenset[str] = frozenset()
    # note: free text the operator typed, e.g. "damaged parcels go to hold"; it is operator origin
    instructions: str = ""

    @model_validator(mode="after")
    def check_shape(self) -> Self:
        slot = self.slot(self.route_slot)
        if slot is None:
            raise ValueError(f"route_slot {self.route_slot!r} is not a declared slot")
        if slot.domain is None and self.routing_default is None:
            raise ValueError("an open route slot needs routing_default")
        if self.allowed_actions & self.privileged_actions:
            raise ValueError("an action cannot be both allowed and privileged")
        return self

    def slot(self, name: str) -> Slot | None:
        return next((s for s in self.slots if s.name == name), None)

    def bin_for(self, value: str) -> Bin | None:
        for key, bin_ in self.routing.items():
            if is_same_value(key, value):
                return bin_
        return self.routing_default

    def declares(self, kind: ActionKind, param: str, value: str) -> bool:
        if kind == "route" and param == "bin":
            return value in set(self.routing.values()) | {self.routing_default}
        return any(g.kind == kind and g.params.get(param) == value for g in self.grants)
