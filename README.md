# vision-triage-ops
Open-vocab visual anomaly triage with human approval gate. Fully runnable, zero heavy deps.

Pipeline: ingest -> score 0..1 -> Gemini explain (optional) -> approval POST if flagged -> run.json + run-report.md.

Quickstart (Windows / Linux, no Docker needed):
  pip install -r requirements.txt
  python scripts/run_demo.py --threshold 0.5
  python -m unittest discover tests -v

What the demo does:
  1. ensures evidence/ incl. bright-defect.png (flagged sample, score 1.0)
  2. starts local approval server on 127.0.0.1:5679 (stdlib, no n8n needed)
  3. runs src/triage.py with --webhook to that server
  4. calls Gemini explain per image (skips as skipped-no-key without GEMINI_API_KEY)
  5. writes reports/run.json + reports/run-report.md + reports/approvals.jsonl

Last verified run: 3 images, 1 flagged (bright-defect.png posted-200), 3/3 tests OK.

Options:
  python src/triage.py --input evidence --out reports/run.json --threshold 0.5 --webhook http://127.0.0.1:5679/triage
  python src/triage.py --input evidence --out reports/run.json --use-clip --labels defect,normal
  python scripts/approval_server.py --port 5679

Upgrades (all optional, all degrade gracefully):
  pip install torch transformers -> real CLIP instead of heuristic-fallback
  set GEMINI_API_KEY -> real vision explanations instead of skipped-no-key
  Docker Desktop up -> docker compose up --build (triage + n8n)
  n8n -> import n8n/approval-workflow.json, set N8N_WEBHOOK to n8n URL

Files:
  src/triage.py, src/explain.py, scripts/run_demo.py, scripts/approval_server.py
  tests/test_triage.py, n8n/approval-workflow.json, docs/arch.mmd, .github/workflows/ci.yml

Rule: no autonomous action without human approval.
