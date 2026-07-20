#!/usr/bin/env python3
"""
Rock-band arrangement of Uf Gozal  (v2).

Changes from v1, all from listening feedback:
  * solo guitar much quieter, and rendered CLEAN so a real amp sim can
    supply the distortion in the mix (v1's GM "distortion guitar" was the
    nasal "bagpipe" tone)
  * parallel-thirds harmony guitar removed - it droned under the solo and
    was a big part of the bagpipe effect. Replaced with sparse octave stabs.
  * vibrato greatly reduced, bends only on selected notes
  * solo now ends with a descending blues run down to bass notes instead of
    holding the final note
  * drums get real variety: swung jazz sections, half-time, fills every few
    bars, hat/ride/sidestick variation
  * embellishments throughout: piano fills, organ swells, bass walk-ups,
    guitar slides

Output: uf-gozal-band.midi
"""
import random
from collections import defaultdict
import mido

random.seed(20260720)

SRC, OUT = "uf-gozal-v2.midi", "uf-gozal-band.midi"
src = mido.MidiFile(SRC)
TPB = src.ticks_per_beat
Q, E, S, T = TPB, TPB // 2, TPB // 4, TPB // 8

# ---------------------------------------------------------------- parse source
def note_events(track):
    t, on, out = 0, defaultdict(list), []
    for msg in track:
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            on[msg.note].append((t, msg.velocity))
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if on[msg.note]:
                st, v = on[msg.note].pop(0)
                out.append((st, t - st, msg.note, v))
    out.sort()
    return out

melody = note_events(src.tracks[1])
chordnotes = note_events(src.tracks[2])

byonset = defaultdict(list)
for st, dur, p, v in chordnotes:
    byonset[st].append((p, dur))
chords = [{"start": st,
           "dur": max(d for _, d in byonset[st]),
           "pitches": sorted(p for p, _ in byonset[st]),
           "bass": min(p for p, _ in byonset[st])} for st in sorted(byonset)]

sigs, t = [], 0
for msg in src.tracks[0]:
    t += msg.time
    if msg.type == "time_signature":
        sigs.append((t, msg.numerator, msg.denominator))
if not sigs or sigs[0][0] != 0:
    sigs.insert(0, (0, 4, 4))

END = max(max(s + d for s, d, _, _ in melody),
          max(c["start"] + c["dur"] for c in chords))
bars, t = [], 0
while t < END:
    num, den = 4, 4
    for st, n, d in sigs:
        if st <= t:
            num, den = n, d
    beats = num * (4 / den)
    bars.append((t, t + int(beats * Q), beats))
    t += int(beats * Q)
NBARS = len(bars)

# ---------------------------------------------------------------- sections
SOLO_BARS = range(58, 67)
# The coda no longer strips the arrangement - the band plays the SAME parts but
# very softly (a continuous gain dip, see accomp_gain below), so nothing drops
# out, it just gets quiet. SUBDUED kept empty so the old branches fall through.
SUBDUED_BARS = set()
SOLO_LAST = 66                     # gets the blues descent
CLEAN_MEL_BARS = set(range(1, 5)) | set(range(30, 34))
SECTION_STARTS = {1, 5, 14, 23, 30, 34, 43, 50, 58, 67, 71, 74, 77}

def section_of(b):
    """one consistent rock beat throughout; choruses get hat/crash treatment"""
    if b <= 4:  return "intro",  0, "sparse"
    if b <= 13: return "verse",  1, "rock"
    if b <= 22: return "verse",  1, "rock"
    if b <= 29: return "chorus", 2, "rock"
    if b <= 33: return "inter",  2, "rock"
    if b <= 42: return "verse",  1, "rock"
    if b <= 49: return "chorus", 2, "rock"
    if b <= 57: return "coda",   2, "rock"
    if b <= 66: return "solo",   3, "rock"
    if b <= 70: return "chorus", 2, "rock"
    if b <= 76: return "chorus", 2, "rock"
    return "outro", 2, "rock"

