"""One-command demo: evidence (incl. flagged sample), local approval server,
triage run with webhook + Gemini explain stub, markdown report. Zero heavy deps.
Usage: python scripts/run_demo.py [--threshold 0.5]
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
REP = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))

def ensure_evidence():
    EV.mkdir(exist_ok=True)
    from PIL import Image
    import numpy as np
    rng = np.random.default_rng(0)
    if not (EV / "dark.png").exists():
        Image.new("L", (200, 200), color=30).save(EV / "dark.png")
    if not (EV / "noisy.png").exists():
        Image.fromarray((rng.random((200, 200)) * 255).astype("uint8")).save(EV / "noisy.png")
    # flagged sample: half bright white -> bright_frac ~0.5 -> score 1.0
    b = (EV / "bright-defect.png")
    if not b.exists():
        a = np.full((200, 200), 30, dtype="uint8")
        a[:, 100:] = 255
        Image.fromarray(a).save(b)
        print("created bright-defect.png (flagged sample)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()
    ensure_evidence()
    REP.mkdir(exist_ok=True)
    for f in ["run.json", "approvals.jsonl"]:
        try:
            (REP / f).unlink()
        except FileNotFoundError:
            pass
    # start local approval server (no docker/n8n needed)
    srv = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "approval_server.py"), "--port", "5679"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    webhook = "http://127.0.0.1:5679/triage"
    try:
        r = subprocess.run([sys.executable, str(ROOT / "src" / "triage.py"),
                            "--input", str(EV), "--out", str(REP / "run.json"),
                            "--threshold", str(args.threshold), "--webhook", webhook],
                           capture_output=True, text=True, timeout=60)
        print(r.stdout[-3000:])
        if r.returncode != 0:
            print(r.stderr[-1000:])
            raise SystemExit(r.returncode)
        # gemini explain per file (skips gracefully without key)
        from explain import explain_image
        data = json.loads((REP / "run.json").read_text())
        for x in data["results"]:
            e = explain_image(str(EV / x["file"]), x.get("score", 0))
            x["explanation"] = e.get("status", "")
        (REP / "run.json").write_text(json.dumps(data, indent=2))
        appr = []
        if (REP / "approvals.jsonl").exists():
            appr = [json.loads(l) for l in (REP / "approvals.jsonl").read_text().splitlines() if l.strip()]
        md = ["# vision-triage-ops run report", f"threshold={data['threshold']} method={data['method']} count={data['count']}",
              f"flagged={sum(1 for x in data['results'] if x.get('needs_approval'))} approvals_received={len(appr)}", "",
              "| file | score | method | needs_approval | notify | explanation |",
              "|---|---|---|---|---|---|"]
        for x in data["results"]:
            md.append(f"| {x['file']} | {x.get('score')} | {x.get('method')} | {x.get('needs_approval')} | {x.get('notify')} | {x.get('explanation','')} |")
        md += ["", "## approval queue (reports/approvals.jsonl)", "Each flagged image POSTed here for human Approve/Reject.",
               "n8n path: import n8n/approval-workflow.json, set N8N_WEBHOOK to n8n URL instead.", "",
               "## failure modes (all graceful)", "- notify posted-200 = approval server got it.",
               "- webhook-failed = receiver down (triaging still completes).",
               "- heuristic-fallback-no-clip-deps = torch missing; pip install torch transformers for real CLIP."]
        (REP / "run-report.md").write_text("\n".join(md))
        print(f"OK: {data['count']} images, {len(appr)} approvals received. reports/run-report.md written.")
    finally:
        srv.terminate()

if __name__ == "__main__":
    main()
