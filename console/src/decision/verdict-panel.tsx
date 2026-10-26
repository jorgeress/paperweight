import type { Decision, JudgedAction, Verdict } from "./types";
import { outcomeOf } from "./types";

const VerdictTag = ({ verdict }: { verdict: Verdict }) => (
  <span className={`tag tag-${verdict.kind}`}>{verdict.kind}{verdict.kind !== "allow" ? ` ${verdict.rule}` : ""}</span>
);

const ActionRow = ({ judged, decision }: { judged: JudgedAction; decision: Decision }) => {
  const { action, policy_verdict: policy, final_verdict: final } = judged;
  return (
    <div className="action">
      <div className="action-head">
        <span className="mono strong">{action.kind}</span>
        <VerdictTag verdict={final} />
        {final.kind !== policy.kind && <span className="muted small">policy said {policy.kind}, escalated</span>}
      </div>
      <table className="params">
        <tbody>
          {Object.entries(action.params).map(([name, cited]) => {
            const source = decision.observations.find((o) => o.id === cited.cite);
            return (
              <tr key={name}>
                <td className="mono muted">{name}</td>
                <td className="mono strong">{cited.value}</td>
                <td className="mono">
                  <span className={cited.cite === "operator" ? "origin-operator" : "origin-scene"}>{cited.cite}</span>
                  {source && <span className="muted"> {source.kind} "{source.text}"</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {final.kind !== "allow" &&
        final.hits.map((hit, i) => (
          <div key={i} className={`hit hit-${hit.severity}`}>
            <span className="mono">{hit.rule}</span> {hit.reason}
          </div>
        ))}
    </div>
  );
};

export const VerdictPanel = ({ decision }: { decision: Decision }) => {
  const outcome = outcomeOf(decision);
  const decisive = decision.judged.find((j) => j.final_verdict.kind === outcome)?.final_verdict;
  return (
    <section className="panel verdict">
      <div className={`outcome outcome-${outcome}`}>
        <span className="outcome-word">{outcome}</span>
        <span className="mono">station {decision.commands.join(" + ")}</span>
      </div>
      {decisive && decisive.kind !== "allow" && (
        <p className="decisive"><span className="mono">{decisive.rule}</span> {decisive.reason}</p>
      )}
      {decision.error && <p className="hit hit-hold">fail-closed: {decision.error}</p>}
      {decision.judged.length === 0 && !decision.error && (
        <p className="hit hit-deny">no defense: the model chose {decision.commands.join(" + ")} straight from the image, nothing was checked</p>
      )}
      {decision.judged.map((j, i) => <ActionRow key={i} judged={j} decision={decision} />)}
      {decision.review && (
        <div className="review">
          <span className="label">reasoning check</span>
          <span className={decision.review.obeys_scene_text ? "tag tag-hold" : "tag tag-allow"}>
            {decision.review.obeys_scene_text ? "follows scene text" : "clean"}
          </span>
          {decision.review.quote && <q className="muted">{decision.review.quote}</q>}
        </div>
      )}
      <table className="stages">
        <tbody>
          {decision.stages.map((s) => (
            <tr key={s.stage}>
              <td className="mono">{s.stage}</td>
              <td className="mono muted">{s.model.replace("nvidia/", "")}</td>
              <td className="mono num">{(s.latency_ms / 1000).toFixed(2)} s</td>
              <td className="mono num muted">{s.tokens_in}/{s.tokens_out} tok</td>
              <td className="mono muted">{s.replayed ? "replay" : "live"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};