# Piano and organ never play together - they INTERCHANGE by section, so the two
# keyboards trade off through the song instead of stacking into one chord bed.
#   piano = rhythmic short stabs;  organ = sustained pad with gaps.
def keyboard_for(b):
    if b <= 4:  return None            # intro: neither (clean guitar only)
    if b <= 22: return "piano"         # verses A + B (intimate, rhythmic)
    if b <= 29: return "organ"         # chorus  -> full organ
    if b <= 33: return "piano"         # inter
    if b <= 42: return "piano"         # verse
    if b <= 49: return "organ"         # chorus  -> full organ
    if b <= 57: return "organ"         # coda    -> full organ
    if b <= 66: return "organ"         # solo    -> answers in the gaps
    return "organ"                     # choruses 67-76 + outro -> full organ

CH_LEAD, CH_SOLO, CH_HARM, CH_RHY, CH_CLEAN, CH_BASS, CH_PIANO, CH_ORGAN, CH_STR, CH_DRUM = range(10)
SPEC = [
    ("Lead Vocal",     CH_LEAD,   5),   # FM/DX electric piano (sharp, bell-like)
    ("Solo Guitar",    CH_SOLO,  27),   # CLEAN - amp sim added in the mix
    ("Harmony Guitar", CH_HARM,  27),
    ("Rhythm Guitar",  CH_RHY,   29),
    ("Clean Guitar",   CH_CLEAN, 27),
    ("Bass",           CH_BASS,  33),
    ("Piano",          CH_PIANO,  0),
    ("Organ",          CH_ORGAN, 16),   # drawbar organ - warm filler pad
    ("Strings",        CH_STR,   48),
    ("Drums",          CH_DRUM,   0),
]
ev = {ch: [] for _, ch, _ in SPEC}

def put(ch, pitch, vel, start, dur):
    if not (0 <= pitch <= 127) or dur <= 0:
        return
    v = max(1, min(127, int(vel)))
    ev[ch].append((int(start), mido.Message("note_on", note=pitch, velocity=v, channel=ch)))
    ev[ch].append((int(start + dur), mido.Message("note_off", note=pitch, velocity=0, channel=ch)))

def hum(v, s=6):
    return v + random.randint(-s, s)

def bar_of(tick):
    for i, (a, b, _) in enumerate(bars):
        if a <= tick < b:
            return i + 1
    return NBARS

# ---------------------------------------------------------------- melody routing
a66_, b66_, _ = bars[SOLO_LAST - 1]
DESC_START = b66_ - Q                                 # descent = final beat only

for st, dur, p, v in melody:
    b = bar_of(st)
    if b in SOLO_BARS:
        if b == SOLO_LAST and st >= DESC_START - E:
            continue                                  # make room for the descent
        d = min(dur, DESC_START - st) if b == SOLO_LAST else dur
        put(CH_SOLO, p, hum(78, 6), st, d)            # quieter, clean
    elif b in CLEAN_MEL_BARS:
        put(CH_CLEAN, p, hum(94, 5), st, dur)        # intro motif: clean gtr, present
    else:
        # fade the very last notes of the tune down to a soft ending (~4:04)
        lv = 96
        if b >= 80:
            lv = 60
        elif b == 79:
            lv = 78
        put(CH_LEAD, p, hum(lv, 5), st, dur)

# --- slow, deliberate blues descent, tumbling ~2 octaves down ---------------
# half-speed (16th-note steps) so it reads as a clear descending line, not a
# blur. Strictly non-overlapping; ends on F1. Spills past the barline into 67.
# ends on F2 (41), NOT F1 - a guitar's lowest string is E2(40); anything below
# that fed into the neural amp model is sub-range garbage (the "horrible sound"
# at the end of the solo). Three octaves of descent is plenty.
DESC = [77, 74, 70, 65, 60, 53, 48, 41]        # F blues plunge, ends on F2
tpos = DESC_START
for i, p in enumerate(DESC):
    step = S if i < len(DESC) - 1 else E       # 16ths, last note longer
    put(CH_SOLO, p, hum(92 - i * 3, 3), tpos, int(step * 0.9))
    tpos += step
