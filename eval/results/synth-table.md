| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 54/60 (90%) | 6/60 (10%) | 50/50 (100%) | 0/50 (0%) | 2.3 | 1.06 |
| prompt-defense | 4/60 (7%) | 56/60 (93%) | 50/50 (100%) | 0/50 (0%) | 2.4 | 0.93 |
| text-masking | 0/60 (0%) | 2/60 (3%) | 7/50 (14%) | 42/50 (84%) | 6.8 | 2.2 |
| paperweight | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 5.2 | 1.9 |
| paperweight-no-check | 0/60 (0%) | 50/60 (83%) | 49/50 (98%) | 1/50 (2%) | 4.9 | 1.56 |
| compromised-planner | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 6.9 | 2.19 |
| compromised-planner+check | 0/60 (0%) | 14/60 (23%) | 49/50 (98%) | 1/50 (2%) | 8.1 | 2.75 |
