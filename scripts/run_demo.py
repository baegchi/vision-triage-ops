"""One-command demo: ensure evidence, run triage, write markdown report."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
REP = ROOT / "reports"

def ensure_evidence():
    EV.mkdir(exist_ok=True)
    if not list(EV.glob("*.png")):
        from PIL import Image
        import numpy as np
        rng = np.random.default_rng(0)
        Image.fromarray((rng.random((200, 200)) * 255).astype("uint8")).save(EV / "noisy.png")
        Image.new("L", (200, 200), color=30).save(EV / "dark.png")
        print("created sample evidence")

def main():
    ensure_evidence()
    REP.mkdir(exist_ok=True)
    out = REP / "run.json"
    r = subprocess.run([sys.executable, str(ROOT / "src" / "triage.py"),
                        "--input", str(EV), "--out", str(out), "--threshold", "0.5"],
                       capture_output=True, text=True)
    print(r.stdout[-2000:])
    data = json.loads(out.read_text())
    md = ["# run report", f"threshold={data['threshold']} method={data['method']} count={data['count']}", "",
          "| file | score | method | needs_approval | notify |", "|---|---|---|---|---|"]
    for x in data["results"]:
        md.append(f"| {x['file']} | {x.get('score')} | {x.get('method')} | {x.get('needs_approval')} | {x.get('notify')} |")
    md += ["", "## failure cases", "- webhook-failed = n8n not running (expected locally). Start n8n + set N8N_WEBHOOK to clear.",
           "- heuristic-fallback-no-clip-deps = torch/transformers not installed. pip install torch transformers for real CLIP."]
    (REP / "run-report.md").write_text("\n".join(md))
    print("wrote reports/run.json + reports/run-report.md")

if __name__ == "__main__":
    main()