DESC_NOTES = set(DESC)

# sparse octave stabs instead of the old parallel-thirds drone
for st, dur, p, v in melody:
    b = bar_of(st)
    if b in (62, 64) and dur >= Q:
        put(CH_HARM, p - 12, hum(58, 5), st, dur)

# --- expression: slides, whole-step bends, vibrato -------------------------
# widen pitch-bend range to +/-12 semitones (RPN 0) so real slides are possible
BEND_RANGE = 12.0
bend = [
    (0, mido.Message("control_change", control=101, value=0, channel=CH_SOLO)),
    (0, mido.Message("control_change", control=100, value=0, channel=CH_SOLO)),
    (0, mido.Message("control_change", control=6,   value=12, channel=CH_SOLO)),
    (0, mido.Message("control_change", control=38,  value=0, channel=CH_SOLO)),
]

def bval(semis):
    return max(-8191, min(8191, int(semis / BEND_RANGE * 8192)))

# reconstruct the solo note list from what we emitted
solo, _open = [], {}
for t, m in sorted(ev[CH_SOLO], key=lambda x: (x[0], x[1].type == "note_on")):
    if m.type == "note_on":
        _open.setdefault(m.note, []).append(t)
    elif _open.get(m.note):
        s = _open[m.note].pop(0)
        solo.append((s, t - s, m.note))
solo.sort()

# No expression modulation on the solo at all - straight, in-tune notes.
# (Earlier vibrato/bends read as too much tremolo/slide.) The pitch wheel is
# just held centred throughout.
# make sure the wheel is centred before the descent - a stray bend on those
# low notes through the amp would be exactly the kind of "weird sound" to avoid
bend.append((DESC_START - 4, mido.Message("pitchwheel", pitch=0, channel=CH_SOLO)))

# ---------------------------------------------------------------- helpers
def chords_in(a, b):
    return [c for c in chords if a <= c["start"] < b] or \
           [c for c in chords if c["start"] < a <= c["start"] + c["dur"]]

def voice(ps, lo, hi):
    out = []
    for p in ps:
        q = p % 12
        while q < lo: q += 12
        while q > hi: q -= 12
        out.append(q)
    return sorted(set(out))

def bassify(p):
    while p > 47: p -= 12
    while p < 33: p += 12
    return p

K, SN, SS, HH, OH, PH, CR, RD, RB, T1, T2, T3 = 36, 38, 37, 42, 46, 44, 49, 51, 53, 48, 45, 41

def swing(off):
    """map an 8th offset to a swung (triplet) position"""
    return off if off % Q == 0 else off - E + int(E * 4 / 3)

def chord_at(tick):
    cur = None
    for c in chords:
        if c["start"] <= tick:
            cur = c
        else:
            break
    return cur

# --- electric-piano lead comps itself: soft chords + bluesy licks in the gaps
# The EP carries the melody; where a singer would breathe between phrases it
# fills with a quiet chord voicing and, now and then, a short F-blues lick.
_lead, _o = [], {}
for _t, _m in sorted(ev[CH_LEAD], key=lambda x: (x[0], x[1].type == "note_on")):
    if _m.type == "note_on":
        _o.setdefault(_m.note, []).append(_t)
    elif _o.get(_m.note):
        _s = _o[_m.note].pop(0)
        _lead.append((_s, _t - _s, _m.note))
_lead.sort()

