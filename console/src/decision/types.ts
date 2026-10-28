export type RuleId =
  | "action-in-task"
  | "citation-mismatch"
  | "privileged-operator-only"
  | "routing-operator-only"
  | "scene-slot-domain"
  | "slot-conflict"
  | "parcel-condition"
  | "reasoning-check";

export type RuleHit = { rule: RuleId; severity: "hold" | "deny"; reason: string };

export type Verdict =
  | { kind: "allow" }
  | { kind: "hold"; rule: RuleId; reason: string; hits: RuleHit[] }
  | { kind: "deny"; rule: RuleId; reason: string; hits: RuleHit[] };

export type Observation = {
  id: string;
  kind: "label_field" | "free_text" | "object";
  field: string | null;
  text: string;
  bbox: [number, number, number, number];
};

export type CitedValue = { value: string; cite: string };

export type ProposedAction = { kind: "route" | "hold" | "priv_open"; params: Record<string, CitedValue> };

export type JudgedAction = { action: ProposedAction; policy_verdict: Verdict; final_verdict: Verdict };

export type StageCost = {
  stage: string;
  model: string;
  latency_ms: number;
  tokens_in: number;
  tokens_out: number;
  replayed: boolean;
};

export type Grant = { kind: ProposedAction["kind"]; params: Record<string, string> };

export type OperatorTask = {
  allowed_actions: ProposedAction["kind"][];
  privileged_actions: ProposedAction["kind"][];
  slots: { name: string; domain: string[] | null }[];
  route_slot: string;
  routing: Record<string, "A" | "B" | "C">;
  routing_default: "A" | "B" | "C" | null;
  grants: Grant[];
  instructions: string;
};

export type Decision = {
  id: string;
  at: string;
  frame_sha: string;
  task: OperatorTask;
  pipeline: "paperweight" | "no-defense" | "hijacked-planner";
  observations: Observation[];
  judged: JudgedAction[];
  reasoning: string;
  review: { obeys_scene_text: boolean; quote: string } | null;
  commands: string[];
  lcd: string;
  consumed_grants: Grant[];
  stages: StageCost[];
  error: string | null;
};

export type Outcome = "allow" | "hold" | "deny";

export const outcomeOf = (decision: Decision): Outcome => {
  if (decision.commands.includes("DENY")) return "deny";
  if (decision.commands.includes("HOLD")) return "hold";
  return "allow";
};

export const citedIds = (decision: Decision): Set<string> =>
  new Set(decision.judged.flatMap((j) => Object.values(j.action.params).map((p) => p.cite)));
