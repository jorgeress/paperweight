from paperweight.policy.verdict import Hold, RuleHit, Verdict
from paperweight.reasoning_check.review import ReasoningReview


def escalate_verdict(verdict: Verdict, review: ReasoningReview | None) -> Verdict:
    # note: the second layer can only raise allow to hold; it never lowers a verdict
    if verdict.kind != "allow":
        return verdict
    if review is None:
        hit = RuleHit(rule="reasoning-check", severity="hold", reason="reasoning review unavailable")
        return Hold(rule=hit.rule, reason=hit.reason, hits=(hit,))
    if not review.obeys_scene_text:
        return verdict
    hit = RuleHit(rule="reasoning-check", severity="hold", reason=f"planner reasoning follows scene text: {review.quote!r}")
    return Hold(rule=hit.rule, reason=hit.reason, hits=(hit,))
