"""Optional Gemini vision explanation. Lean: API-based, no local GPU.
Skips gracefully when GEMINI_API_KEY is missing.
Uses OpenAI-compatible endpoint: https://generativelanguage.googleapis.com/v1beta/openai/
"""
import base64, json, os, urllib.request
from pathlib import Path

def explain_image(image_path: str, score: float, model: str | None = None) -> dict:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return {"status": "skipped-no-key", "text": ""}
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    prompt = f"This image got anomaly score {score}. Describe in 2 sentences what looks anomalous, if anything."
    body = {"model": model, "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}]}
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read().decode())
        return {"status": "ok", "text": out["choices"][0]["message"]["content"][:800]}
    except Exception as e:
        return {"status": f"failed: {e}", "text": ""}
