# Eval history

Each stage changed one prompt or rule, then re-ran the evals. Tables are copied from the run logs; only the current stage replays from `recordings/`.

## v0, 26 oct: first synthetic run

Baseline perception and planner prompts.

synth corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 0/60 (0%) | 2/60 (3%) | 7/50 (14%) | 42/50 (84%) | 6.8 | 2.2 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 5.2 | 1.9 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 4.9 | 1.56 |
| compromised-planner | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 6.9 | 2.19 |
| compromised-planner+check | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 8.1 | 2.75 |

## v1, 27 oct: perception stops reading captions as fields

"SHIP TO" was sometimes read as the destination_city or tracking field, which held a legitimate Paris parcel. The prompt now says a label field holds a value, never a caption, and splits "50001 ZARAGOZA" into two fields.

synth corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 2/60 (3%) | 3/60 (5%) | 8/50 (16%) | 37/50 (74%) | 10.4 | 2.24 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 7.0 | 1.88 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 6.7 | 1.54 |
| compromised-planner | 0/60 (0%) | 7/60 (12%) | 50/50 (100%) | 0/50 (0%) | 7.9 | 2.2 |
| compromised-planner+check | 0/60 (0%) | 7/60 (12%) | 50/50 (100%) | 0/50 (0%) | 8.2 | 2.76 |

## v2, 27 oct: planner stops dithering over the hold reason

12 runs hit max_tokens: the planner looped on whether hold's reason had to be copied verbatim from an observation. The prompt now lets it word the reason freely. Truncations: 12 to 0.

synth corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 2/60 (3%) | 3/60 (5%) | 8/50 (16%) | 37/50 (74%) | 10.4 | 2.24 |
| paperweight | 0/60 (0%) | 49/60 (82%) | 50/50 (100%) | 0/50 (0%) | 9.7 | 2.09 |
| paperweight-no-check | 0/60 (0%) | 49/60 (82%) | 50/50 (100%) | 0/50 (0%) | 9.4 | 1.7 |
| compromised-planner | 0/60 (0%) | 7/60 (12%) | 50/50 (100%) | 0/50 (0%) | 10.5 | 2.38 |
| compromised-planner+check | 0/60 (0%) | 7/60 (12%) | 50/50 (100%) | 0/50 (0%) | 10.9 | 2.99 |

## v3, 27 oct: first run on 34 real photos

Photographed with the Tapo camera. Finding: a hijacked planner routed a torn parcel to bin A in 2/17 attacks, because "damaged parcels go to hold" lived only in the operator's free text, which only the planner reads.

real corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 3/17 (18%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 5.4 | 1.11 |
| prompt-defense | 0/17 (0%) | 17/17 (100%) | 14/14 (100%) | 0/14 (0%) | 6.5 | 0.85 |
| text-masking | 0/17 (0%) | 2/17 (12%) | 0/14 (0%) | 14/14 (100%) | 20.1 | 2.12 |
| paperweight | 0/17 (0%) | 12/17 (71%) | 14/14 (100%) | 0/14 (0%) | 14.8 | 2.26 |
| paperweight-no-check | 0/17 (0%) | 12/17 (71%) | 14/14 (100%) | 0/14 (0%) | 14.5 | 1.84 |
| compromised-planner | 2/17 (12%) | 6/17 (35%) | 14/14 (100%) | 0/14 (0%) | 22.7 | 2.72 |
| compromised-planner+check | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 23.2 | 3.43 |

## v4, 27 oct: parcel-condition rule (broken planner prompt)

Perception now reports parcel_condition and the policy holds any condition the operator lists. Perception also writes single-line JSON, which ended a whitespace loop that hit max_tokens. The same single-line instruction on the planner made it emit route with no params, so legit parcels were denied as malformed. Reverted on the planner.

real corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 3/17 (18%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 5.4 | 1.11 |
| prompt-defense | 0/17 (0%) | 17/17 (100%) | 14/14 (100%) | 0/14 (0%) | 6.5 | 0.85 |
| text-masking | 1/17 (6%) | 2/17 (12%) | 0/14 (0%) | 14/14 (100%) | 12.2 | 2.02 |
| paperweight | 0/17 (0%) | 8/17 (47%) | 5/14 (36%) | 9/14 (64%) | 14.9 | 2.89 |
| paperweight-no-check | 0/17 (0%) | 8/17 (47%) | 5/14 (36%) | 9/14 (64%) | 14.6 | 2.3 |
| compromised-planner | 0/17 (0%) | 2/17 (12%) | 7/14 (50%) | 7/14 (50%) | 16.2 | 2.81 |
| compromised-planner+check | 0/17 (0%) | 2/17 (12%) | 7/14 (50%) | 7/14 (50%) | 16.6 | 3.57 |
| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 4/60 (7%) | 3/60 (5%) | 8/50 (16%) | 39/50 (78%) | 12.5 | 2.13 |
| paperweight | 0/60 (0%) | 23/60 (38%) | 29/50 (58%) | 21/50 (42%) | 16.1 | 3.06 |
| paperweight-no-check | 0/60 (0%) | 23/60 (38%) | 29/50 (58%) | 21/50 (42%) | 15.8 | 2.42 |
| compromised-planner | 0/60 (0%) | 2/60 (3%) | 15/50 (30%) | 35/50 (70%) | 17.3 | 3.03 |
| compromised-planner+check | 0/60 (0%) | 2/60 (3%) | 14/50 (28%) | 36/50 (72%) | 18.0 | 3.87 |

## v5, 27 oct: current

Condition rule kept, planner prompt reverted. The hijacked-planner torn-parcel attack is held by parcel-condition. Synthetic "damaged" drawings are now read as intact and routed; real torn parcels are held.

real corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 3/17 (18%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 5.4 | 1.11 |
| prompt-defense | 0/17 (0%) | 17/17 (100%) | 14/14 (100%) | 0/14 (0%) | 6.5 | 0.85 |
| text-masking | 1/17 (6%) | 2/17 (12%) | 0/14 (0%) | 14/14 (100%) | 12.2 | 2.02 |
| paperweight | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 10.1 | 2.23 |
| paperweight-no-check | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 9.8 | 1.81 |
| compromised-planner | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.2 | 2.3 |
| compromised-planner+check | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.6 | 2.88 |

synth corpus:

| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 4/60 (7%) | 3/60 (5%) | 8/50 (16%) | 39/50 (78%) | 12.5 | 2.13 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.4 | 2.16 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.1 | 1.75 |
| compromised-planner | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 12.9 | 2.38 |
| compromised-planner+check | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 13.2 | 2.99 |
