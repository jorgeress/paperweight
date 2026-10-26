import type { Decision } from "./types";
import { citedIds } from "./types";

type Props = { decision: Decision; focusId: string | null; onFocus: (id: string | null) => void };

export const FrameView = ({ decision, focusId, onFocus }: Props) => {
  const cited = citedIds(decision);
  return (
    <div className="frame">
      <img src={`/api/frames/${decision.frame_sha}.jpg`} alt={`camera frame ${decision.frame_sha.slice(0, 8)}`} />
      <svg viewBox="0 0 1000 1000" preserveAspectRatio="none">
        {decision.observations
          .filter((o) => o.kind !== "object")
          .map((o) => {
            const [x0, y0, x1, y1] = o.bbox;
            const tone = cited.has(o.id) ? "cited" : o.kind === "free_text" ? "scene" : "label";
            return (
              <g key={o.id} className={`box box-${tone} ${focusId === o.id ? "box-focus" : ""}`}
                onMouseEnter={() => onFocus(o.id)} onMouseLeave={() => onFocus(null)}>
                <rect x={x0} y={y0} width={x1 - x0} height={y1 - y0} vectorEffect="non-scaling-stroke" />
              </g>
            );
          })}
      </svg>
      <div className="frame-tags">
        {decision.observations
          .filter((o) => o.kind !== "object" && (cited.has(o.id) || focusId === o.id))
          .map((o) => (
            <span key={o.id} className="frame-tag" style={{ left: `${o.bbox[0] / 10}%`, top: `${o.bbox[1] / 10}%` }}>
              {o.id}
            </span>
          ))}
      </div>
    </div>
  );
};
