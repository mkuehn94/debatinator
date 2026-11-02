"""Real debate: diarized speaker turns + YouTube json3 caption words → d1 per turn.
usage: python eval/turns.py data/<name>.json3 data/<name>.turns.json [out.json] [--skip-intro 116]"""
import json, sys
from collections import Counter
from d1client import ask, wait
from taxonomy import MAIN, POSITIVE, MAIN_MIN_P, POSITIVE_MIN_P

SKIP_INTRO_SECONDS = 116  # default: skip before this timestamp

cap, tj = sys.argv[1], sys.argv[2]
out_path = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else tj.replace(".turns.json", ".labels.json")

# parse optional skip time
skip_intro = SKIP_INTRO_SECONDS
if '--skip-intro' in sys.argv:
    idx = sys.argv.index('--skip-intro')
    skip_intro = float(sys.argv[idx + 1])

turns = [t for t in json.load(open(tj)) if t["start"] >= skip_intro]
j = json.load(open(cap))
words = [((e["tStartMs"] + s.get("tOffsetMs", 0)) / 1000, s["utf8"].strip())
         for e in j["events"] if "segs" in e for s in e["segs"] if s.get("utf8", "").strip()]
spk_of = lambda t: next((u["spk"] for u in turns if u["start"] - 0.3 <= t <= u["end"] + 0.3), None)

segs = []  # words → merged speaker turns
for t, w in words:
    s = spk_of(t) or (segs[-1]["spk"] if segs else None)
    if segs and segs[-1]["spk"] == s: segs[-1]["text"] += " " + w; segs[-1]["end"] = t
    else: segs.append({"spk": s, "start": t, "end": t, "text": w})
dur = Counter(); [dur.update({s["spk"]: s["end"] - s["start"]}) for s in segs if s["spk"]]
mod = min((k for k in dur if k is not None), key=dur.get) if dur else None  # moderator = least talk time; skipped
segs = [s for s in segs if s["spk"] and len(s["text"].split()) >= 6]

wait()
out, ms, last_mod = [], [], ""
for s in segs:
    if s["spk"] == mod: last_mod = s["text"]; continue
    other = next((p for p in reversed(out) if p["spk"] != s["spk"]), None)
    a = other["text"] if other else last_mod
    ans, t = ask(f"A: {a[-900:]}\n\nB: {s['text'][:1500]}", {"m": MAIN, **POSITIVE}); ms.append(t)
    raw = ans["m"]["value"]; p = ans["m"]["probabilities"][raw]
    out.append({**s, "label": raw if raw == "sachlich" or p >= MAIN_MIN_P else "sachlich", "raw": raw, "p": round(p, 2),
                **{k: round(ans[k]["p"], 2) for k in POSITIVE}})

print("moderator", mod, "| turns", len(out), "| median ms", round(sorted(ms)[len(ms) // 2]))
print("labels:", dict(Counter(o["label"] for o in out)))
for o in out:
    if o["label"] != "sachlich" or any(o[k] >= POSITIVE_MIN_P for k in POSITIVE):
        print(f"\n[{int(o['start']) // 60:02d}:{int(o['start']) % 60:02d}] {o['spk']} {o['label']} p={o['p']} " +
              " ".join(f"{k}={o[k]}" for k in POSITIVE) + f"\n  {o['text'][:300]}")
json.dump({"moderator": mod, "turns": out}, open(out_path, "w"), ensure_ascii=False, indent=1)
