# Contributing

Issues and pull requests are welcome. This is one small file, so the bar is
simple: keep each change focused on one thing, and say why in the description.

## Getting set up

```sh
pip install -r requirements.txt
python3 mechkeys.py --list
```

## Adding a sound pack

New packs are the most welcome contribution. A pack is a function that takes a
key and returns a float32 numpy array:

```python
def pack_yours(key):
    f = key_note(key)
    dur = 0.2
    t = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * f * t)
    return w * adsr(dur) * 0.8
```

Add it to `PACKS` with a one line description and it becomes a CLI choice
automatically.

Keep the peak amplitude at or below roughly 1.0. The mixer clips at that point,
and a pack that clips on every keystroke sounds broken rather than loud.

## Before opening a pull request

- Run it and type for a while, including fast typing, so overlapping notes are
  actually exercised.
- Keep it dependency free beyond numpy, sounddevice, and pynput.
- Do not add anything that writes keystrokes to disk or sends them over the
  network. The README makes a promise that this program only ever turns a key into
  a pitch, and that promise is the reason it is safe to grant it Input Monitoring.

Issues labelled `good first issue` are self contained and a good place to start.
