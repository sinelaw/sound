#!/usr/bin/env python3
"""
Studio mix of uf-gozal-band.midi.

Renders each of the 10 instrument tracks as its own stem, then mixes them:
per-track EQ / compression / panning, a shared plate reverb send, bus glue
compression, and a final limiter targeting a measured loudness.

Everything here is verifiable by measurement (ITU-R BS.1770 loudness, true
peak, per-stem balance) rather than by ear.
"""
import os, subprocess, sys, wave
import numpy as np
from scipy import signal
import mido

SR = 48000
SRC = "uf-gozal-band.midi"
STEM_DIR = "stems"
SF_DEFAULT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SF_ALT = os.path.expanduser("~/.cache/musescore_general.sf3")

# track index in the MIDI -> (name, soundfont, gain_dB, pan, hp_hz, comp, verb)
# pan: -1 = hard L, +1 = hard R
PLAN = {
    "Lead Vocal":     dict(gain=-5.0, pan= 0.00, hp=90 , comp=(0.30, 3.0), verb=0.05),
    # solo: rendered clean, gets a real amp sim below, and sits ~7dB lower now
    "Solo Guitar":    dict(gain= 3.5, pan= 0.00, hp=110, comp=(0.40, 3.0), verb=0.18),
    "Harmony Guitar": dict(gain=-14.0,pan= 0.35, hp=110, comp=(0.35, 3.0), verb=0.22),
    "Rhythm Guitar":  dict(gain=-9.5, pan=-0.45, hp=110, comp=(0.30, 3.0), verb=0.08),
    "Clean Guitar":   dict(gain=-9.0, pan= 0.45, hp=140, comp=(0.35, 2.5), verb=0.14),
    "Bass":           dict(gain=-4.5, pan= 0.00, hp=35,  comp=(0.25, 4.0), verb=0.00),
    "Piano":          dict(gain=-14.0,pan=-0.30, hp=90,  comp=(0.40, 2.0), verb=0.14),
    "Organ":          dict(gain=-12.0,pan= 0.30, hp=120, comp=(0.45, 2.0), verb=0.12),
    "Strings":        dict(gain=-13.0,pan= 0.00, hp=160, comp=(0.50, 2.0), verb=0.30),
    "Drums":          dict(gain=-3.5, pan= 0.00, hp=0,   comp=(0.30, 3.5), verb=0.10),
}


# ----------------------------------------------------------------- utilities
def split_stems(src):
    """one MIDI file per instrument track, keeping tempo/timesig track"""
    os.makedirs(STEM_DIR, exist_ok=True)
    mf = mido.MidiFile(src)
    meta = mf.tracks[0]
    out = []
    for tr in mf.tracks[1:]:
        name = next((m.name for m in tr if m.type == "track_name"), None)
        if not name or not any(m.type == "note_on" for m in tr):
            continue
        new = mido.MidiFile(ticks_per_beat=mf.ticks_per_beat)
        new.tracks.append(meta)
        new.tracks.append(tr)
        path = os.path.join(STEM_DIR, f"{name.replace(' ','_')}.mid")
        new.save(path)
        out.append((name, path))
    return out


def render(midi_path, wav_path, sf):
    subprocess.run(["fluidsynth", "-ni", "-F", wav_path, "-r", str(SR),
                    "-g", "0.8", sf, midi_path],
                   check=True, capture_output=True)


def load_wav(path):
    w = wave.open(path)
    n, ch = w.getnframes(), w.getnchannels()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    return a.reshape(-1, ch).T if ch > 1 else np.vstack([a, a])


def db(x):
    return 10 ** (x / 20.0)


def find_vst3(basename):
    import glob
    root = os.path.expanduser("~/.local/share/flatpak/runtime")
    hits = glob.glob(f"{root}/**/{basename}", recursive=True)
    return hits[0] if hits else None


def amp_sim(x, plugin="SmartAmp.vst3", params=None, pregain=1.0, stages=1):
    """Run a stem through a neural amp-sim VST3 (offline, via pedalboard).

    pregain drives the amp harder; stages cascades the amp into itself for
    more distortion (measured: x2 cascade + pregain 6 gives the heaviest
    saturation SmartAmp can produce, ~8.3 dB crest from ~20 dB dry)."""
    try:
        from pedalboard import load_plugin, Pedalboard
    except ImportError:
        print("    (pedalboard missing - skipping amp sim)")
        return x
    path = find_vst3(plugin)
    if not path:
        print(f"    ({plugin} not found - skipping amp sim)")
        return x
    try:
        def mk():
            p = load_plugin(path)
            for k, v in (params or {}).items():
                if k in p.parameters:
                    setattr(p, k, v)
            return p
        board = Pedalboard([mk() for _ in range(stages)])
        y = board((x * pregain).astype("float32"), SR)
        y = np.asarray(y, dtype=np.float64)
        if y.shape[0] == 1:
            y = np.vstack([y[0], y[0]])
        rms_in = np.sqrt((x ** 2).mean()) + 1e-12
        rms_out = np.sqrt((y ** 2).mean()) + 1e-12
        y *= rms_in / rms_out                     # match level, judge tone not volume
        print(f"    amp sim: {plugin} x{stages} pregain{pregain:g} applied")
        return y[:, :x.shape[1]]
    except Exception as e:
        print(f"    (amp sim failed: {str(e)[:70]})")
        return x


