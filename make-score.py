#!/usr/bin/env python3
"""Generate an orchestral-style multi-staff PDF score from the band MIDI."""
import sys
from music21 import converter, instrument, tempo, meter, key, environment

us = environment.UserSettings()
us['lilypondPath'] = '/usr/bin/lilypond'

NAMES = {
    'Lead Vocal': ('Electric Piano', instrument.ElectricPiano),
    'Solo Guitar': ('Solo Guitar', instrument.ElectricGuitar),
    'Rhythm Guitar': ('Rhythm Guitar', instrument.ElectricGuitar),
    'Clean Guitar': ('Clean Guitar', instrument.ElectricGuitar),
    'Bass': ('Bass', instrument.ElectricBass),
    'Piano': ('Piano', instrument.Piano),
    'Organ': ('Organ', instrument.Organ),
    'Strings': ('Strings', instrument.StringInstrument),
    'Drums': ('Drums', instrument.Percussion),
}

print("parsing MIDI…")
s = converter.parse('uf-gozal-band.midi', quantizePost=True,
                    quarterLengthDivisors=(4, 3))   # 16th + triplet grid

print("cleaning parts…")
for p in list(s.parts):
    nm = p.partName
    if nm not in NAMES or not p.flatten().notes:
        s.remove(p); continue
    label, inst = NAMES[nm]
    p.partName = label; p.partAbbreviation = label[:4]

s.metadata.title = "עוף גוזל / Uf Gozal — band score"
s.metadata.composer = "Miki Gavrielov, arr."

print("writing PDF via LilyPond…")
s.write('lilypond.pdf', fp='uf-gozal-score')
print("done -> uf-gozal-score.pdf")
