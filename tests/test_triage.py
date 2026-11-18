import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triage import score_heuristic, notify_n8n

class TestTriage(unittest.TestCase):
    def test_dark_scores_zero(self):
        p = Path(__file__).resolve().parents[1] / "evidence" / "dark.png"
        r = score_heuristic(p)
        self.assertEqual(r["score"], 0.0)
        self.assertEqual(r["method"], "heuristic")

    def test_notify_skipped_without_webhook(self):
        self.assertEqual(notify_n8n("", {"a": 1}), "skipped-no-webhook")

    def test_notify_fails_gracefully(self):
        s = notify_n8n("http://127.0.0.1:9/nope", {"a": 1})
        self.assertTrue(s.startswith("webhook-failed"))

if __name__ == "__main__":
    unittest.main()
