from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triage import score_heuristic

def test_heuristic_dark():
    p = Path(__file__).resolve().parents[1] / "evidence" / "dark.png"
    r = score_heuristic(p)
    assert r["score"] == 0.0, r
    assert r["method"] == "heuristic"
