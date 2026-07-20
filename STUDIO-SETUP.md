# Uf Gozal — studio setup

Everything below is installed and verified working (287 LV2 plugins visible
inside Ardour's sandbox). All free, all native Linux, no sudo was needed.

## Open the project

```
flatpak run org.ardour.Ardour
```

New session → **Session > Import** → `uf-gozal-band.midi`.
It imports as **10 separate tracks** (each instrument is on its own MIDI
track *and* channel), so every part lands ready to assign.

## Track → plugin mapping

| # | Track | Load this | Notes |
|---|-------|-----------|-------|
| 1 | Lead Vocal | *(guide only)* | it's the sung melody — mute it, or sing over it |
| 2 | **Solo Guitar** | sfizz → **Neural Amp Modeler** | see below — this is the money track |
| 3 | Harmony Guitar | same chain as solo | thirds on the last solo phrase |
| 4 | Rhythm Guitar | sfizz → **Guitarix** (`gx_*`) or Ratatouille | power-chord chugs |
| 5 | Clean Guitar | sfizz → light Guitarix amp | intro/verse arpeggios |
| 6 | Bass | **sfizz** + FingerBassYR | |
| 7 | Piano | **sfizz** + Salamander Grand | |
| 8 | Organ | **setBfree** (`b_synth`) + `b_whirl` | real tonewheel B3 + Leslie |
| 9 | Strings | Surge XT, or GM Synth w/ a soundfont | no free orchestral lib installed yet |
| 10 | Drums | **AVL Drums** (`avldrums.lv2`) | Black Pearl or Red Zeppelin kit |

The MIDI drums use standard GM mapping (36 kick, 38 snare, 42/46 hats,
49 crash, 51 ride, 41/45/48 toms), which is what AVL Drums expects — it
should line up with no remapping.

## The guitar chain (the important bit)

The sample library is a **DI/direct** electric guitar — deliberately dry,
with no amp on it. That's the point: you supply the amp.

```
sfizz  (EGuitarFSBS-bridge-direct-20220911.sfz)
  → Neural Amp Modeler   ← load a .nam capture
  → (optional) Ratatouille for cab IR
```

Neural Amp Modeler ships with no captures. Grab free ones from
**https://tonehunt.org** — a cranked British/Marshall-style capture suits
this track. Drop the `.nam` file anywhere and point NAM at it.

Guitarix is the zero-download alternative: `gx_*` plugins are self-contained
amp/cab models, no captures needed.

The solo already has pitch-bend articulation written in (bend into every
note ≥ a quarter, vibrato fading in on sustains) — that expression is what
sells a lead once there's a real amp behind it.

## Sample libraries

`~/Music/sample-libraries/`

- `SalamanderGrandPianoV3_44.1khz16bit/` — 1.2 GB, load `SalamanderGrandPianoV3.sfz`
- `EGuitarFSBS-bridge-direct-SFZ+FLAC-.../` — 94 MB, clean electric DI
- `FingerBassYR SFZ+FLAC-.../` — 3.3 MB, fingered electric bass

All are SFZ — load them into **sfizz**.

## Mixing plugins worth knowing

- **LSP** — pro-grade EQ / compressor / limiter / gate. The workhorse.
- **Calf** — friendlier UI, good bus compressor
- **Dragonfly Reverb** — Hall / Plate / Room / Early Reflections
- **ChowTapeModel** — tape saturation; glues the drum bus and master
- **master_me** — automatic mastering chain for the final bus
- **x42**, **Airwindows**, **ZamPlugins** — meters, colour, utilities

## Audio performance — already optimal

Checked, no action needed:

- **Realtime scheduling: working.** `rtkit-daemon` is active and PipeWire's
  `pw-data-loop` threads run `SCHED_RR` priority 20. You do *not* need to
  join the `audio` group or edit limits.conf on this system.
- **PipeWire buffer: fine.** min-quantum is 32, so Ardour can negotiate
  low latency itself. (The `min-quantum = 1024` line in pipewire.conf is
  inside `vm.overrides` — VM-only, doesn't apply here.)
- **Sandbox: fine.** Ardour and Carla already hold `home` and
  `xdg-run/pipewire-0`, so they reach your files and the audio server.

In Ardour choose the **JACK** backend — it connects straight to PipeWire.

### The two things that DO need sudo

```bash
# 1. CPU governor is 'powersave'; 'performance' reduces xruns
sudo apt install linux-tools-common linux-tools-generic
sudo cpupower frequency-set -g performance

# 2. Disk is 94% full (29 GB left). Audio projects eat space fast.
```

To reclaim ~890 MB right now, the OMR virtualenv is fully regenerable:

```bash
rm -rf ~/Music/oof-gozal/omr/.venv     # rebuild later: cd omr && uv sync
```
