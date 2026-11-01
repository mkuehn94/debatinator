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
    for _ in range(sec):
        try:
            requests.get(URL, timeout=1); return
        except requests.RequestException:
            time.sleep(1)
    raise SystemExit(f"no d1 server at {URL}")
