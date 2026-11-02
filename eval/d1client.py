"""Thin client for d1 decision models, same interface for both backends.

D1_URL = http://127.0.0.1:8095/v1/decisions   (mlx-vlm server --decision-model, macOS)
       = http://127.0.0.1:8096/v1/systemone   (llama.cpp llama-server, Win/Linux/macOS)
"""
import os, time, requests

URL = os.environ.get("D1_URL", "http://127.0.0.1:8095/v1/decisions")


def _norm(a: dict) -> dict:
    # mlx-vlm: {value, probabilities} / {probability};  llama.cpp: {choice, probabilities} / {noul}
    if "noul" in a or a.get("type") in ("noul", "bool"):
        return {"p": a.get("noul", a.get("probability"))}
    return {"value": a.get("choice", a.get("value")), "probabilities": a.get("probabilities", {})}


def ask(state: str, questions: dict) -> tuple[dict, float]:
    """→ ({qid: {"p"} | {"value","probabilities"}}, ms)"""
    t = time.perf_counter()
    r = requests.post(URL, json={"state": state, "questions": questions}, timeout=300)
    r.raise_for_status()
    return {k: _norm(v) for k, v in r.json()["answers"].items()}, (time.perf_counter() - t) * 1000


def wait(sec: int = 120):
    print(f"waiting for d1 server at {URL}...", end="", flush=True)
    for i in range(sec):
        try:
            requests.get(URL, timeout=1)
            print(f" ✓ ready in {i}s")
            return
        except requests.RequestException:
            if (i + 1) % 10 == 0:
                print(f" ({i}s)", end="", flush=True)
            time.sleep(1)
    print(f"\n✗ server not reachable after {sec}s")
    raise SystemExit(f"no d1 server at {URL}\n\nstart it with: bash scripts/serve-d1-llamacpp.sh -c 2048 -ub 2048")
