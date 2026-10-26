import type { Decision } from "../decision/types";
import { outcomeOf } from "../decision/types";

type Props = { decisions: Decision[]; selectedId: string | null; onSelect: (id: string) => void };

export const LedgerList = ({ decisions, selectedId, onSelect }: Props) => (
  <section className="panel ledger">
    <h2>Ledger</h2>
    <ol>
      {[...decisions].reverse().map((d) => {
        const outcome = outcomeOf(d);
        const fired = d.judged.map((j) => j.final_verdict).find((v) => v.kind !== "allow");
        const rule = fired && "rule" in fired ? fired.rule : "";
        return (
          <li key={d.id} className={d.id === selectedId ? "selected" : ""} onClick={() => onSelect(d.id)}>
            <span className="mono muted">{d.at.slice(11, 19)}</span>
            <span className={`tag tag-${outcome}`}>{outcome}</span>
            <span className="mono">{d.commands.join("+")}</span>
            <span className="mono muted ellipsis">{rule}</span>
          </li>
        );
      })}
    </ol>
  </section>
);
