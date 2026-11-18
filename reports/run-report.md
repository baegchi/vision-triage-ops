# vision-triage-ops run report
threshold=0.5 method=heuristic count=3
flagged=1 approvals_received=1

| file | score | method | needs_approval | notify | explanation |
|---|---|---|---|---|---|
| bright-defect.png | 1.0 | heuristic | True | posted-200 | skipped-no-key |
| dark.png | 0.0 | heuristic | False | not-needed | skipped-no-key |
| noisy.png | 0.093 | heuristic | False | not-needed | skipped-no-key |

## approval queue (reports/approvals.jsonl)
Each flagged image POSTed here for human Approve/Reject.
n8n path: import n8n/approval-workflow.json, set N8N_WEBHOOK to n8n URL instead.

## failure modes (all graceful)
- notify posted-200 = approval server got it.
- webhook-failed = receiver down (triaging still completes).
- heuristic-fallback-no-clip-deps = torch missing; pip install torch transformers for real CLIP.