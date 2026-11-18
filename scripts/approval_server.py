"""Local approval receiver. Zero deps. Stands in for n8n when Docker is down.
POST JSON to http://127.0.0.1:5679/triage -> appends to reports/approvals.jsonl
Run: python scripts/approval_server.py [--port 5679]
"""
import argparse, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

class H(BaseHTTPRequestHandler):
    out = Path("reports/approvals.jsonl")
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode() if n else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw": body}
        self.out.parent.mkdir(parents=True, exist_ok=True)
        with open(self.out, "a") as f:
            f.write(json.dumps(data) + "\n")
        msg = json.dumps({"status": "held-for-approval", "got": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5679)
    args = ap.parse_args()
    print(f"approval server on http://127.0.0.1:{args.port}/triage (Ctrl+C to stop)", flush=True)
    HTTPServer(("127.0.0.1", args.port), H).serve_forever()
