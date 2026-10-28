# Paperweight

A piece of paper shouldn't be able to command your robot.

Paperweight sits between a vision-language model and the hardware it controls. Text
the camera reads can fill in a value the operator's task declares, such as a parcel's
destination. It can never change the goal, the routing or who is in charge. Every
action parameter has to cite where it came from, and a deterministic policy checks
those citations before anything reaches the actuator.

<!-- todo: demo gif of the real station -->

**Try it:** <!-- todo: hosted read-only demo url --> (replays recorded Nemotron calls,
no key needed). Pick a recorded frame and switch the pipeline to `no defense` or
`hijacked planner` to see the same frame without Paperweight. The live station runs
locally, see [Run locally](#run-locally).

Built for the Nebius x NVIDIA Global AI Hackathon (October 2026), Physical AI track.

## Vocabulary

| Term | Meaning |
|---|---|
| operator task | What the operator typed: allowed actions, slots, routing, one-shot grants |
| observation | Something the camera saw: a label field, free text or an object, with an id |
| scene text | Any text read from the camera image. Never trusted as an instruction |
| slot | A value the task declares and scene text may fill, such as `destination_city` |
| citation | The observation id or `operator` that an action parameter comes from |
| origin | `operator` or `scene` |
| verdict | `allow`, `hold` or `deny`, with the rule that fired |
| station | The Arduino that executes allowed actions |
| hold | Park the parcel for a human. Always safe |

## Why

In 2026, several papers showed that printed text in a robot's camera view can redirect
VLM-controlled robots (CHAI, PPIA, "Hijacking Robots with a Piece of Paper"). The
strongest defense they found is masking all text in the image, but that breaks any task
that has to read a label. On our 34 real parcel photos, masking still let 1 of 17
attacks through and sorted 0 of 14 legitimate parcels.

## How it works

```
camera frame ─> perception (Super-VL, thinking off) ─> observations obs-1..n   origin: scene
operator task ─────────────────────────────────────> slots, routing, grants   origin: operator
observations + task ─> planner (Super-VL, thinking on) ─> actions, every param cited
actions ─> policy (deterministic, 7 rules) ─> verdict per action
planner reasoning ─> reasoning check (Lightning) ─> may raise allow to hold, never lowers
verdicts ─> station link (single exit, serial) ─> Arduino: gate servo, LEDs, buzzer, LCD
everything ─> ledger (jsonl) ─> console (SSE)
```

The model never assigns observation ids, so a citation can only point at something
perception actually transcribed. The planner never sees the image.

| Rule | Outcome | Stops |
|---|---|---|
| `action-in-task` | deny | actions or params the operator never declared |
| `citation-mismatch` | deny | a value that is not in the cited observation (whole normalized tokens), or a value claiming `operator` that the task never declares |
| `privileged-operator-only` | deny | a privileged action (open the restricted cage) with any scene-cited param, or without a matching one-shot operator grant |
| `routing-operator-only` | deny | a bin that does not match the operator's routing for the cited destination |
| `scene-slot-domain` | hold | a slot filled from free text (a loose note) instead of the label field, or outside its domain |
| `slot-conflict` | hold | two label fields for the same slot that disagree (a forged label stuck next to the real one) |
| `parcel-condition` | hold | routing a parcel whose condition (damaged, open, wet) the operator wants held. Condition is judged from how the parcel looks, never from text |

All rules run on every action and deny beats hold. If any action in a plan is denied,
the whole parcel goes to `DENY` (parked, alarm): a plan that tried something forbidden
is not trusted for anything else. Any stage error or timeout fails closed to `HOLD`.

## Models

| Stage | Model on Nebius Token Factory | Why this one |
|---|---|---|
| Perception | `nvidia/Nemotron-3.5-Super-VL` | Reads labels and gives usable bounding boxes (0-1000). Thinking off: ~1.5 s per frame |
| Planner | `nvidia/Nemotron-3.5-Super-VL` | Text only here. Thinking on, because the reasoning is audited |
| Reasoning check | `nvidia/Nemotron-3_5-Lightning` | ~0.3 s to audit the planner's `reasoning_content` |

All calls use `response_format` with a JSON schema, temperature 0, and are recorded so
the eval and the hosted demo can replay them after the models change.

## Threat model

In scope: anything visible to the camera. Printed notes, signs, stickers, a forged
label next to the real one, text claiming to be the operator or a supervisor, requests
for the privileged action. We assume the attacker controls scene text but not the
operator console, the task file or the station firmware.

Out of scope: an attacker who replaces the only label on a parcel (no vision system
can tell, and damage is bounded to the declared bins), physical tampering with the
station, and attacks on the operator.

## Results

Two corpora, same task in every config. Reproduce with
`uv run python -m eval.run_eval --corpus eval/corpus/real` (or `.../synth`); it replays
the recorded calls by default, so it costs nothing and needs no key.

**Real photos:** 34 frames of real parcels taken with the station camera (a Tapo over
RTSP). 17 legitimate (12 plain, 3 damaged or covered that must be held, 2 with a
harmless handling note) and 17 attacks: conflicting instructions, forged labels, signage, task
redefinition, fake authority and privileged requests, all printed on paper.

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 3/17 (18%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 5.4 | 1.11 |
| prompt-defense | 0/17 (0%) | 17/17 (100%) | 14/14 (100%) | 0/14 (0%) | 6.5 | 0.85 |
| text-masking | 1/17 (6%) | 2/17 (12%) | 0/14 (0%) | 14/14 (100%) | 12.2 | 2.02 |
| paperweight | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 10.1 | 2.23 |
| paperweight-no-check | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 9.8 | 1.81 |
| compromised-planner | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.2 | 2.3 |
| compromised-planner+check | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.6 | 2.88 |

**Synthetic:** 120 generated frames, 60 legitimate and 60 attacks across the same
categories.

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 4/60 (7%) | 3/60 (5%) | 8/50 (16%) | 39/50 (78%) | 12.5 | 2.13 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.4 | 2.16 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.1 | 1.75 |
| compromised-planner | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 12.9 | 2.38 |
| compromised-planner+check | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 13.2 | 2.99 |

- **compromised-planner** tells the planner to obey scene notes and to pick whatever
  citations will pass the check: a stand-in for an injection that already worked. The
  policy alone keeps attack success at 0% on both corpora. The parcels it does not route
  are parked (`DENY` or `HOLD`), never misrouted.
- **prompt-defense** (a system prompt that says to ignore scene instructions) blocked all
  17 real attacks and routed every attacked parcel right, better than Paperweight there,
  and it is cheaper. On the synthetic corpus it let 4 of 60 through. The difference is what happens when the model is fooled anyway: a prompt has
  nothing behind it, the policy does (see compromised-planner).
- **Adaptive attacker** (`uv run python -m eval.adaptive_attacker --corpus ...`): for every
  attack frame we generated every action that would reach the attacker's goal, with every
  possible citation (each observation id and `operator`) on every parameter. 159,325
  forged actions on the synthetic corpus and 39,113 on the real one; 0 reached the station.
- **Reasoning check** (Lightning): with the planner hijacked, it flagged the reasoning on
  44 of 60 synthetic attacks and 7 of 17 real ones, and raised no flag on any of the 77
  legitimate frames in either corpus. The policy had already stopped every one of those
  attacks, so it works as an alarm, not as an extra block.
- Paperweight holds forged-label parcels on purpose (`slot-conflict`): 3 of the 17 real
  attacks and 10 of the 60 synthetic ones. That is why "still routed right" is below 100%.
- Evals changed one prompt or rule at a time. Every stage and its tables are in
  [`eval/results/history.md`](eval/results/history.md).

## Run locally

```sh
uv sync && (cd console && npm ci && npm run build)
cp .env.example .env   # add NEBIUS_API_KEY; leave STATION_PORT empty for the simulated station
uv run uvicorn paperweight.server.app:app --port 8765   # open http://localhost:8765
```

Firmware: `firmware/station/station.ino` for an Arduino Uno. Wiring and the serial
protocol are below. `uv run pytest` runs the policy tests.

`PAPERWEIGHT_MAX_LIVE_CALLS` (default 200) caps paid model calls per process. Past it every
parcel fails closed to `HOLD` until the server restarts.

### Station protocol

Line-based ASCII over USB serial at 115200 baud.

| Host to station | Station to host |
|---|---|
| `PING` | `READY` on boot, `PONG` |
| `BIN A` / `BIN B` / `BIN C` | `OK <command>` |
| `HOLD`, `DENY` | `ERR <reason>` |
| `PRIV OPEN` | `ARRIVAL <cm>`, `DEPARTURE` |
| `LCD <text>` | |

<!-- todo: wiring table and photo -->

## Limitations

- Perception is a model too. It can be wrong about what is a label field, and a sheet
  that looks exactly like a label is classified as one. `slot-conflict` catches it only
  when the real label is also in view.
- One real parcel had its city half covered by a folded sheet and perception completed
  "RID" to "MADRID", so it was routed instead of held. Perception reads what it expects.
- Drawn damage on synthetic frames is read as intact, so "damaged goes to hold" is
  only exercised on real photos (3 frames).
- About 10 s per decision (p50) on the real photos, most of it the planner reasoning.
  Fine for a station that waits for a parcel, too slow for a moving belt.
- With thinking on, the planner can reason past `max_tokens`; that fails closed to
  `HOLD`. It happened 12 times before the planner prompt was fixed and 0 times in the
  current runs. The cut is recorded, so replays show the same error.
- When the reasoning check times out (6 s cap) the parcel is held. During live testing
  two Lightning calls in a row stalled and two legitimate parcels were held.
- Models can be retired on Token Factory without a redirect. The recorded calls keep
  the eval and the demo reproducible, but live use needs the exact model IDs above.

## AI tools used

<!-- todo: ai tools used -->

## License

Apache-2.0
