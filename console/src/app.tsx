import { useRef, useState } from "react";
import { FrameView } from "./decision/frame-view";
import { ObservationTable } from "./decision/observation-table";
import { VerdictPanel } from "./decision/verdict-panel";
import { LedgerList } from "./ledger/ledger-list";
import { SamplePicker } from "./station/sample-picker";
import { StatusBar } from "./station/status-bar";
import type { PipelineMode } from "./station/use-station";
import { useStation } from "./station/use-station";
import { TaskPanel } from "./task/task-panel";

export const App = () => {
  const { state, isDeciding, failure, requestDecision, decideSample, choosePipeline, simulateArrival, grantOnce } =
    useStation();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);
  const upload = useRef<HTMLInputElement>(null);

  if (!state) return <div className="boot mono">connecting to station...</div>;
  const decision = state.decisions.find((d) => d.id === selectedId) ?? state.decisions.at(-1);

  return (
    <div className="shell">
      <StatusBar state={state} />
      <div className="controls">
        <SamplePicker onPick={decideSample} isDisabled={isDeciding} />
        {!state.public && (
          <>
            <button onClick={() => requestDecision()} disabled={isDeciding}>{isDeciding ? "Deciding..." : "Capture and decide"}</button>
            {state.station === "simulated" && <button onClick={simulateArrival} disabled={isDeciding}>Simulate arrival</button>}
            <button onClick={() => upload.current?.click()} disabled={isDeciding}>Upload frame</button>
            <select className={`mono pipeline pipeline-${state.pipeline}`} value={state.pipeline}
              onChange={(e) => void choosePipeline(e.target.value as PipelineMode)}>
              <option value="paperweight">pipeline: paperweight</option>
              <option value="no-defense">pipeline: no defense (demo)</option>
              <option value="hijacked-planner">pipeline: hijacked planner (demo)</option>
            </select>
          </>
        )}
        {state.public && <span className="muted small">Read-only demo replaying recorded Nemotron calls. The live station runs locally.</span>}
        <input ref={upload} type="file" accept="image/jpeg" hidden
          onChange={(e) => { const file = e.target.files?.[0]; if (file) void requestDecision(file); e.target.value = ""; }} />
        {failure && <span className="failure mono">{failure.message}</span>}
      </div>
      <main className="layout">
        <section className="panel scene">
          <h2>Scene {decision && <span className="mono muted small">frame {decision.frame_sha.slice(0, 12)}</span>}</h2>
          {decision ? (
            <>
              <FrameView decision={decision} focusId={focusId} onFocus={setFocusId} />
              <ObservationTable decision={decision} focusId={focusId} onFocus={setFocusId} />
            </>
          ) : (
            <p className="muted">No decisions yet. Put a parcel on the tray or upload a frame.</p>
          )}
        </section>
        <div className="side">
          {decision && <VerdictPanel decision={decision} />}
          <TaskPanel task={state.task} onGrant={grantOnce} isReadOnly={state.public} />
          <LedgerList decisions={state.decisions} selectedId={decision?.id ?? null} onSelect={setSelectedId} />
        </div>
      </main>
    </div>
  );
};
