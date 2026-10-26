from typing import Literal

from pydantic import BaseModel, Field

from paperweight.policy.action import ProposedAction
from paperweight.policy.task import Grant, OperatorTask
from paperweight.policy.verdict import Verdict
from paperweight.provenance.observation import Observation
from paperweight.reasoning_check.review import ReasoningReview

# note: no-defense and hijacked-planner exist to film the before/after, never for real sorting
type PipelineMode = Literal["paperweight", "no-defense", "hijacked-planner"]


class StageCost(BaseModel):
    stage: str
    model: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    replayed: bool


class JudgedAction(BaseModel):
    action: ProposedAction
    policy_verdict: Verdict = Field(discriminator="kind")
    final_verdict: Verdict = Field(discriminator="kind")


class Decision(BaseModel):
    id: str
    at: str
    frame_sha: str
    task: OperatorTask
    pipeline: PipelineMode = "paperweight"
    observations: list[Observation] = []
    judged: list[JudgedAction] = []
    reasoning: str = ""
    review: ReasoningReview | None = None
    commands: list[str]
    lcd: str
    consumed_grants: list[Grant] = []
    stages: list[StageCost] = []
    error: str | None = None
