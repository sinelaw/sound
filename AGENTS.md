# Working on this project — a guide for coding agents

This repo turns a scanned lead sheet into an engraved score **and** a produced
rock-band arrangement, entirely from the command line on Linux (no DAW, no GUI,
no realtime audio). This document is the map: what to install, how the pipeline
fits together, where to change things, and the non-obvious lessons that cost
real time to learn. Read it before touching audio.

---

## 0. The one-paragraph mental model

`uf-gozal-v2.ly` (hand-verified transcription) → LilyPond → `uf-gozal-v2.midi`
(plain melody+chords). `arrange-band.py` reads that and writes
`uf-gozal-band.midi`, a 10-track band. `mix-studio.py` renders each track to a
stem with `fluidsynth`, runs the guitars through **real amp-sim VST3s hosted
offline via `pedalboard`**, applies DSP (EQ/compression/pan/reverb/glue/master),
and writes `uf-gozal-band-mixed.{wav,mp3}`. `render.sh` runs the whole chain.

You cannot hear the output. **Levels are decided by measurement; timbre and
musical choices come from the user.** Respect that division or you will waste
turns polishing things you can't perceive.

---

## 1. Environment / install

### System tools (apt)
`lilypond fluidsynth ffmpeg` and a GM soundfont
(`/usr/share/sounds/sf2/FluidR3_GM.sf2`, already present on Ubuntu with
`fluid-soundfont-gm`). `7z`/`p7zip` if you fetch sample libraries.

### Python (via `uv`, in `omr/`)
All Python runs through the `uv` project in `omr/`:
```bash
cd omr && uv sync                     # creates omr/.venv
uv run --project omr python <script>  # from the repo root
```
Deps: `mido numpy scipy pedalboard` (+ `oemer music21 opencv-python-headless`
for the OMR path). `omr/.venv` is ~890 MB and git-ignored — regenerate, never
commit it.

### Audio plugins + apps (Flatpak, `--user`, no sudo)
```bash
flatpak install --user flathub org.ardour.Ardour studio.kx.carla
P=org.freedesktop.LinuxAudio.Plugins
flatpak install --user flathub $P.GuitarML//25.08 $P.sfizz//25.08 \
  $P.setBfree//25.08 $P.AVLDrums//25.08 $P.DragonflyReverb//25.08 \
  $P.Calf//25.08 $P.LSP//25.08 $P.ZamPlugins//25.08 $P.Surge-XT//25.08 ...
```
Match the `//25.08` branch to the Ardour runtime (`flatpak info --user
org.ardour.Ardour | grep Runtime`). Plugin binaries then live under
`~/.local/share/flatpak/runtime/org.freedesktop.LinuxAudio.Plugins.*/**/`.

---

## 2. How to change things (the common asks)

| You want to change… | Edit… |
|---|---|
| A wrong/again note, rhythm | `uf-gozal-v2.ly` (the transcription) |
| Which instrument plays a part | `SPEC` list in `arrange-band.py` (GM program numbers) |
| Drum groove / fills / per-section feel | the `# ---- drums` block + `section_of()` in `arrange-band.py` |
| The guitar solo (notes, bends, descent) | the solo/`DESC`/expression blocks in `arrange-band.py` |
| Embellishments (piano fills, organ swells, licks) | the `# ---- embellishments` block and the EP-comp pass |
| Section dynamics / fades | `section_of()` levels, `SUBDUED_BARS`, the `accomp_gain` post-pass |
| **Per-track level / pan / EQ / comp / reverb** | `PLAN` dict in `mix-studio.py` |
| **Guitar tone / distortion** | the `amp_sim(...)` calls in `mix-studio.py` |
| Overall loudness target | the `-10.5 LUFS` aim near the end of `mix-studio.py` |

### Build
```bash
./render.sh            # full: score → arrange → stems → amp sims → mix → mp3
./render.sh --fast     # reuse cached stems; use after MIX-ONLY changes
./render.sh --score-only
```
`--fast` skips fluidsynth re-rendering. It is **only valid when the band MIDI
did not change** — any edit to `arrange-band.py` needs a full run.

