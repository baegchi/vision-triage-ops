"""Vision triage ops - heuristic + optional CLIP zero-shot + n8n gate.
Contract: image -> {score 0..1, needs_approval} -> webhook POST if flagged.
Lean default: heuristic only (no torch needed).
Real detector: pip install torch transformers && --use-clip --labels "defect,fire,leak,normal"
"""
import argparse, json, os, urllib.request
from pathlib import Path
from PIL import Image
import numpy as np

def score_heuristic(p: Path) -> dict:
    img = Image.open(p).convert("L").resize((128, 128))
    a = np.asarray(img, dtype=float) / 255.0
    var = float(a.var())
    bright = float((a > 0.9).mean())
    score = min(1.0, var * 4.0 + bright * 2.0)
    return {"file": p.name, "score": round(score, 3), "method": "heuristic",
            "var": round(var, 4), "bright_frac": round(bright, 4)}

_clip_cache = {}
def score_clip(p: Path, labels: list[str]) -> dict:
    try:
        from transformers import CLIPProcessor, CLIPModel
        import torch
    except ImportError as e:
        r = score_heuristic(p)
        r["method"] = "heuristic-fallback-no-clip-deps"
        r["clip_error"] = f"pip install torch transformers ({e})"
        return r
    key = "model"
    if key not in _clip_cache:
        m = "openai/clip-vit-base-patch32"
        _clip_cache[key] = (CLIPModel.from_pretrained(m), CLIPProcessor.from_pretrained(m))
    model, proc = _clip_cache[key]
    img = Image.open(p).convert("RGB")
    inputs = proc(text=labels, images=img, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model(**inputs)
        probs = out.logits_per_image.softmax(dim=1)[0].tolist()
    # anomaly score = 1 - P(normal) if 'normal' in labels else max prob
    if "normal" in labels:
        score = 1.0 - probs[labels.index("normal")]
    else:
        score = max(probs)
    top = labels[int(np.argmax(probs))]
    return {"file": p.name, "score": round(float(score), 3), "method": "clip",
            "top_label": top, "probs": {l: round(float(x), 3) for l, x in zip(labels, probs)}}

def notify_n8n(webhook_url: str, payload: dict) -> str:
    if not webhook_url:
        return "skipped-no-webhook"
    try:
        req = urllib.request.Request(webhook_url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return f"posted-{r.status}"
    except Exception as e:
        return f"webhook-failed: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="reports/run.json")
    ap.add_argument("--threshold", type=float, default=float(os.getenv("THRESHOLD", "0.5")))
    ap.add_argument("--use-clip", action="store_true")
    ap.add_argument("--labels", default=os.getenv("CLIP_LABELS", "defect,normal"))
    ap.add_argument("--webhook", default=os.getenv("N8N_WEBHOOK", ""))
    args = ap.parse_args()
    labels = [s.strip() for s in args.labels.split(",") if s.strip()]
    in_dir = Path(args.input)
    imgs = sorted([p for p in in_dir.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")])
    results = []
    for p in imgs:
        try:
            r = score_clip(p, labels) if args.use_clip else score_heuristic(p)
        except Exception as e:
            r = {"file": p.name, "score": 0.0, "method": "error", "error": str(e)}
        r["needs_approval"] = r.get("score", 0) >= args.threshold
        if r["needs_approval"]:
            r["notify"] = notify_n8n(args.webhook, {"file": r["file"], "score": r["score"], "method": r.get("method")})
        else:
            r["notify"] = "not-needed"
        results.append(r)
    out = {"threshold": args.threshold, "method": "clip" if args.use_clip else "heuristic",
           "labels": labels, "count": len(results), "results": results}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
