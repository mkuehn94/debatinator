"""
Get debate exchanges with actual text from captions.

Usage:
  python extract_exchanges.py turns.json captions.json3 output.json [--skip-intro 116] [--min-duration 3.0]
"""

import json
import sys

SKIP_INTRO_SECONDS = 116  # default: skip first 1:56
MIN_DURATION_SECONDS = 3.0  # filter out short segments

# load youtube captions and get word timestamps
def load_captions(path):
    data = json.load(open(path))
    words = []

    for event in data.get('events', []):
        if 'segs' not in event:
            continue
        base_ms = event['tStartMs']

        for seg in event['segs']:
            word = seg.get('utf8', '').strip()
            if word:
                offset_ms = seg.get('tOffsetMs', 0)
                time_sec = (base_ms + offset_ms) / 1000.0
                words.append((time_sec, word))

    return words

# get text for a time range
def get_text(start, end, words):
    bits = []
    for time, word in words:
        if start <= time <= end:
            bits.append(word)
    return ' '.join(bits)

# main
if len(sys.argv) < 4:
    print("Usage: python extract_exchanges.py turns.json captions.json3 output.json [--skip-intro 116] [--min-duration 3.0]")
    sys.exit(1)

turns_file = sys.argv[1]
captions_file = sys.argv[2]
output_file = sys.argv[3]

# parse optional args
skip_intro = SKIP_INTRO_SECONDS
min_duration = MIN_DURATION_SECONDS

if '--skip-intro' in sys.argv:
    idx = sys.argv.index('--skip-intro')
    skip_intro = float(sys.argv[idx + 1])

if '--min-duration' in sys.argv:
    idx = sys.argv.index('--min-duration')
    min_duration = float(sys.argv[idx + 1])

print("Loading captions...")
caption_words = load_captions(captions_file)
print(f"  {len(caption_words)} words")

print("Loading turns...")
all_turns = json.load(open(turns_file))

print(f"Filtering: skip first {skip_intro}s, keep segments >= {min_duration}s")

# filter: after skip time, at least min duration
turns = []
for t in all_turns:
    duration = t['end'] - t['start']
    if t['start'] >= skip_intro and duration >= min_duration:
        turns.append(t)

print(f"  {len(turns)} turns kept")

# find the two main speakers
speaker_time = {}
for t in turns:
    who = t['spk']
    if who not in speaker_time:
        speaker_time[who] = 0
    speaker_time[who] += t['end'] - t['start']

sorted_speakers = sorted(speaker_time.items(), key=lambda x: x[1], reverse=True)
speaker_a = sorted_speakers[0][0]
speaker_b = sorted_speakers[1][0]

print(f"Main speakers: {speaker_a} ({speaker_time[speaker_a]:.0f}s), {speaker_b} ({speaker_time[speaker_b]:.0f}s)")

# keep only main speakers
main_turns = [t for t in turns if t['spk'] in [speaker_a, speaker_b]]
print(f"  {len(main_turns)} turns from main speakers")

# find exchanges (statement -> response pairs)
exchanges = []
for i in range(len(main_turns) - 1):
    curr = main_turns[i]
    nxt = main_turns[i+1]

    if curr['spk'] != nxt['spk']:  # speaker changed
        gap = nxt['start'] - curr['end']

        statement_txt = get_text(curr['start'], curr['end'], caption_words)
        response_txt = get_text(nxt['start'], nxt['end'], caption_words)

        exchanges.append({
            'statement': {
                'speaker': curr['spk'],
                'start': curr['start'],
                'end': curr['end'],
                'duration': round(curr['end'] - curr['start'], 1),
                'text': statement_txt
            },
            'response': {
                'speaker': nxt['spk'],
                'start': nxt['start'],
                'end': nxt['end'],
                'duration': round(nxt['end'] - nxt['start'], 1),
                'text': response_txt
            },
            'gap': round(gap, 1)
        })

print(f"\nFound {len(exchanges)} exchanges")

# save
result = {
    'speaker_a': speaker_a,
    'speaker_b': speaker_b,
    'exchanges': exchanges
}

with open(output_file, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Saved to {output_file}")

# show samples
print("\nSample exchanges:")
samples = [0, len(exchanges)//3, 2*len(exchanges)//3, len(exchanges)-1]
for idx in samples:
    if idx >= len(exchanges):
        continue
    ex = exchanges[idx]
    mins = int(ex['statement']['start']) // 60
    secs = int(ex['statement']['start']) % 60
    print(f"\n[{mins:02d}:{secs:02d}] {ex['statement']['speaker']}: {ex['statement']['text'][:80]}...")
    print(f"      → {ex['response']['speaker']}: {ex['response']['text'][:80]}...")
