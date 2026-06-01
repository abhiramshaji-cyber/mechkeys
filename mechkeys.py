#!/usr/bin/env python3
"""mechkeys — synthesized keyboard sounds for macOS"""

import sys
import threading
import argparse
import numpy as np
import sounddevice as sd
from pynput import keyboard

SR = 44100

# Pentatonic minor scale across 4 octaves — musically pleasant no matter which key is hit
_BASE = [65.41, 77.78, 87.31, 98.00, 116.54]
SCALE = [f * 2**o for o in range(4) for f in _BASE]

def key_note(key, mult=1.0):
    if hasattr(key, 'char') and key.char:
        n = ord(key.char.lower())
    elif hasattr(key, 'vk') and key.vk:
        n = key.vk
    else:
        n = 60
    return SCALE[n % len(SCALE)] * mult

def adsr(dur, a=0.005, d=0.08, s=0.0, r=0.04):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.where(
        t < a,
        t / max(a, 1e-9),
        np.where(
            t < a + d,
            1.0 - (1.0 - s) * (t - a) / max(d, 1e-9),
            np.where(
                t < dur - r,
                float(s),
                s * np.maximum(0.0, 1.0 - (t - (dur - r)) / max(r, 1e-9)),
            ),
        ),
    ).astype(np.float32)


# ── Packs ──────────────────────────────────────────────────────────────────

def pack_bass(key):
    f = key_note(key, 0.5)
    dur = 0.35
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = (0.70 * np.sin(2*np.pi*f*t)
       + 0.22 * np.sin(2*np.pi*2*f*t)
       + 0.08 * np.sin(2*np.pi*3*f*t))
    w = np.tanh(w * 2.0)
    return w * adsr(dur, a=0.006, d=0.20, s=0.0, r=0.12) * 0.85

def pack_electro(key):
    f = key_note(key, 1.5)
    dur = 0.20
    n = int(dur * SR)
    t = np.arange(n) / SR
    ft = f * np.exp(-t * 14)               # pitch drop
    phase = np.cumsum(ft) / SR
    w = 2 * (phase - np.floor(phase + 0.5))  # sawtooth
    w = np.tanh(w * 4.5)                    # heavy distortion
    w += 0.28 * np.sin(2*np.pi*(f*0.5)*t)  # sub layer
    return w * adsr(dur, a=0.002, d=0.11, s=0.0, r=0.07) * 0.72

def pack_retro(key):
    f = key_note(key, 2.0)
    dur = 0.18
    n = int(dur * SR)
    t = np.arange(n) / SR
    ft = f * (1.0 + 0.9 * np.exp(-t * 45))  # upward chirp on attack
    phase = np.cumsum(ft) / SR
    w = np.sign(np.sin(2*np.pi*phase))       # square wave
    levels = 7
    w = np.round(w * levels) / levels        # bit-crush
    w += 0.05 * np.random.randn(n)           # grit
    return w * adsr(dur, a=0.001, d=0.09, s=0.0, r=0.08) * 0.65

def pack_asmr(key):
    f = key_note(key, 4.0)
    dur = 0.65
    n = int(dur * SR)
    t = np.arange(n) / SR
    # Inharmonic bell-like partials (crystal / singing bowl feel)
    w = (0.55 * np.sin(2*np.pi*f        *t) * np.exp(-t * 6)
       + 0.28 * np.sin(2*np.pi*f*2.756  *t) * np.exp(-t * 11)
       + 0.12 * np.sin(2*np.pi*f*5.404  *t) * np.exp(-t * 20)
       + 0.05 * np.sin(2*np.pi*f*8.933  *t) * np.exp(-t * 32))
    w *= 1.0 + 0.03 * np.sin(2*np.pi*5*t)   # gentle shimmer
    return w * adsr(dur, a=0.002, d=0.38, s=0.0, r=0.25) * 0.95


PACKS = {
    'bass':    ('Deep sub-bass punchy thud',            pack_bass),
    'electro': ('Distorted sawtooth stab + pitch drop', pack_electro),
    'retro':   ('8-bit sci-fi chirp with bit-crush',    pack_retro),
    'asmr':    ('Crystal bell ASMR shimmer',            pack_asmr),
}


# ── Mixer ─────────────────────────────────────────────────────────────────

class Mixer:
    def __init__(self):
        self._q = []
        self._lock = threading.Lock()
        self._stream = sd.OutputStream(
            samplerate=SR, channels=1, dtype='float32',
            blocksize=256, callback=self._cb,
        )

    def _cb(self, out, frames, *_):
        buf = np.zeros(frames, np.float32)
        with self._lock:
            alive = []
            for arr, pos in self._q:
                end = min(pos + frames, len(arr))
                buf[:end - pos] += arr[pos:end]
                if end < len(arr):
                    alive.append((arr, end))
            self._q = alive
        np.clip(buf, -1.0, 1.0, out=buf)
        out[:, 0] = buf

    def play(self, arr):
        with self._lock:
            self._q.append((arr.astype(np.float32), 0))

    def __enter__(self):
        self._stream.start()
        return self

    def __exit__(self, *_):
        self._stream.stop()
        self._stream.close()


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='mechkeys — keyboard sound synthesizer')
    parser.add_argument('pack', nargs='?', default='bass', choices=list(PACKS.keys()),
                        help='Sound pack to use (default: bass)')
    parser.add_argument('--list', action='store_true', help='List packs and exit')
    args = parser.parse_args()

    if args.list:
        for name, (desc, _) in PACKS.items():
            print(f'  {name:<10}  {desc}')
        return

    _, synth = PACKS[args.pack]
    print(f'mechkeys  pack={args.pack}  (Ctrl+C to quit)')

    with Mixer() as mixer:
        def on_press(key):
            try:
                mixer.play(synth(key))
            except Exception:
                pass

        with keyboard.Listener(on_press=on_press) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                pass

    print('stopped.')

if __name__ == '__main__':
    main()
