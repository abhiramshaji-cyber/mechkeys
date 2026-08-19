# mechkeys

Synthesized keyboard sounds for macOS. Every keystroke plays a note, generated
from scratch at runtime. There are no samples and no audio files in this
repository.

Notes are mapped onto a minor pentatonic scale spanning four octaves, so whatever
you type stays musical rather than turning into noise.

## Sound packs

| Pack | Sound |
| --- | --- |
| `bass` | Deep sub bass punchy thud. The default. |
| `electro` | Distorted sawtooth stab with a pitch drop. |
| `retro` | 8 bit sci fi chirp with bit crush and grit. |
| `asmr` | Crystal bell shimmer built from inharmonic partials. |

## Install

```sh
pip install -r requirements.txt
```

macOS will ask for **Input Monitoring** permission the first time you run it,
under System Settings > Privacy & Security > Input Monitoring. Without it, no
keystrokes are seen and nothing plays.

## Usage

```sh
python3 mechkeys.py            # bass, the default
python3 mechkeys.py asmr       # pick a pack
python3 mechkeys.py --list     # list packs and exit
```

Press Ctrl+C to quit.

## What it does with your keystrokes

It listens globally, because that is the only way to react to typing in another
application. So it is worth being precise about what that means:

- A pressed key is converted to a single integer, which selects a pitch from the
  scale. That is the only use of the key.
- Nothing is stored, written to disk, or sent anywhere. There is no file output
  and no network code in this repository.
- Key releases are ignored, so it never sees a full keystroke sequence in the way
  a logger would.

It is one short file with no build step. Reading it end to end takes a couple of
minutes, and that is the intended way to satisfy yourself about the above.

## How the synthesis works

Each pack is a function that takes a key and returns a float32 waveform. Packs
build a waveform from sine, sawtooth, or square components, then shape it with an
ADSR envelope. `retro` quantises the waveform to seven levels for the bit crushed
character, `electro` sweeps the pitch down through an exponential decay, and
`asmr` stacks inharmonic partials with separate decay rates for a bell.

A small mixer runs one `sounddevice` output stream with a 256 frame block size
and sums overlapping notes in the audio callback, so fast typing layers instead of
cutting the previous note off.

## Adding a pack

Write a function that takes a key and returns a float32 numpy array, then add it
to the `PACKS` dictionary with a one line description. It becomes a CLI choice
automatically. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT. See [LICENSE](LICENSE).
