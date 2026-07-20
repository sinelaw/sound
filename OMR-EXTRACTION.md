# How the song was extracted from the PDF (OMR process)

Getting `uf-gozal-v2.ly` out of `oof-orig.pdf` (a 2-page scanned lead sheet:
single melody line + chord symbols + Hebrew lyrics) took an elaborate,
multi-tool process because **no single OMR engine was trustworthy**. This is
the record of what worked, what didn't, and how to redo it.

## The short version

Melody **pitches** are only reliable when *measured off the engraving* — by
detecting the staff geometry and template-matching noteheads — not when read
from any OMR engine's guess. **Rhythms** came from reconciling two OMR engines
under a hard "every bar sums to its time signature" constraint. **Chords** were
transcribed by hand (both engines captured essentially none). Every measure was
then eyeballed against a cropped, pitch-gridded image before trusting it.

## Step by step

### 1. Rasterize the PDF
```bash
pdftoppm -r 300 -png oof-orig.pdf hi        # 300 dpi, hi-1.png / hi-2.png
```
Lower-res (150 dpi) copies are fine for eyeballing whole systems; 300 dpi is
needed for notehead detection.

### 2. Run OMR engines — and distrust them
- **Audiveris** (prior output was in `unzipped/*.xml`): split the score into ten
  fake "movements" (it read the A–H rehearsal-mark boxes as movement breaks),
  **captured zero chord symbols** (every `<harmony>` empty), collapsed whole
  passages an octave or two, and ~34 of 62 bars didn't sum to a full bar.
- **oemer** (`uv`-installed): better melody, but mangled rhythms, added phantom
  accidentals (ignored the key signature), and also missed chords.

Neither is usable as-is. Install notes for oemer (they cost real time):
  - it pulls `onnxruntime-gpu` (needs CUDA) — force the CPU build via
    `[tool.uv] override-dependencies = ["onnxruntime-gpu ; sys_platform == 'nonexistent'"]`;
  - it breaks on OpenCV 5's `HoughLinesP` return shape — pin `opencv-python-headless<5`;
  - run with `-d` (no deskew) on clean digital renders.

### 3. Detect staff geometry (the reliable coordinate system)
For each system: sum dark pixels per row → the 5 staff lines are the rows above
a coverage threshold (grouped into 5 clusters). Spacing came out a constant
20.5 px. Barlines: vertical dark runs spanning exactly top→bottom staff line,
**with a stem-rejection test** (a real barline has whitespace either side at the
staff-interior rows; a note stem does not). This gives exact x-positions to slice
measures and an exact y→pitch mapping (top line = F5, one ledger below = C4).

### 4. Template-match noteheads (the reliable pitch signal)
- "De-staff" the image: remove short vertical dark runs centred on a staff line.
- Crop one real notehead from the score itself; `cv2.matchTemplate`
  (`TM_CCOEFF_NORMED`, threshold ~0.62) across each de-staffed system.
- Keep a hit only if its y sits within tolerance of a real diatonic pitch
  position (from the staff geometry) — this rejects lyrics and chord glyphs.
- Hollow (half/whole) heads: find enclosed white holes of notehead size.
- Map each surviving centroid to a pitch via the geometry.

This reproduced hand readings note-for-note on the bars checked, and
independently found that the intro motif repeats verbatim later — a good
internal-consistency signal.

### 5. Reconcile rhythm
Dump each engine's per-measure durations; where they disagree, pick the reading
that (a) matches the measured pitches and (b) makes the bar sum to 4/4 (or 2/4
for the metre changes at m12/21/41/65). The "every bar must sum" constraint
resolves most conflicts on its own.

### 6. Chords and lyrics by hand
Both engines captured no chords, so the chord symbols were read directly off the
rasterized systems. (Hebrew lyrics were left out of the transcription.)

### 7. Verify every measure visually
Generate one cropped PNG per measure with a **labelled pitch grid** overlaid
(horizontal lines at each staff position, named C6…G3), so each notehead's pitch
is checkable at a glance. Fix the off-by-N until the top line reads F5 and the
first ledger below reads C4. Only then trust the bar.

### 8. Engrave and compare
Write LilyPond, compile, render to PNG, and lay it **side by side with the
original page**. Iterate until they match. Watch for `\relative` octave drift —
writing the melody in absolute octaves (`c'` = middle C) made pitch errors
obvious and self-documenting.

## Result
`uf-gozal-v2.ly` — 63 bars, key F, with the Intro/A–H section map, the segno at
m14, To-Coda at m29, D.S. al Coda, the 2/4 inserts, and the 1st/2nd endings.
The scratch detection scripts were one-offs (staff/barline/notehead detection,
per-measure grid crops); they are not kept in the repo but are straightforward
to rebuild from this description with numpy + scipy + opencv (all in `omr/`).

## Lesson
For a clean digital lead sheet, an OMR engine gets you a *skeleton* at best.
The trustworthy pitches came from measuring the image against its own detected
staff geometry; everything else was cross-checking and hand verification. Budget
for that — the engines' confident-looking XML is where the errors hide.
