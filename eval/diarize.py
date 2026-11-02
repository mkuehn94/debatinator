"""pyannote community-1 diarization → turns.json [{start,end,spk}] (exclusive). usage: diarize.py audio.wav turns.json [n_speakers]"""
import json, sys, torch, soundfile as sf, os
from pyannote.audio import Pipeline
wav, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None
p = Pipeline.from_pretrained("pyannote/speaker-diarization-community-1", token=os.getenv("HF_TOKEN"))
p.to(torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"))
x, sr = sf.read(wav, dtype="float32")
res = p({"waveform": torch.from_numpy(x)[None], "sample_rate": sr}, num_speakers=n)
dia = getattr(res, "exclusive_speaker_diarization", res)
turns = [{"start": round(s.start, 2), "end": round(s.end, 2), "spk": k} for s, _, k in dia.itertracks(yield_label=True)]
json.dump(turns, open(out, "w"), indent=0)
from collections import Counter
c = Counter(); [c.update({t["spk"]: t["end"] - t["start"]}) for t in turns]
print(len(turns), "turns", {k: round(v) for k, v in c.items()})
