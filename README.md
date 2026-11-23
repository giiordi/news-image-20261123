# The Monday Ledger

A one-page newspaper front page that sums up 23 November 2026 in a single
image: the Gulf war reaching U.S. bases in Bahrain, attacks on shipping in
the Strait of Hormuz, the Geneva talks on the Ukraine peace plan, the
collapse of COP31, the killing of Hezbollah's chief of staff in Beirut,
and a factory fire in Indonesia — plus a schematic map of the Gulf, a
bar chart of reported attacks on shipping, and the day in numbers. It is
drawn entirely by a standard-library-only Python program (`main.py`) with
a hand-designed 5x7 bitmap font and a from-scratch PNG encoder, so every
run produces the same deterministic 1024x1024 image.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, deterministic across runs).

https://make.fun/?ref=v0wjehd6