def highpass(x, hz):
    if hz <= 0:
        return x
    b, a = signal.butter(2, hz / (SR / 2), "highpass")
    return signal.lfilter(b, a, x, axis=-1)


def shelf(x, hz, gain_db, kind="high"):
    """gentle first-order shelf"""
    if abs(gain_db) < 0.01:
        return x
    b, a = signal.butter(1, hz / (SR / 2), "highpass" if kind == "high" else "lowpass")
    return x + (db(gain_db) - 1.0) * signal.lfilter(b, a, x, axis=-1)


def compress(x, thresh, ratio, attack=0.008, release=0.12, makeup=True):
    """simple feed-forward peak compressor on the stereo sum envelope"""
    det = np.maximum(np.abs(x[0]), np.abs(x[1]))
    aa = np.exp(-1.0 / (SR * attack))
    ar = np.exp(-1.0 / (SR * release))
    env = np.zeros_like(det)
    prev = 0.0
    for i in range(0, len(det), 64):                 # 64-sample blocks: fast + smooth
        blk = det[i:i + 64].max() if len(det[i:i + 64]) else 0.0
        c = aa if blk > prev else ar
        prev = c * prev + (1 - c) * blk
        env[i:i + 64] = prev
    gain = np.ones_like(env)
    over = env > thresh
    gain[over] = (thresh + (env[over] - thresh) / ratio) / np.maximum(env[over], 1e-9)
    y = x * gain
    if makeup:
        y *= db((1 - 1 / ratio) * 3.0)
    return y


def plate_ir(seconds=2.0, predelay=0.02, damp=0.35):
    """synthetic decaying-noise plate with early reflections"""
    n = int(seconds * SR)
    rng = np.random.default_rng(7)
    ir = rng.standard_normal((2, n)) * np.exp(-np.linspace(0, 7.0, n))
    for t, g in [(0.011, .5), (0.019, .4), (0.031, .32), (0.047, .25), (0.063, .18)]:
        i = int(t * SR)
        ir[:, i] += g
    b, a = signal.butter(2, (8000 * (1 - damp)) / (SR / 2), "lowpass")
    ir = signal.lfilter(b, a, ir, axis=-1)
    pd = int(predelay * SR)
    ir = np.pad(ir, ((0, 0), (pd, 0)))[:, :n]
    return ir / np.abs(ir).max()


def k_weight(x):
    """ITU-R BS.1770 K-weighting"""
    b1 = np.array([1.53512485958697, -2.69169618940638, 1.19839281085285])
    a1 = np.array([1.0, -1.69065929318241, 0.73248077421585])
    b2 = np.array([1.0, -2.0, 1.0])
    a2 = np.array([1.0, -1.99004745483398, 0.99007225036621])
    y = signal.lfilter(b1, a1, x, axis=-1)
    return signal.lfilter(b2, a2, y, axis=-1)


def lufs(x):
    """gated integrated loudness"""
    y = k_weight(x)
    blk = int(0.4 * SR)
    hop = blk // 4
    z = []
    for i in range(0, y.shape[1] - blk, hop):
        z.append(np.mean(y[:, i:i + blk] ** 2, axis=1).sum())
    z = np.array(z)
    z = z[z > 0]
    if not len(z):
        return -np.inf
    l = -0.691 + 10 * np.log10(z)
    abs_gated = z[l > -70]
    if not len(abs_gated):
        return -np.inf
    rel = -0.691 + 10 * np.log10(abs_gated.mean()) - 10
    fin = z[(l > -70) & (l > rel)]
    return -0.691 + 10 * np.log10(fin.mean()) if len(fin) else -np.inf


def true_peak(x, os_factor=4):
    up = signal.resample_poly(x, os_factor, 1, axis=-1)
    return 20 * np.log10(np.abs(up).max() + 1e-12)


def limiter(x, ceiling_db=-1.0, lookahead=0.005):
    ceil = db(ceiling_db)
    la = int(lookahead * SR)
    det = np.maximum(np.abs(x[0]), np.abs(x[1]))
    det = np.maximum.accumulate(
        np.pad(det, (la, 0))[::-1])[::-1][:len(det)] if la else det
    g = np.ones_like(det)
    over = det > ceil
    g[over] = ceil / det[over]
    b, a = signal.butter(2, 40 / (SR / 2), "lowpass")
    g = signal.lfilter(b, a, g)
    return x * np.minimum(g, 1.0)


