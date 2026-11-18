# vision-triage-ops
Open-vocab visual anomaly triage with human approval.

One-command run:
  docker compose up --build
  python src/triage.py --input evidence --out reports/run.json

Local demo without docker:
  pip install -r requirements.txt
  python src/triage.py --input evidence --out reports/run.json

How it works: docs/arch.mmd
Evidence: evidence/ (screenshots)
Report: reports/run.json

Eval (MVP heuristic):
  score = variance + bright-fraction. Threshold 0.5 default.
  Replace score_image() with Grounding-DINO + CLIP later.

Failure cases logged in reports/run.json (needs_approval flag).
No autonomous action without n8n approval.
