import { useCallback, useEffect, useState } from "react";
import type { Decision, Grant, OperatorTask } from "../decision/types";

export type StationState = {
  task: OperatorTask;
  mode: "live" | "record" | "replay";
  station: "serial" | "simulated";
  camera: string;
  second_layer: boolean;
  public: boolean;
  pipeline: PipelineMode;
  decisions: Decision[];
};

export type PipelineMode = "paperweight" | "no-defense" | "hijacked-planner";

type Failure = { message: string; at: number };

const readDetail = async (response: Response): Promise<string> => {
  const body = await response.json().catch(() => ({}));
  return typeof body.detail === "string" ? body.detail : `${response.status} ${response.statusText}`;
};

export const useStation = () => {
  const [state, setState] = useState<StationState | null>(null);
  const [isDeciding, setIsDeciding] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);

  const refreshState = useCallback(async () => {
    const response = await fetch("/api/state");
    if (!response.ok) return setFailure({ message: await readDetail(response), at: Date.now() });
    setState(await response.json());
  }, []);

  useEffect(() => {
    void refreshState();
    const events = new EventSource("/api/events");
    events.addEventListener("decision", (event) => {
      const decision: Decision = JSON.parse((event as MessageEvent).data);
      setState((s) => (s ? { ...s, decisions: [...s.decisions.slice(-49), decision], task: decision.task } : s));
      void refreshState();
    });
    return () => events.close();
  }, [refreshState]);

  const post = useCallback(async (path: string, init: RequestInit) => {
    setFailure(null);
    const response = await fetch(path, { method: "POST", ...init });
    if (!response.ok) setFailure({ message: await readDetail(response), at: Date.now() });
    return response.ok;
  }, []);

  const requestDecision = useCallback(
    async (frame?: Blob) => {
      setIsDeciding(true);
      await post("/api/decide", frame ? { body: frame, headers: { "content-type": "image/jpeg" } } : {});
      setIsDeciding(false);
    },
    [post],
  );

  const decideSample = useCallback(
    async (sampleId: string) => {
      setIsDeciding(true);
      await post(`/api/samples/${sampleId}/decide`, {});
      setIsDeciding(false);
    },
    [post],
  );

  const choosePipeline = useCallback(
    async (mode: PipelineMode) => {
      setFailure(null);
      const response = await fetch("/api/pipeline", {
        method: "PUT",
        body: JSON.stringify({ mode }),
        headers: { "content-type": "application/json" },
      });
      if (!response.ok) return setFailure({ message: await readDetail(response), at: Date.now() });
      await refreshState();
    },
    [refreshState],
  );

  const simulateArrival = useCallback(() => post("/api/arrival", {}), [post]);

  const grantOnce = useCallback(
    async (grant: Grant) => {
      const json = { body: JSON.stringify(grant), headers: { "content-type": "application/json" } };
      if (await post("/api/grants", json)) await refreshState();
    },
    [post, refreshState],
  );

  return { state, isDeciding, failure, requestDecision, decideSample, choosePipeline, simulateArrival, grantOnce };
};
