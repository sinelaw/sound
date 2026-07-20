\version "2.24.1"

%% עוף גוזל / Uf Gozal — transcribed from oof-orig.pdf (2-page lead sheet)
%% Melody + chord symbols, 63 measures. Key F major, 4/4, quarter = 78.
%% Structure: Intro(1-4) A(5-13) B(14-22, segno@14) C(23-29, To Coda@29)
%%            D(30-33, D.S. al Coda) Coda/E(34-41) F(42-50, guitar solo)
%%            G(51-54) (55-58 repeat w/ 1st+2nd endings) H(59-63)
%%
%% Pitches measured from the engraving (staff geometry + notehead detection);
%% melody written in ABSOLUTE octaves (c' = middle C) to keep them verifiable.

global = { \key f \major \time 4/4 \tempo 4 = 78 }

%% ---------------------------------------------------------------- MELODY

melIntro = {
  r8 c'8 a'8 g'8~ g'8 f'4.                                   |  % 1
  r8 bes8 g'8 f'8 a'8 g'8 f'8 g'8                            |  % 2
  f'8 c'8 a'8 g'8~ g'8 f'4.                                  |  % 3
  r8 bes8 g'8 f'8~ f'2                                       |  % 4
}

melA = {
  r8 c'8 c'8 c'16 d'16~ d'8 f'8 g'8 a'8                      |  % 5
  g'4~ g'16 f'16 d'16 f'16~ f'4 r4                           |  % 6
  r8 c'8 c'8 c'16 d'16~ d'8 f'4 d'16 c'16~                   |  % 7
  c'8 a8 r4 r2                                               |  % 8
  r8 a'16 a'16 a'8 a'16 g'16~ g'8 f'8 f'8 d'8                |  % 9
  d'4 d'8 a8 bes2                                            |  % 10
  r8 bes'16 bes'16 bes'8 bes'16 a'16~ a'4. f'16 f'16         |  % 11
  \time 2/4 g'8 a'8 g'8 f'8                                  |  % 12
  \time 4/4 f'8 d'8~ d'2 r4                                  |  % 13
}

melB = {
  r8 c'8 c'8 c'16 d'16~ d'8 f'8 g'8 a'8                      |  % 14
  g'4~ g'16 f'16 f'16 f'16~ f'4 r4                           |  % 15
  r8 c'8 c'8 c'16 d'16~ d'8 f'8 f'16 f'16 d'16 c'16~         |  % 16
  c'2 r2                                                     |  % 17
  r8 a'8 a'8 a'8 g'8 f'8 f'8 d'8                             |  % 18
  d'4 d'8 a16 bes16~ bes2                                    |  % 19
  r8 bes'8 bes'8 bes'16 a'16~ a'8. g'8 f'16 g'8              |  % 20
  \time 2/4 a'4 a'8 f'16 g'16~                               |  % 21
  \time 4/4 g'2 r4 r4                                        |  % 22
}

melC = {
  c''4. a'16 f'16~ f'4 r8 f'8                                |  % 23
  bes'8 bes'8 a'8 g'16 g'16~ g'8 f'8 r4                      |  % 24
  c''4. bes'16 a'16~ a'4 r8 d'8                              |  % 25
  bes'8 a'16 g'16~ g'2 r8 c''8                               |  % 26
  c''4. a'16 f'16~ f'4 r8 f'8                                |  % 27
  d''8 d''8 c''8 bes'16 bes'16~ bes'16 a'8. c''8 a'16 g'16~  |  % 28
  g'2. r4                                                    |  % 29
}

melD = {
  r8 c'8 a'8 g'8~ g'8 f'4.                                   |  % 30
  r8 bes8 g'8 f'8 a'8 g'8 f'8 g'8                            |  % 31
  f'8 c'8 a'8 g'8~ g'8 f'4.                                  |  % 32
  r8 bes8 g'8 f'8~ f'2                                       |  % 33
}

melCoda = {
  r8 d'8 d'8 d'16 e'16~ e'8 f'8 r8 c'8                       |  % 34
  a'8 a'8 a'8 g'16 f'16~ f'8 c'4.                            |  % 35
  r8 d'8 d'8 e'16 f'16~ f'8 g'8 f'8 e'8                      |  % 36
  c'2. r4                                                    |  % 37
  r8 bes'8 bes'8 f'16 bes'16~ bes'4. f'8                     |  % 38
  bes'8 c''8 a'8 g'8~ g'4 c'8 c'8                            |  % 39
  d''8 c''8 c''8 a'16 g'16~ g'4 r8 c'8                       |  % 40
  d''8 c''8 c''8 a'16 g'16~ g'4 c'16 c'16 d'16 f'16          |  % 41
}

%% guitar solo (42-50): pitches measured from the page; rhythms are a
%% close approximation of the printed beaming.
melSolo = {
  a'8 a'4. a'16 g'16 f'8 g'8 d'16 f'16                       |  % 42
  bes'16 b'16 a'16 a'16 a'16 a'16 a'16 a'16 c''16 b'16 c''8 bes'4 | % 43
  f'4 g'16 a'16 c''8 c''8 bes'8 a'8 bes'8                    |  % 44
  a'8~ a'8 c'16 d'16 f'16 g'16 a'16 c''16 d''16 f''16 a''8 a''8 | % 45
  f''8. e''16 f''8 e''16 f''16 f''16 e''16 f''8 f''8 f''8    |  % 46
  a'8 bes'8 c''8 bes'8 bes'16 d'16 g'16 d'16 bes'16 d'8.     |  % 47
  f'16 g'16 f'16 d'16 f'16 f'16 d'16 f'16 a'16 c''16 c''16 c''16 c''8 c''8 | % 48
  \time 2/4 c''16 bes'16 a'16 f'16 c'16 d'16 f'16 g'16       |  % 49
  \time 4/4 a'16 c''16 d''16 f''16 a''8. a''16 f''8 f''8 f''8 f''8 | % 50
}

melG = {
  c''4. a'16 f'16~ f'4 r8 f'8                                |  % 51
  bes'8 bes'8 a'8 g'16 g'16~ g'8 f'8 r4                      |  % 52
  c''4. bes'16 a'16~ a'4 r8 d'8                              |  % 53
  bes'8 a'16 g'16~ g'2 r8 c''8                               |  % 54
}

melRepBody = {
  c''4. a'16 f'16~ f'4 r8 f'8                                |  % 55
  d''8 d''8 c''8 bes'16 bes'16~ bes'16 a'8. c''8 a'8         |  % 56
}
melEndOne = { g'2. r8 c''8 }                                     % 57
melEndTwo = { g'1 }                                              % 58

melH = {
  r8 c'8 a'8 g'8~ g'8 f'4.                                   |  % 59
  r8 bes8 g'8 f'8 a'8 g'8 f'8 g'8                            |  % 60
  f'8 c'8 a'8 g'8~ g'8 f'4.                                  |  % 61
  r8 bes8 g'8 f'8~ f'8 d'4.                                  |  % 62
  c'2.\fermata r4                                            |  % 63
}

%% ---------------------------------------------------------------- CHORDS

chIntro = \chordmode { f1 | g2:m7 bes2/c | f1 | g2:m7 bes2/c }
chA = \chordmode {
  f1 | g2:m7 bes2/c | f2 bes2 | f1 |
  f2 bes2 | d2:7 g2:m | bes2 a2:m/c |
  \time 2/4 ees2 | \time 4/4 bes1
}
chB = \chordmode {
  f1 | g2:m7 bes2/c | f2 bes2 | f1 |
  f2 bes2 | d2:7 g2:m | bes2 c2 |
  \time 2/4 f2 | \time 4/4 g2:m7 f4/g g4:m7
}
chC = \chordmode {
  f2 f2:7 | bes2 f2 | f2 a2:m |
  g2:m7 bes2/c | f2 f2:7 | bes2 f2 | g1:m7
}
chD = \chordmode { f1 | g2:m7 bes2/c | f1 | g2:m7 bes2/c }
chCoda = \chordmode {
  d2:m c2 | f2 f2:7/a | bes2 c2 | f2 f2:7 |
  bes1 | c2 c2/bes | f2 g2:m7 | f2/a bes4 c4
}
chSolo = \chordmode {
  f1 | g2:m bes4 c4:7.5+ | f2 bes2 |
  f1 | f2 bes2 | d2:7 g2:m |
  bes2 c2:7 | \time 2/4 f2 | \time 4/4 g1:m7
}
chG = \chordmode { f2 f2:7 | bes2 f2 | f2 a2:m | g2:m7 bes2/c }
chRepBody = \chordmode { f2 f2:7 | bes2 f2 }
chEndOne = \chordmode { g1:m7 }
chEndTwo = \chordmode { g1:m7 }
chH = \chordmode {
  f2 d4:m7 f4/c | g2:m7 bes2/c | f2 d4:m7 f4/c | g2:m7 bes2/c | f1
}

%% ---------------------------------------------------------------- SCORES

melodyPrint = {
  \melIntro \melA \melB \melC \melD
  \melCoda \melSolo \melG
  \melRepBody \melEndOne \melEndTwo \melH
}
chordsPrint = {
  \chIntro \chA \chB \chC \chD
  \chCoda \chSolo \chG
  \chRepBody \chEndOne \chEndTwo \chH
}

\header {
  title = "עוף גוזל  (Uf Gozal)"
  composer = "Miki Gavrielov / מיקי גבריאלוב"
  poet = "Arik Einstein / אריק איינשטיין"
  tagline = ##f
}

\score {
  <<
    \new ChordNames \chordsPrint
    \new Staff { \global \melodyPrint }
  >>
  \layout { }
}

%% MIDI with the roadmap unfolded:
%% 1-13, 14-33, D.S.->14-29, Coda 34-56, ending1, 55-56, ending2, 59-63
melodyMidi = {
  \melIntro \melA \melB \melC \melD
  \melB \melC
  \melCoda \melSolo \melG
  \melRepBody \melEndOne
  \melRepBody \melEndTwo \melH
}
chordsMidi = {
  \chIntro \chA \chB \chC \chD
  \chB \chC
  \chCoda \chSolo \chG
  \chRepBody \chEndOne
  \chRepBody \chEndTwo \chH
}

\score {
  <<
    \new Staff { \set midiInstrument = "acoustic grand" \global \melodyMidi }
    \new Staff { \set midiInstrument = "acoustic guitar (steel)" \global \chordsMidi }
  >>
  \midi { }
}