# a single blue note dropped in now and then - no runs (they read as cheesy)
BLUE_NOTES = [70, 68, 71, 65, 72]                    # Bb4 Ab4 B4(blue) F4 C5
_gi = 0
for i in range(len(_lead) - 1):
    end = _lead[i][0] + _lead[i][1]
    nxt = _lead[i + 1][0]
    gap = nxt - end
    b = bar_of(end)
    if b in SOLO_BARS or b in CLEAN_MEL_BARS or b in SUBDUED_BARS or b >= 79:
        continue
    if gap < Q:
        continue
    c = chord_at(end)
    if not c:
        continue
    # the EP no longer comps chords under its own melody (that self-doubling
    # muddied the harmony with the piano/organ). Just an occasional single
    # blue-note fill, in the lead's own tone, to answer a phrase.
    if gap >= Q * 2 and _gi % 2 == 0:
        p = BLUE_NOTES[_gi % len(BLUE_NOTES)]
        put(CH_LEAD, p, hum(52, 5), nxt - E, E - 20)
    _gi += 1

# ---------------------------------------------------------------- generate
for bi, (a, b, beats) in enumerate(bars):
    bar = bi + 1
    sec, lvl, style = section_of(bar)
    cs = chords_in(a, b)
    if not cs:
        continue
    nb = int(beats)
    fill_bar = ((bar + 1) in SECTION_STARTS) or (bar % 8 == 0 and lvl >= 1)
    subdued = bar in SUBDUED_BARS               # quiet breakdown before the solo
    if subdued:
        lvl = 1                                 # pull everything back to a low level

    # ---- bass
    for c in cs:
        root = bassify(c["bass"])
        cs_, cd = c["start"], min(c["dur"], b - c["start"])
        fifth, octv = root + 7, root + 12
        if subdued:
            put(CH_BASS, root, hum(56), cs_, min(cd, Q * 2 - 20))   # soft root pulse
            continue
        if style == "jazz":
            steps = int(cd // Q)
            walk = [root, root + 5, fifth, root + 9]
            for k in range(steps):
                put(CH_BASS, walk[k % 4], hum(78), cs_ + k * Q, Q - 30)
        elif lvl <= 1:
            put(CH_BASS, root, hum(88), cs_, min(cd, Q * 2 - 20))
            if cd >= Q * 2:
                put(CH_BASS, root, hum(80), cs_ + Q + E, E - 20)
        elif lvl == 2:
            for k in range(int(cd // E)):
                put(CH_BASS, root if k % 4 < 3 else fifth,
                    hum(92 if k % 2 == 0 else 78), cs_ + k * E, E - 18)
        else:
            for k in range(int(cd // E)):
                p = root if k % 8 < 6 else (fifth if k % 2 else octv)
                put(CH_BASS, p, hum(100 if k % 2 == 0 else 84), cs_ + k * E, E - 14)
    # bass walk-up into the next section
    if fill_bar and lvl >= 1:
        r = bassify(cs[-1]["bass"])
        for k, iv in enumerate([0, 3, 5, 7]):
            put(CH_BASS, r + iv, hum(86), b - Q + k * S, S - 10)

    # ---- guitars / keys
    for c in cs:
        cs_, cd = c["start"], min(c["dur"], b - c["start"])
        tones = voice(c["pitches"], 52, 76)
        root = c["bass"] % 12 + 48
        power = [root, root + 7, root + 12]

        # clean-guitar arpeggios run through the verses AND the choruses/coda/
        # outro (the same figure carries across), just not under the solo.
        if sec in ("intro", "verse", "chorus", "coda", "outro") and style != "jazz":
            pat = tones * 3
            avel = 60 if sec in ("chorus", "outro") else 64
            for k in range(int(cd // E)):
                put(CH_CLEAN, pat[k % len(pat)], hum(avel), cs_ + k * E, E + 40)
        if style == "jazz":                       # comp stabs on the off-beats
            for k in range(int(cd // Q)):
                if k % 2 == 1:
                    for p in tones[:3]:
                        put(CH_CLEAN, p, hum(58), swing(cs_ + k * Q + E), E - 20)
        if subdued:
            pass                                  # no rhythm guitar in the breakdown
        elif lvl >= 2 and style != "jazz":
            for k in range(int(cd // E)):
                for p in power:
                    put(CH_RHY, p, hum(94 if k % 2 == 0 else 76), cs_ + k * E, E - 12)
        elif lvl == 1 and style != "jazz":
            for p in power:
                put(CH_RHY, p, hum(52), cs_, cd - 20)

        kbd = keyboard_for(bar)
        # PIANO = rhythmic, but sparse: short chord stabs on beats 1 & 3 only
        # (slower repeating, staccato) - never a sustained bed.
        if kbd == "piano":
            ptones = voice(c["pitches"], 55, 72)
            for k in range(int(cd // Q)):
                if k % 2 == 0:                             # beats 1 & 3
                    for p in ptones:
                        put(CH_PIANO, p, hum(56 if lvl == 1 else 64),
                            cs_ + k * Q, E - 40)           # short stab
        # ORGAN = sustained pad (no rhythm), lower/warmer register.
        #  chorus / coda / outro -> FULL, every bar, no gaps, a touch louder
        #  (in the solo it instead answers the gaps - see the post-pass).
        if kbd == "organ" and sec != "solo":
            ov = {"chorus": 62, "coda": 54, "outro": 56}.get(sec, 52)
            for p in voice(c["pitches"], 67, 84):        # higher pad register
                put(CH_ORGAN, p, hum(ov), cs_, cd - 10)
        if sec in ("chorus", "solo", "coda", "outro"):
            for p in voice(c["pitches"], 64, 88):
                put(CH_STR, p, hum(54), cs_, cd - 10)

    # ---- embellishments
    if bar % 4 == 2 and lvl >= 1:                       # piano fill in the gaps
        tones = voice(cs[-1]["pitches"], 64, 84)
        for k, p in enumerate(tones[:4]):
            put(CH_PIANO, p, hum(64), b - E - k * T, T)
    if sec in ("chorus", "outro") and bar % 4 == 0:     # organ swell
        for p in voice(cs[-1]["pitches"], 60, 79):
            for k in range(4):
                put(CH_ORGAN, p, 40 + k * 12, b - Q + k * S, S)
    if bar in (21, 41, 65) or (fill_bar and lvl >= 2):  # guitar slide up
        r = cs[-1]["bass"] % 12 + 60
        for k, iv in enumerate([-5, -3, -1, 0]):
            put(CH_CLEAN, r + iv, hum(70), b - Q + k * S, S)

    # ---- drums: one consistent rock beat the whole way through.
    # crash accents only on the actual choruses (not the "inter" restatement,
    # which would drag them on to ~1:40 - they should stop by ~1:30).
    is_chorus = sec in ("chorus", "outro")

    if bar >= 80:
        # soft ending: light kit - soft hats, kick 1, sidestick 3
        for k in range(nb * 2):
            put(CH_DRUM, HH, hum(38, 3), a + k * E, E - 10)
        put(CH_DRUM, K, hum(60), a, E)
        if nb >= 3:
            put(CH_DRUM, SS, hum(56), a + 2 * Q, E)
    elif style == "sparse":                                # intro only
        for k in range(nb * 2):
            put(CH_DRUM, HH, hum(44, 4), a + k * E, E - 10)
        put(CH_DRUM, K, 76, a, Q)
    else:
        if bar in SECTION_STARTS and lvl >= 1:
            put(CH_DRUM, CR, 100, a, S)                    # section-start crash
        # cymbal layer:
        #  chorus -> sharp, short crash hits on the quarter-notes (not washy)
        #  solo   -> ride cymbal
        #  verses -> closed hats
        for k in range(nb * 2):
            onbeat = (k % 2 == 0)
            if is_chorus:
                if onbeat:
                    v = 62 if k == 0 else 52               # sharp, not too loud
                    put(CH_DRUM, CR, hum(v, 3), a + k * E, S)   # short = defined
                else:
                    put(CH_DRUM, HH, hum(34, 3), a + k * E, S)  # quiet hat under
            else:
                cym, v = (RD, 72 if onbeat else 56) if lvl == 3 \
                    else (HH, 74 if onbeat else 54)
                put(CH_DRUM, cym, hum(v, 4), a + k * E, E - 10)

        # kick / snare backbone (same basic beat everywhere)
        for beat in range(nb):
            tb = a + beat * Q
            if beat % 2 == 0:
                put(CH_DRUM, K, hum(100), tb, E)
            else:
                put(CH_DRUM, SN, hum(96), tb, E)
            if lvl >= 2 and beat % 2 == 0:
                put(CH_DRUM, K, hum(80), tb + E + S, S)    # syncopated kick
            if lvl == 3 and beat % 2 == 1:
                put(CH_DRUM, SN, hum(38), tb + E + S, S)   # ghost note

    # ---- transitions: frequent but light (not in the breakdown)
    if lvl >= 1 and style != "sparse" and not subdued:
        if bar % 8 == 0:                                   # small tom turnaround
            for k, d in enumerate([SN, T1, T2]):
                put(CH_DRUM, d, hum(78, 4), b - 3 * S + k * S, S)
        elif bar % 4 == 0:                                 # snare pickup
            for k in range(2):
                put(CH_DRUM, SN, hum(70, 4), b - 2 * S + k * S, S)
    if fill_bar and lvl >= 1 and not subdued:              # into a new section
        for k, d in enumerate([SN, T1, T2, T3]):
            put(CH_DRUM, d, hum(84, 4), b - 4 * S + k * S, S)
    if bar == NBARS:
        put(CH_DRUM, CR, 72, a, Q * 4)          # soft final cymbal, let it ring
        put(CH_DRUM, K, 70, a, Q)

# --- post-passes ------------------------------------------------------------
# 0. keyboards answer in the gaps of the lead/solo (call-and-response). Where
#    the solo leaves a rest, the organ swells a prominent chord into the gap;
#    where the sung melody rests, the piano answers with a short chord.
def gap_answer(voice_notes, ch, lo, hi, vel, minsec, only_bars=None):
    vn = sorted(voice_notes)
    for i in range(len(vn) - 1):
        end = vn[i][0] + vn[i][1]
        nxt = vn[i + 1][0]
        gap = nxt - end
        b = bar_of(end)
        if only_bars and b not in only_bars:
            continue
        if gap < minsec:
            continue
        c = chord_at(end)
        if not c:
            continue
        for p in voice(c["pitches"], lo, hi):
            put(ch, p, hum(vel, 4), end + S, min(int(gap * 0.7), Q * 2))

gap_answer(solo, CH_ORGAN, 60, 79, 72, int(Q * 1.2),
           only_bars=set(range(58, 67)))          # organ fills solo gaps, prominent

# piano answers the lead EP's phrase gaps with SHORT SHARP chords, in the
# sections where piano is the keyboard (verses / inter). Catches the shorter
# "half-phrase" rests too, so it converses with the melody.
_pbars = {b for b in range(1, NBARS + 1) if keyboard_for(b) == "piano"}
_pl = sorted(_lead)
for i in range(len(_pl) - 1):
    _end = _pl[i][0] + _pl[i][1]
    _gap = _pl[i + 1][0] - _end
    if bar_of(_end) not in _pbars or _gap < E * 3:
        continue
    _c = chord_at(_end)
    if not _c:
        continue
    for _p in voice(_c["pitches"], 55, 72):
        # sharp attack but let it ring through the gap (not staccato)
        put(CH_PIANO, _p, hum(74, 4), _end + S, min(int(_gap * 0.85), Q * 2))

# 1. the band plays full right up to the coda, then fades over the first bar or
#    two OF the coda (50-51), sits low through 52-54, and ramps back up over
#    55-57. Continuous (per-note by onset time) so it glides, not steps.
ACCOMP = {CH_RHY, CH_CLEAN, CH_BASS, CH_PIANO, CH_ORGAN, CH_STR, CH_DRUM}
LOW = 0.3                                       # very soft, but NOT silent
def bstart(bar):
    return bars[bar - 1][0]
FADES = [(bstart(50), bstart(52), 1.0, LOW),   # fade down over the coda's first 2 bars
         (bstart(52), bstart(55), LOW, LOW),   # stay very soft (all parts present)
         (bstart(55), bstart(58), LOW, 1.0)]   # ramp back up into the solo
def accomp_gain(tick):
    for t0, t1, g0, g1 in FADES:
        if t0 <= tick < t1:
            return g0 + (g1 - g0) * (tick - t0) / (t1 - t0)
    return 1.0
for ch in ACCOMP:
    scaled = []
    for t, msg in ev[ch]:
        if msg.type == "note_on" and msg.velocity > 0:
            g = accomp_gain(t)
            if g < 0.999:
                msg = msg.copy(velocity=max(1, int(msg.velocity * g)))
        scaled.append((t, msg))
    ev[ch] = scaled

# 2. at the very end, drop the last few busy bass notes and hold one soft root
#    of the key (F) instead - the running notes were redundant there.
_bass_on = sorted(t for t, m in ev[CH_BASS] if m.type == "note_on" and m.velocity > 0)
if len(_bass_on) >= 4:
    _cut = _bass_on[-4]                         # remove the final four onsets
    ev[CH_BASS] = [(t, m) for t, m in ev[CH_BASS]
                   if not (m.type == "note_on" and m.velocity > 0 and t >= _cut)]
    put(CH_BASS, bassify(53), 52, _cut, bars[-1][1] - _cut)   # soft held F

# 3. the melody keeps its final fermata note, but the accompaniment guitars
#    that ramble on past it are replaced by ONE softly arpeggiated F chord
#    ringing under it (the mix fades it out).
_fa, _fb = bars[-2][0], bars[-1][1]              # last two bars
for _ch in (CH_RHY, CH_CLEAN):
    ev[_ch] = [(t, m) for t, m in ev[_ch] if t < _fa]
for _j, _p in enumerate([53, 57, 60, 65, 69]):   # F A C F A  arpeggiated up
    put(CH_CLEAN, _p, hum(58 - _j * 3, 3), _fa + _j * S, _fb - _fa - _j * S)

# ---------------------------------------------------------------- write
out = mido.MidiFile(ticks_per_beat=TPB)
meta = mido.MidiTrack()
meta.append(mido.MetaMessage("track_name", name="Uf Gozal - Rock Band v2", time=0))
tempo_ev = [(0, mido.bpm2tempo(78))]
rit = bars[-2][0]
for k in range(8):
    tempo_ev.append((rit + k * (Q // 2), mido.bpm2tempo(78 - k * 5)))
am = [(t, mido.MetaMessage("set_tempo", tempo=v, time=0)) for t, v in tempo_ev]
am += [(t, mido.MetaMessage("time_signature", numerator=n, denominator=d, time=0))
       for t, n, d in sigs]
am.sort(key=lambda x: x[0])
prev = 0
for t, m in am:
    m.time = t - prev; prev = t; meta.append(m)
out.tracks.append(meta)

for name, ch, prog in SPEC:
    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("track_name", name=name, time=0))
    items = list(ev[ch]) + (bend if ch == CH_SOLO else [])
    if ch != CH_DRUM:
        tr.append(mido.Message("program_change", program=prog, channel=ch, time=0))
    items.sort(key=lambda x: (x[0], x[1].type == "note_on"))
    prev = 0
    for t, m in items:
        mm = m.copy(); mm.time = max(0, t - prev); prev = t; tr.append(mm)
    out.tracks.append(tr)

out.save(OUT)
print(f"wrote {OUT}: {len(out.tracks)} tracks, {NBARS} bars, {out.length:.1f}s")
for name, ch, prog in SPEC:
    print(f"  ch{ch:2d} prog{prog:3d}  {name:15s} "
          f"{len([1 for _, m in ev[ch] if m.type=='note_on'])} notes")