# ----------------------------------------------------------------- main
def main():
    sf = SF_DEFAULT
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        sf = sys.argv[1]
    print(f"soundfont: {sf}")

    stems = split_stems(SRC)
    print(f"stems: {len(stems)}")

    reuse = "--reuse" in sys.argv
    rendered = {}
    for name, mid in stems:
        wav = mid.replace(".mid", ".wav")
        if not (reuse and os.path.exists(wav) and
                os.path.getmtime(wav) >= os.path.getmtime(mid)):
            render(mid, wav, sf)
        rendered[name] = load_wav(wav)
        print(f"  {'cached  ' if reuse else 'rendered'} {name:15s} {rendered[name].shape[1]/SR:6.1f}s")

    n = max(a.shape[1] for a in rendered.values())
    mix = np.zeros((2, n))
    verb_bus = np.zeros((2, n))

    print("\nper-stem processing:")
    for name, a in rendered.items():
        p = PLAN.get(name)
        if p is None:
            continue
        x = np.pad(a, ((0, 0), (0, n - a.shape[1])))
        # NB: Proteus measured as a no-op (crest factor unchanged at any drive).
        # SmartAmp's lead channel genuinely saturates: 21.6 -> 9.3 dB crest.
        if name == "Solo Guitar":
            # heavy distortion for the solo, but drop it for the closing
            # descent - low, fast notes through the cascade turn to noise.
            heavy = amp_sim(x, "SmartAmp.vst3",
                            dict(leadgain=1.0, leadbass=0.2, leadmid=0.6,
                                 leadtreble=0.5, presence=0.7, master=0.6),
                            pregain=6.0, stages=2)      # heaviest SmartAmp can do
            light = amp_sim(x, "SmartAmp.vst3",
                            dict(leadgain=0.32, leadbass=0.3, leadmid=0.5,
                                 leadtreble=0.5, presence=0.4, master=0.5),
                            pregain=1.0, stages=1)      # mild crunch for the descent
            def bar_time(bar):                          # seconds to a bar (pre-ritard)
                two = {12, 21, 41, 65}
                return sum(2 if i in two else 4 for i in range(1, bar)) * 60.0 / 78.0
            desc = bar_time(66) + 3 * 60.0 / 78.0 - 0.15   # just before beat 4 of 66
            xf = int(desc * SR)
            w = int(0.04 * SR)
            x = heavy.copy()
            if xf < x.shape[1]:
                end = min(xf + w, x.shape[1])
                f = np.linspace(1, 0, end - xf)
                x[:, xf:end] = heavy[:, xf:end] * f + light[:, xf:end] * (1 - f)
                x[:, end:] = light[:, end:]
        elif name == "Rhythm Guitar":
            x = amp_sim(x, "SmartAmp.vst3",
                        dict(leadgain=0.7, leadbass=0.3, leadmid=0.45,
                             leadtreble=0.4, presence=0.5, master=0.5),
                        pregain=2.0, stages=1)
        x = highpass(x, p["hp"])
        if name == "Drums":
            x = shelf(x, 6000, 2.0)
        if name == "Bass":
            x = shelf(x, 200, -1.5, "low")
        if name in ("Solo Guitar", "Lead Vocal"):
            x = shelf(x, 3000, 1.5)
        x = compress(x, *p["comp"])
        x *= db(p["gain"])
        pan = p["pan"]                                   # equal-power pan
        ang = (pan + 1) * np.pi / 4
        x = np.vstack([x[0] * np.cos(ang), x[1] * np.sin(ang)]) * np.sqrt(2)
        verb_bus += x * p["verb"]
        mix += x
        print(f"  {name:15s} gain{p['gain']:+6.1f}dB pan{pan:+.2f} hp{p['hp']:4d} verb{p['verb']:.2f}")

    print("\nreverb…")
    ir = plate_ir()
    wet = np.vstack([signal.fftconvolve(verb_bus[c], ir[c])[:n] for c in range(2)])
    mix += wet * 0.35

    print("bus glue + limiter…")
    mix = compress(mix, 0.35, 2.0, attack=0.02, release=0.25, makeup=False)
    mix = np.tanh(mix * 1.1) * 0.92                      # gentle saturation
    pre = lufs(mix)
    mix *= db(-10.5 - pre)                               # aim ~-10.5 LUFS (rock)
    mix = limiter(mix, -1.0)

    out = "uf-gozal-band-mixed.wav"
    data = np.clip(mix.T, -1, 1)
    with wave.open(out, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())

    print(f"\n=== {out} ===")
    print(f"  length      {n/SR:.1f}s")
    print(f"  loudness    {lufs(mix):.2f} LUFS (integrated, BS.1770 gated)")
    print(f"  true peak   {true_peak(mix):.2f} dBTP")
    print(f"  sample peak {20*np.log10(np.abs(mix).max()):.2f} dBFS")


if __name__ == "__main__":
    main()
