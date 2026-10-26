import type { StationState } from "./use-station";

export const StatusBar = ({ state }: { state: StationState }) => (
  <header className="status">
    <span className="brand">PAPERWEIGHT</span>
    <span className="muted">scene text fills slots, never commands</span>
    <span className="spacer" />
    <span className="mono">station <b className={state.station === "serial" ? "ok" : "warn"}>{state.station}</b></span>
    <span className="mono">models <b className={state.mode === "replay" ? "warn" : "ok"}>{state.mode}</b></span>
    <span className="mono">camera <b>{state.camera}</b></span>
    <span className="mono">second layer <b>{state.second_layer ? "on" : "off"}</b></span>
  </header>
);
