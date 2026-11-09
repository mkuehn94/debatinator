"""Live proof-of-concept: PC audio → faster-whisper → LLM counter-arguments → SSE (for the Tauri overlay).

    python live/server.py                 # capture system audio (PulseAudio/PipeWire monitor of default sink)
    python live/server.py --file x.wav    # replay a file in real time instead (testing)

Env:
    WHISPER_MODEL  (large-v3-turbo)  WHISPER_DEVICE (cuda)  LANG_STT (de)
    LLM_URL        (http://127.0.0.1:8097/v1/chat/completions)  — start with scripts/serve-llm.sh
    PORT           (8765)  → GET /events (text/event-stream)
    BUCH_BIN       optional path to llm-buch's `buch` binary → passages + citations grounding the counters; BUCH_K (3)
"""
import argparse, json, os, queue, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import requests

SR = 16000
FRAME = SR * 30 // 1000            # 30 ms frames for the energy VAD
SILENCE_END = 0.7                  # s of silence that closes an utterance
MIN_UTT, MAX_UTT = 1.5, 12.0       # s; MAX caps music/background-noise that never goes quiet
MIN_WORDS = 8                      # accumulate transcript until a claim is plausible

LLM_URL = os.environ.get("LLM_URL", "http://127.0.0.1:8097/v1/chat/completions")

SYSTEM = (
    "Du bist ein schneller Debatten-Assistent. Du bekommst ein Transkript-Stück (automatisch erkannt, kann Fehler haben) "
    "und den vorherigen Kontext. Bestimme die zentrale Behauptung des letzten Stücks und liefere genau drei "
    "Gegenargumente, die sich deutlich voneinander unterscheiden (z.B. Gegenbeispiel, Rückfrage, andere Gewichtung). "
    "Jedes Gegenargument höchstens 20 Wörter, direkt aussprechbar, auf Deutsch. "
    "Wenn das Stück keine strittige Behauptung enthält (Begrüßung, Moderation, Füllwörter), gib claim als leeren String "
    "und args als leere Liste zurück."
)
SYSTEM_SOURCES = (
    " Die Behauptung (claim) kommt ausschließlich aus dem letzten Stück des Sprechers. Zusätzlich bekommst du Passagen aus einer Bibliothek. Stütze Gegenargumente auf diese Passagen, wenn sie "
    "wirklich passen, und hänge dann die Quelle exakt wie angegeben in eckigen Klammern an, z.B. [Hoppe: Titel, S. 34]. "
    "Erfinde keine Quellen und keine Zitate; passt keine Passage, argumentiere ohne Quelle."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "args": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": ["claim", "args"],
}


# ---------- event bus (SSE) ----------
clients: list[queue.Queue] = []
clients_lock = threading.Lock()


def emit(kind: str, **data):
    msg = json.dumps({"type": kind, "t": time.time(), **data}, ensure_ascii=False)
    print(f"[{kind}] {msg[:160]}", flush=True)
    with clients_lock:
        for q in clients:
            q.put(msg)


