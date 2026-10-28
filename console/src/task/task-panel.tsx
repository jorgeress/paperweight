import { useState } from "react";
import type { Grant, OperatorTask } from "../decision/types";

type Props = { task: OperatorTask; onGrant: (grant: Grant) => void; isReadOnly: boolean };

export const TaskPanel = ({ task, onGrant, isReadOnly }: Props) => {
  const [cage, setCage] = useState("R1");
  return (
    <section className="panel task">
      <h2>Operator task <span className="origin-operator mono small">origin operator</span></h2>
      <table className="params">
        <tbody>
          {Object.entries(task.routing).map(([value, bin]) => (
            <tr key={value}><td className="mono muted">{task.route_slot}</td><td className="mono">{value}</td><td className="mono strong">bin {bin}</td></tr>
          ))}
          {task.routing_default && (
            <tr><td className="mono muted">{task.route_slot}</td><td className="mono">any other</td><td className="mono strong">bin {task.routing_default}</td></tr>
          )}
        </tbody>
      </table>
      <p className="small"><span className="label">actions</span> <span className="mono">{task.allowed_actions.join(", ")}</span></p>
      <p className="small"><span className="label">privileged</span> <span className="mono">{task.privileged_actions.join(", ") || "none"}</span></p>
      {task.instructions && <p className="small"><span className="label">notes</span> {task.instructions}</p>}
      {!isReadOnly && task.privileged_actions.includes("priv_open") && (
        <form className="grant" onSubmit={(e) => { e.preventDefault(); onGrant({ kind: "priv_open", params: { cage } }); }}>
          <span className="label">one-shot grant</span>
          <span className="mono">priv_open cage=</span>
          <input className="mono" value={cage} onChange={(e) => setCage(e.target.value.toUpperCase())} maxLength={8} />
          <button type="submit">Grant once</button>
        </form>
      )}
      {task.grants.map((g, i) => (
        <p key={i} className="mono small grant-live">grant pending: {g.kind} {Object.entries(g.params).map(([k, v]) => `${k}=${v}`).join(" ")}</p>
      ))}
    </section>
  );
};
