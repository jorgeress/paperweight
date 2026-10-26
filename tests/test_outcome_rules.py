from paperweight.pipeline.decision import JudgedAction
from paperweight.pipeline.outcome_rules import choose_commands
from paperweight.policy.action import ProposedAction
from paperweight.policy.escalate import escalate_verdict
from paperweight.policy.verdict import Allow, Deny, Hold, RuleHit
from paperweight.provenance.observation import OPERATOR, CitedValue
from paperweight.reasoning_check.review import ReasoningReview

ROUTE_A = ProposedAction(
    kind="route",
    params={"destination_city": CitedValue(value="MADRID", cite="obs-1"), "bin": CitedValue(value="A", cite=OPERATOR)},
)
PRIV = ProposedAction(kind="priv_open", params={"cage": CitedValue(value="R1", cite=OPERATOR)})
HIT = RuleHit(rule="routing-operator-only", severity="deny", reason="x")
DENY = Deny(rule="routing-operator-only", reason="x", hits=(HIT,))
HOLD = Hold(rule="scene-slot-domain", reason="y", hits=(RuleHit(rule="scene-slot-domain", severity="hold", reason="y"),))


def judged(action, verdict) -> JudgedAction:
    return JudgedAction(action=action, policy_verdict=verdict, final_verdict=verdict)


def test_allowed_route_sends_its_bin():
    assert choose_commands([judged(ROUTE_A, Allow())]) == (["BIN A"], "ALLOW A")


def test_one_denied_action_blocks_the_whole_plan():
    commands, lcd = choose_commands([judged(ROUTE_A, Allow()), judged(PRIV, DENY)])
    assert commands == ["DENY"]
    assert "routing-operator-only" in lcd


def test_hold_verdict_parks_the_parcel():
    assert choose_commands([judged(ROUTE_A, HOLD)])[0] == ["HOLD"]


def test_empty_or_ambiguous_plan_holds():
    assert choose_commands([])[0] == ["HOLD"]
    assert choose_commands([judged(ROUTE_A, Allow()), judged(ROUTE_A, Allow())])[0] == ["HOLD"]


def test_granted_privileged_action_runs_before_routing():
    assert choose_commands([judged(ROUTE_A, Allow()), judged(PRIV, Allow())])[0] == ["PRIV OPEN", "BIN A"]


def test_review_escalates_allow_to_hold():
    verdict = escalate_verdict(Allow(), ReasoningReview(obeys_scene_text=True, quote="the note says bin B"))
    assert verdict.kind == "hold"
    assert verdict.rule == "reasoning-check"


def test_review_never_lowers_a_verdict():
    assert escalate_verdict(DENY, ReasoningReview(obeys_scene_text=False, quote="")) == DENY


def test_missing_review_fails_closed():
    assert escalate_verdict(Allow(), None).kind == "hold"


def test_clean_review_keeps_allow():
    assert escalate_verdict(Allow(), ReasoningReview(obeys_scene_text=False, quote="")).kind == "allow"
