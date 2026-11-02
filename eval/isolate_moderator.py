"""
Find moderator segments by running diarization twice.

How it works (simple version):
1. Run diarization as "person A vs everyone else" -> get 2 speakers
2. Run diarization as "person B vs everyone else" -> get 2 speakers
3. The "everyone else" from run 1 includes: person B + moderators
4. The "everyone else" from run 2 includes: person A + moderators
5. Where both "everyone else" overlap = just moderators!

Usage:
  python isolate_moderator.py personA.turns.json personB.turns.json output.json

Output: segments where moderator is speaking (hopefully)
"""

import json
import sys

def load_turns(path):
    # just read the json and group by speaker
    data = json.load(open(path))
    speakers = {}

    for turn in data:
        who = turn['spk']
        if who not in speakers:
            speakers[who] = []
        speakers[who].append(turn)

    return speakers

def find_minor_speaker(speakers_dict):
    # figure out who talked less - that's the "everyone else" bucket
    talk_times = {}

    for speaker, turns in speakers_dict.items():
        total = 0
        for turn in turns:
            total += turn['end'] - turn['start']
        talk_times[speaker] = total

    # just sort and grab the shortest one
    sorted_list = sorted(talk_times.items(), key=lambda item: item[1])
    shortest = sorted_list[0][0]

    return shortest, talk_times

def check_if_overlaps(seg1, seg2, slop=0.5):
    # check if two segments happen at roughly the same time
    # give it some wiggle room (slop) since diarization isn't perfect
    start_a = seg1['start'] - slop
    end_a = seg1['end'] + slop
    start_b = seg2['start'] - slop
    end_b = seg2['end'] + slop

    # they overlap if one doesn't end before the other starts
    if end_a < start_b:
        return False
    if end_b < start_a:
        return False
    return True

def find_overlaps(list1, list2):
    # go through list1 and see which ones also appear in list2
    matches = []

    for segment in list1:
        # check if this matches anything in the other list
        found_one = False
        for other_segment in list2:
            if check_if_overlaps(segment, other_segment):
                found_one = True
                break

        if found_one:
            matches.append(segment)

    return matches

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python isolate_moderator.py personA.turns.json personB.turns.json output.json")
        sys.exit(1)

    personA_file = sys.argv[1]
    personB_file = sys.argv[2]
    output_file = sys.argv[3]

    print("Loading person A run...")
    personA_turns = load_turns(personA_file)
    personA_minor, personA_time = find_minor_speaker(personA_turns)
    print(f"  Minor speaker (person B+mods): {personA_minor} ({personA_time[personA_minor]:.0f}s)")

    print("Loading person B run...")
    personB_turns = load_turns(personB_file)
    personB_minor, personB_time = find_minor_speaker(personB_turns)
    print(f"  Minor speaker (person A+mods): {personB_minor} ({personB_time[personB_minor]:.0f}s)")

    # Get the "everyone else" segments from each run
    personA_others = personA_turns[personA_minor]
    personB_others = personB_turns[personB_minor]

    print(f"\nFinding overlaps between {len(personA_others)} and {len(personB_others)} segments...")
    moderator_segments = find_overlaps(personA_others, personB_others)

    print(f"Found {len(moderator_segments)} likely moderator segments")

    # Calculate total moderator time
    mod_time = sum(seg['end'] - seg['start'] for seg in moderator_segments)
    print(f"Total moderator time: {mod_time:.0f}s ({mod_time/60:.1f} min)")

    # Save results
    output = {
        'moderator_segments': moderator_segments,
        'total_time': round(mod_time, 2),
        'count': len(moderator_segments)
    }

    json.dump(output, open(output_file, 'w'), indent=2)
    print(f"\nSaved to {output_file}")

    # Show sample segments (spread them out a bit)
    print("\nSample moderator segments:")
    # don't just show first 5, show some from different parts
    sample_count = min(20, len(moderator_segments))
    step = len(moderator_segments) // sample_count if sample_count > 0 else 1

    for i in range(0, len(moderator_segments), step):
        if i >= len(moderator_segments):
            break
        seg = moderator_segments[i]
        duration = seg['end'] - seg['start']
        mins = int(seg['start']) // 60
        secs = int(seg['start']) % 60
        print(f"  [{mins:02d}:{secs:02d}] {duration:.1f}s - speaker: {seg['spk']}")

        # stop after showing ~20
        if i // step >= 19:
            break
