#!/usr/bin/env python3
"""Adapt one Cheetah .spccl row + its per-candidate .fil into the
payload.bin + meta.msgpack pair consumed by kafka_producer_cli.

See kafka/docs/plans/2026-06-16-cheetah-real-candidate-adaptor-design.md
for the full design.
"""
from __future__ import annotations

SPCCL_HEADER = "MJD(decimal days)\tdm(dimensionless)\twidth(ms)\tsigma\tlabel"


def parse_spccl_row(path: str, row: int = 0) -> dict:
    """Read one candidate row from a Cheetah .spccl file.

    Returns a dict with keys mjd, dm, width, snr. width stays in
    milliseconds (pass-through). The leading 'label' column is dropped.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    if not lines or lines[0] != SPCCL_HEADER:
        raise ValueError(
            f"unexpected .spccl header in {path!r}; got {lines[0]!r}"
        )
    body = lines[1:]
    if row >= len(body):
        raise IndexError(f"row {row} not present in .spccl (only {len(body)} rows)")
    cols = [c.strip() for c in body[row].split("\t")]
    return {
        "mjd":   float(cols[0]),
        "dm":    float(cols[1]),
        "width": float(cols[2]),
        "snr":   float(cols[3]),
    }
