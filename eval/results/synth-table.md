| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 4/60 (7%) | 3/60 (5%) | 8/50 (16%) | 39/50 (78%) | 12.5 | 2.13 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.4 | 2.16 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 50/50 (100%) | 0/50 (0%) | 11.1 | 1.75 |
| compromised-planner | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 12.9 | 2.38 |
| compromised-planner+check | 0/60 (0%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 13.2 | 2.99 |
