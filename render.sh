#!/usr/bin/env bash
#
# Uf Gozal - full render pipeline, start to finish.
#
#   ./render.sh              rebuild everything (score -> arrangement -> mix)
#   ./render.sh --fast       reuse cached instrument stems (much quicker)
#   ./render.sh --score-only just re-engrave the PDF + plain MIDI
#
# Produces:
#   uf-gozal-v2.pdf / .midi        engraved lead sheet + plain melody+chords
#   uf-gozal-band.midi             10-track rock band arrangement
#   uf-gozal-band-mixed.wav/.mp3   mixed + mastered
#
set -euo pipefail
cd "$(dirname "$0")"

FAST=""; SCORE_ONLY=""
for a in "$@"; do
  case "$a" in
    --fast)       FAST="--reuse" ;;
    --score-only) SCORE_ONLY=1 ;;
    -h|--help)    sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "MISSING: $1 ($2)" >&2; exit 1; }; }

say "checking tools"
need lilypond  "sudo apt install lilypond"
need fluidsynth "sudo apt install fluidsynth"
need ffmpeg    "sudo apt install ffmpeg"
need uv        "https://docs.astral.sh/uv/"
[ -d omr ] || { echo "MISSING: ./omr uv project (python deps live there)" >&2; exit 1; }
echo "  all present"

say "1/4  engraving score + base MIDI (LilyPond)"
lilypond -o uf-gozal-v2 uf-gozal-v2.ly 2>&1 | grep -Ei "error|barcheck" && {
  echo "LilyPond reported problems - aborting" >&2; exit 1; } || true
echo "  uf-gozal-v2.pdf / uf-gozal-v2.midi"

if [ -n "$SCORE_ONLY" ]; then say "done (score only)"; exit 0; fi

say "2/4  building band arrangement"
uv run --project omr python arrange-band.py

say "3/4  rendering stems + mixing"
# needs: mido, numpy, scipy, pedalboard  (all in ./omr)
uv run --project omr python mix-studio.py $FAST

say "4/4  encoding mp3"
ffmpeg -y -loglevel error -i uf-gozal-band-mixed.wav \
       -codec:a libmp3lame -b:a 256k uf-gozal-band-mixed.mp3
echo "  uf-gozal-band-mixed.mp3"

say "done"
ls -lh uf-gozal-band-mixed.mp3 uf-gozal-band.midi uf-gozal-v2.pdf 2>/dev/null | awk '{print "  "$5"\t"$9}'

cat <<'TIP'

Tweaking:
  arrange-band.py   notes, drum patterns, embellishments, the solo
  mix-studio.py     PLAN{} = per-track gain / pan / EQ / compression / reverb
                    amp_sim() calls pick the guitar amp VST3
  Re-run with --fast after mix-only changes to skip re-rendering stems.
TIP