### Verify without ears
After a change, confirm it with `mido` (structure) and the measurement helpers
in `mix-studio.py` (`lufs`, `true_peak`, per-section RMS, crest factor). Example
checks used this session: "does the solo section sit +Ndb over the chorus",
"how many pitchwheel events on the solo", "is bar 66 strictly descending",
"crest factor before/after the amp" (lower = more distorted).

---

## 3. Lessons learned (the expensive ones)

**You can't hear it — so measure, and use the user as the ear.** Every level
decision here is backed by a number (BS.1770 LUFS, dBTP, crest factor,
per-section RMS). Timbre/aesthetic calls (“sounds like a bagpipe”, “too washy”,
“too much slide”) can only come from the user. When they give such feedback,
translate it to a measurable or structural change, apply it, and re-measure.

**Don't trust a plugin did anything — measure it.** GuitarML **Proteus loaded
fine and was a silent no-op** (crest factor unchanged at every drive setting)
because it had no tone-capture model. Two renders shipped with a "distortion"
that did nothing. **SmartAmp**'s lead channel actually saturates. Always compare
crest factor in vs out. For more distortion, cascade the amp into itself
(`stages=2`) and/or `pregain` — but it plateaus (~8.3 dB crest here).

**Low notes + heavy distortion = noise.** The solo's descent tail turned to
mush through the cascaded amp. Fix: split the stem in time and run the tail
through a milder amp (see the Solo branch in `mix-studio.py`).

**`pedalboard` is how you host plugins headless.** It loads VST3s from Python
and processes offline, faster than realtime — no JACK, no GUI. Caveats: some
flatpak VST3s (**sfizz, LSP**) fail to load *outside* the flatpak sandbox
(missing runtime libs); GuitarML/Zam/Dragonfly/Surge/master_me load fine. This
is why every instrument except the guitars is still General-MIDI: the SFZ
libraries can't be reached from host Python. Getting sfizz working natively
(a non-flatpak build into `~/.vst3`) is the biggest open quality lever.

**Ardour headless Lua is a trap on flatpak.** `ardour9-lua` aborts instantly
with `FATAL: exception not rethrown` because the flatpak wrapper **omits the
`LV2_PATH` export** the GUI wrapper sets — export it manually and it works.
Even then: `Session:new_audio_track` works, but `new_midi_track` segfaults, and
there is **no `import_files` binding**, so you cannot script MIDI import. We
abandoned this path for `pedalboard`. (`RouteGroup` args must be constructed
objects, not `nil`; enum consts like `ARDOUR.TrackMode.Normal` read fine even
though `pairs()` shows the namespace empty.)

**OMR: no engine is trustworthy; measure against the page.** Audiveris split the
score into fake "movements" and captured **zero chords**; both it and oemer
mangled rhythms and octaves. The reliable pitch signal was **template-matching
noteheads against detected staff-line geometry** and enforcing "every bar sums
to 4/4". oemer itself needs `LV2_PATH` unset issues avoided, `onnxruntime` (CPU,
not `-gpu` — needs CUDA) and `opencv<5` (v5 broke its `HoughLinesP` call). Use
`uv`'s `[tool.uv] override-dependencies` to force the CPU onnxruntime past
oemer's pin.

**Git / GitHub:** pushes are rejected if the commit email is a private address
(`GH007`). Use the noreply form `<id>+<user>@users.noreply.github.com`
(get `<id>` from `https://api.github.com/users/<user>`).

**This shell resets `cwd` between `Bash` calls.** Use absolute paths, or `cd`
inside each command. Background `&` jobs return immediately — poll their logs.

**Disk was at ~94%.** Stems (`stems/`, ~450 MB) and `omr/.venv` (~890 MB) are
the big regenerable items; both are git-ignored. Don't commit audio.

---

## 4. What's deliberately NOT in git
Generated audio (`*.wav *.mp3 *.midi`), engraved PDFs except the original
`oof-orig.pdf`, `stems/`, `omr/.venv/`, `sample-libraries/`, scratch. See
`.gitignore`. The source of truth is the `.ly`, the two `.py`, `render.sh`, and
the OMR MusicXML.
