# vision-triage-ops
Open-vocab visual anomaly triage with human approval gate.

Pipeline: ingest image -> score 0..1 -> Gemini explain (optional) -> n8n approval if flagged -> run.json + markdown report.

Run locally (Windows, no Docker needed):
  pip install -r requirements.txt
  python scripts/run_demo.py
  python -m pytest tests/ -q

Run with options:
  python src/triage.py --input evidence --out reports/run.json --threshold 0.5
  python src/triage.py --input evidence --out reports/run.json --use-clip --labels defect,normal
  set N8N_WEBHOOK=http://localhost:5678/webhook/vision-triage for live approval posts

Run with Docker (needs Docker Desktop running):
  docker compose up --build

Real detector upgrade (optional, heavy):
  pip install torch transformers
  then --use-clip works without fallback.

Gemini explain (optional, lean API path):
  copy .env.example to .env, set GEMINI_API_KEY
  from src.explain import explain_image

Files:
  src/triage.py - heuristic + CLIP hook + webhook gate
  src/explain.py - Gemini vision explain, skips without key
  scripts/run_demo.py - one-command end-to-end + markdown report
  n8n/approval-workflow.json - import into n8n, webhook path /vision-triage
  docs/arch.mmd - architecture diagram

Eval: reports/run-report.md after demo.
Failure cases: webhook-failed means n8n down (graceful). heuristic-fallback means torch missing (graceful).
Rule: no autonomous action without human approval.
