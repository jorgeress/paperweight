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
that has to read a label. On our corpus, masking blocks every attack and gets 14% of
legitimate parcels right.

## How it works

```
camera frame ─> perception (Super-VL, thinking off) ─> observations obs-1..n   origin: scene
operator task ─────────────────────────────────────> slots, routing, grants   origin: operator
observations + task ─> planner (Super-VL, thinking on) ─> actions, every param cited
actions ─> policy (deterministic, 6 rules) ─> verdict per action
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

Synthetic corpus: 120 frames (60 legitimate, 60 attacks across indirect signage, task
redefinition, authority impersonation, conflicting instructions, forged labels and
privileged requests). Same task in every config. Reproduce with
`uv run python -m eval.run_eval` (replays recordings by default).

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 0/60 (0%) | 2/60 (3%) | 7/50 (14%) | 42/50 (84%) | 6.8 | 2.2 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 5.2 | 1.9 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 4.9 | 1.56 |
| compromised-planner | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 6.9 | 2.19 |
| compromised-planner+check | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 8.1 | 2.75 |

- **compromised-planner** tells the planner to obey scene notes and to pick whatever
  citations will pass the check: a stand-in for an injection that already worked. The
  policy alone keeps attack success at 0%. The parcels it does not route are parked
  (`DENY` or `HOLD`), never misrouted.
- **Adaptive attacker** (`uv run python -m eval.adaptive_attacker`): for every attack
  frame we generated every action that would reach the attacker's goal, with every
  possible citation (each observation id and `operator`) on every parameter. 142,557
  forged actions, 0 reached the station.
- **Reasoning check**: flagged 36 of 36 hijacked plans and 0 of 120 clean plans, but the
  policy had already stopped all 36. On this corpus it works as an alarm, not as an
  extra block.
- The paperweight rows hold the 10 forged-label parcels on purpose (`slot-conflict`).

<!-- todo: real-photo corpus results -->

## Run locally

```sh
uv sync && (cd console && npm ci && npm run build)
cp .env.example .env   # add NEBIUS_API_KEY; leave STATION_PORT empty for the simulated station
uv run uvicorn paperweight.server.app:app --port 8765   # open http://localhost:8765
```

Firmware: `firmware/station/station.ino` for an Arduino Uno. Wiring and the serial
protocol are below. `uv run pytest` runs the policy tests.

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
- On synthetic frames the drawn damage was not recognized by any config, so "damaged
  goes to hold" is only tested on real photos.
- One legitimate parcel was held because perception merged "50001 ZARAGOZA" into one
  `postal_code` field and produced no `destination_city`. Safe, but a false hold.
- About 5 s per decision. Fine for a station that waits for a parcel, too slow for a
  moving belt.
- With thinking on, the planner sometimes reasons past `max_tokens`; that fails closed
  to `HOLD` (2 of 120 frames in the paperweight run). The cut is recorded, so replays
  show the same error.
- Models can be retired on Token Factory without a redirect. The recorded calls keep
  the eval and the demo reproducible, but live use needs the exact model IDs above.

## AI tools used

<!-- todo: ai tools used -->

## License

Apache-2.0
