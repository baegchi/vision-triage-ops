# run report
threshold=0.5 method=heuristic count=2

| file | score | method | needs_approval | notify |
|---|---|---|---|---|
| dark.png | 0.0 | heuristic | False | not-needed |
| noisy.png | 0.093 | heuristic | False | not-needed |

## failure cases
- webhook-failed = n8n not running (expected locally). Start n8n + set N8N_WEBHOOK to clear.
- heuristic-fallback-no-clip-deps = torch/transformers not installed. pip install torch transformers for real CLIP.