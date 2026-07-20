#!/usr/bin/env bash
#
# Uf Gozal - render pipeline.
#
# The ARRANGEMENT is now frozen as a committed MIDI "score": uf-gozal-band.midi.
# That file is the source of truth for the notes - edit it in a DAW / MIDI
# editor. This script's job is the MIX and TUNING (mix-studio.py): stems,
# amp-sims, EQ/compression/reverb, mastering.
#
#   ./render.sh              mix the committed score -> wav + mp3
#   ./render.sh --fast       reuse cached stems (quickest; mix-tuning changes)
#   ./render.sh --regen      rebuild the score from arrange-band.py first,
#                            then mix (use when changing the generated notes)
#   ./render.sh --score-only just re-engrave the lead-sheet PDF + base MIDI
#
set -euo pipefail
cd "$(dirname "$0")"

FAST=""; REGEN=""; SCORE_ONLY=""
for a in "$@"; do
  case "$a" in
    --fast)       FAST="--reuse" ;;
    --regen)      REGEN=1 ;;
    --score-only) SCORE_ONLY=1 ;;
    -h|--help)    sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "MISSING: $1 ($2)" >&2; exit 1; }; }

say "checking tools"
need lilypond   "sudo apt install lilypond"
need fluidsynth "sudo apt install fluidsynth"
need ffmpeg     "sudo apt install ffmpeg"
need uv         "https://docs.astral.sh/uv/"
[ -d omr ] || { echo "MISSING: ./omr uv project" >&2; exit 1; }
echo "  all present"

say "1/4  engraving score + base MIDI (LilyPond)"
lilypond -o uf-gozal-v2 uf-gozal-v2.ly 2>&1 | grep -Ei "error|barcheck" && {
  echo "LilyPond reported problems - aborting" >&2; exit 1; } || true
echo "  uf-gozal-v2.pdf / uf-gozal-v2.midi"

if [ -n "$SCORE_ONLY" ]; then say "done (score only)"; exit 0; fi

if [ -n "$REGEN" ]; then
  say "2/4  REGENERATING band score from arrange-band.py"
  uv run --project omr python arrange-band.py
else
  say "2/4  using committed score uf-gozal-band.midi (pass --regen to rebuild)"
  [ -f uf-gozal-band.midi ] || { echo "score missing; run with --regen" >&2; exit 1; }
fi

say "3/4  rendering stems + mixing (mix-studio.py)"
uv run --project omr python mix-studio.py $FAST

say "4/4  encoding mp3"
ffmpeg -y -loglevel error -i uf-gozal-band-mixed.wav \
       -codec:a libmp3lame -b:a 256k uf-gozal-band-mixed.mp3
echo "  uf-gozal-band-mixed.mp3"

say "done"
ls -lh uf-gozal-band-mixed.mp3 uf-gozal-band.midi uf-gozal-v2.pdf 2>/dev/null \
  | awk '{print "  "$5"\t"$9}'

cat <<'TIP'

Notes live in the score (uf-gozal-band.midi) - edit in a DAW, then ./render.sh.
Mixing/tuning lives in mix-studio.py (PLAN{} levels/pan/EQ, amp_sim() tone).
Regenerate the score from scratch with ./render.sh --regen (arrange-band.py).
TIP
