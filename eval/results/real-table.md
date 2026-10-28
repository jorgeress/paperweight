| Config | Attack success | Attacked parcel still routed right | Legit label tasks correct | Unneeded holds | p50 latency (s) | USD per 1k parcels |
|---|---|---|---|---|---|---|
| no-defense | 3/17 (18%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 5.4 | 1.11 |
| prompt-defense | 0/17 (0%) | 17/17 (100%) | 14/14 (100%) | 0/14 (0%) | 6.5 | 0.85 |
| text-masking | 1/17 (6%) | 2/17 (12%) | 0/14 (0%) | 14/14 (100%) | 12.2 | 2.02 |
| paperweight | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 10.1 | 2.23 |
| paperweight-no-check | 0/17 (0%) | 14/17 (82%) | 14/14 (100%) | 0/14 (0%) | 9.8 | 1.81 |
| compromised-planner | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.2 | 2.3 |
| compromised-planner+check | 0/17 (0%) | 8/17 (47%) | 14/14 (100%) | 0/14 (0%) | 16.6 | 2.88 |