class SSE(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path != "/events":
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        q: queue.Queue = queue.Queue()
        with clients_lock:
            clients.append(q)
        try:
            self.wfile.write(b": hello\n\n"); self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=15)
                    self.wfile.write(f"data: {msg}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with clients_lock:
                clients.remove(q)


# ---------- audio capture + VAD segmentation ----------
def source_cmd(file: str | None) -> list[str]:
    raw = ["-f", "s16le", "-ac", "1", "-ar", str(SR), "-"]
    if file:
        return ["ffmpeg", "-loglevel", "error", "-re", "-i", file, *raw]
    # PipeWire/PulseAudio: monitor of the default output = "what the PC plays"
    return ["parec", "--device=@DEFAULT_MONITOR@", "--format=s16le", f"--rate={SR}", "--channels=1", "--raw"]


def capture(file: str | None, out: queue.Queue):
    proc = subprocess.Popen(source_cmd(file), stdout=subprocess.PIPE)
    buf, silence, noise = [], 0, 1e-4
    while True:
        b = proc.stdout.read(FRAME * 2)
        if len(b) < FRAME * 2:
            break
        f = np.frombuffer(b, np.int16).astype(np.float32) / 32768
        rms = float(np.sqrt(np.mean(f * f)) + 1e-9)
        noise = min(rms, noise * 1.002)   # noise floor: drops instantly, rises slowly (~2x per 11 s)
        speech = rms > max(noise * 3, 0.005)
        if speech or buf:
            buf.append(f)
        silence = 0 if speech else silence + 1
        dur = len(buf) * FRAME / SR
        if buf and (silence * FRAME / SR >= SILENCE_END or dur >= MAX_UTT):
            if dur >= MIN_UTT:
                out.put(np.concatenate(buf))
            buf, silence = [], 0
    if buf:
        out.put(np.concatenate(buf))
    out.put(None)


# ---------- STT ----------
def stt(audio_q: queue.Queue, text_q: queue.Queue):
    from faster_whisper import WhisperModel
    name = os.environ.get("WHISPER_MODEL", "large-v3-turbo")
    device = os.environ.get("WHISPER_DEVICE", "cuda")
    model = WhisperModel(name, device=device, compute_type="float16" if device == "cuda" else "int8")
    emit("status", msg=f"STT ready ({name}/{device})")
    lang = os.environ.get("LANG_STT", "de")
    while (a := audio_q.get()) is not None:
        t = time.perf_counter()
        segs, _ = model.transcribe(a, language=lang, beam_size=1, vad_filter=True, condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segs).strip()
        if text:
            emit("transcript", text=text, ms=round((time.perf_counter() - t) * 1000))
            text_q.put(text)
    text_q.put(None)


# ---------- optional retrieval: llm-buch (github.com/Red-fuchs/llm-buch) ----------
class Buch:
    """Persistent `buch serve` process: JSON line {"q","k"} in → {"hits":[{citation,text,url..}],"ms"} out."""

    def __init__(self, bin_path: str, k: int):
        self.k = k
        self.p = subprocess.Popen([bin_path, "serve"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def search(self, q: str) -> tuple[list[dict], float]:
        self.p.stdin.write(json.dumps({"q": q, "k": self.k}, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError("buch serve exited")
        r = json.loads(line)
        if r.get("error"):
            raise RuntimeError(r["error"])
        return r["hits"], r["ms"]


def make_buch() -> Buch | None:
    b = os.environ.get("BUCH_BIN")
    if not b:
        return None
    buch = Buch(b, int(os.environ.get("BUCH_K", 3)))
    buch.search("Test")   # warm-up: loads index + e5 model before the first real query
    emit("status", msg=f"llm-buch ready (k={buch.k})")
    return buch


# ---------- LLM ----------
def counter(text_q: queue.Queue):
    buch = make_buch()
    history: list[str] = []
    pending = ""
    while True:
        item = text_q.get()
        if item is None:
            return
        pending = f"{pending} {item}".strip()
        # drain: if STT outran the LLM, merge everything that queued up (latest wins, no backlog)
        while not text_q.empty():
            nxt = text_q.get()
            if nxt is None:
                return
            pending = f"{pending} {nxt}"
        if len(pending.split()) < MIN_WORDS:
            continue
        chunk, pending = pending, ""
        ctx = " ".join(history[-3:])
        history.append(chunk)
        t = time.perf_counter()
        hits, rag_ms, system, user = [], 0.0, SYSTEM, f"Kontext: {ctx or '-'}\n\nLetztes Stück: {chunk}"
        if buch:
            try:
                hits, rag_ms = buch.search(chunk)
            except Exception as e:
                emit("error", msg=f"buch: {e}")
            if hits:
                system += SYSTEM_SOURCES
                user += ("\n\nPassagen (NUR Material für Gegenargumente, NICHT die Behauptung des Sprechers):\n"
                         + "\n\n".join(f"{h['citation']}\n{h['text'][:600]}" for h in hits))
        try:
            r = requests.post(LLM_URL, timeout=30, json={
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7, "max_tokens": 300,
                "response_format": {"type": "json_object", "schema": SCHEMA},
            })
            r.raise_for_status()
            out = json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            emit("error", msg=f"LLM: {e}")
            continue
        if out.get("claim") and out.get("args"):
            emit("counter", claim=out["claim"], args=out["args"][:3], source=chunk,
                 refs=[{"citation": h["citation"], "url": h.get("url")} for h in hits],
                 rag_ms=round(rag_ms), ms=round((time.perf_counter() - t) * 1000))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="replay an audio file in real time instead of capturing system audio")
    args = ap.parse_args()

    port = int(os.environ.get("PORT", 8765))
    srv = ThreadingHTTPServer(("127.0.0.1", port), SSE)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"SSE on http://127.0.0.1:{port}/events", flush=True)

    audio_q, text_q = queue.Queue(), queue.Queue()
    threading.Thread(target=stt, args=(audio_q, text_q), daemon=True).start()
    threading.Thread(target=capture, args=(args.file, audio_q), daemon=True).start()
    try:
        counter(text_q)
        emit("status", msg="source ended")
        time.sleep(2)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
