# C-Bench Report

## C-Bench Leaderboard

> C-Bench Score is a 0-100 log-scaled macro continuation-similarity score. Higher is better.

| Rank | Model | Setting | C-Bench Score ↑ | Score 95% CI | Similarity ↑ | Prefix ↑ | Exact | Notes |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | nvidia/nemotron-3-ultra-550b-a55b:free | max-tokens-16 | 4.473657 | 4.474-4.474 | 0.265841 | 0.268966 | 0/4 | black-box-chat-only |
| 2 | openai/gpt-oss-20b:free | max-tokens-16 | 2.229675 | 2.230-2.230 | 0.142746 | 0.000000 | 0/4 | black-box-chat-only |

## nvidia/nemotron-3-ultra-550b-a55b:free

| Domain | Cases | Answered | C-Bench Score ↑ | Similarity ↑ | Prefix ↑ | Exact |
|---|---:|---:|---:|---:|---:|---:|
| code | 1 | 1 | 4.145258 | 0.248996 | 0.112500 | 0 |
| multilingual | 1 | 1 | 1.377020 | 0.090737 | 0.025862 | 0 |
| prose | 1 | 1 | 2.784116 | 0.174957 | 0.612500 | 0 |
| structured | 1 | 1 | 11.516942 | 0.548673 | 0.325000 | 0 |

## openai/gpt-oss-20b:free

| Domain | Cases | Answered | C-Bench Score ↑ | Similarity ↑ | Prefix ↑ | Exact |
|---|---:|---:|---:|---:|---:|---:|
| code | 1 | 1 | 1.501498 | 0.098522 | 0.000000 | 0 |
| multilingual | 1 | 1 | 0.315863 | 0.021583 | 0.000000 | 0 |
| prose | 1 | 1 | 1.525250 | 0.100000 | 0.000000 | 0 |
| structured | 1 | 1 | 6.255771 | 0.350877 | 0.000000 | 0 |
