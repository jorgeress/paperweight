from pydantic import BaseModel, ConfigDict

from paperweight.policy.task import ActionKind
from paperweight.provenance.observation import CitedValue


class ProposedAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ActionKind
    params: dict[str, CitedValue] = {}
