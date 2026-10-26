import type { Decision } from "./types";
import { citedIds } from "./types";

type Props = { decision: Decision; focusId: string | null; onFocus: (id: string | null) => void };

export const ObservationTable = ({ decision, focusId, onFocus }: Props) => {
  const cited = citedIds(decision);
  return (
    <table className="grid">
      <thead>
        <tr><th>id</th><th>origin</th><th>kind</th><th>field</th><th>text</th></tr>
      </thead>
      <tbody>
        {decision.observations.map((o) => (
          <tr key={o.id} className={`${cited.has(o.id) ? "row-cited" : ""} ${focusId === o.id ? "row-focus" : ""}`}
            onMouseEnter={() => onFocus(o.id)} onMouseLeave={() => onFocus(null)}>
            <td className="mono">{o.id}</td>
            <td className="mono muted">scene</td>
            <td className={`mono kind-${o.kind}`}>{o.kind}</td>
            <td className="mono">{o.field ?? ""}</td>
            <td className="mono text">{o.text}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
