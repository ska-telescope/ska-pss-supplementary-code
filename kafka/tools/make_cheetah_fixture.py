#!/usr/bin/env python3
"""Adapt one Cheetah .spccl row + its per-candidate .fil into the
payload.bin + meta.msgpack pair consumed by kafka_producer_cli.

See kafka/docs/plans/2026-06-16-cheetah-real-candidate-adaptor-design.md
for the full design.
"""
from __future__ import annotations

import struct

import msgpack

SPCCL_HEADER = "MJD(decimal days)\tdm(dimensionless)\twidth(ms)\tsigma\tlabel"

_F32_KEYS = ("dm", "width", "snr")


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


def _float32(x: float) -> float:
    """Round-trip through a 4-byte IEEE-754 float so msgpack picks FLOAT32."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def write_meta(path: str, meta: dict) -> None:
    """Write the SPCCL overrides map to *path* as msgpack.

    `dm`, `width`, `snr` are packed as float32 (matches
    SpcclOverrides::as<float>() on the C++ side). `mjd` is packed as
    float64. Keys absent from *meta* are simply not packed -- the
    producer falls back to its synthetic config defaults.
    """
    buf = bytearray()
    p_f32 = msgpack.Packer(use_single_float=True,  use_bin_type=True)
    p_f64 = msgpack.Packer(use_single_float=False, use_bin_type=True)
    buf += p_f64.pack_map_header(len(meta))
    for k, v in meta.items():
        buf += p_f64.pack(k)
        if k in _F32_KEYS:
            buf += p_f32.pack(_float32(v))
        else:
            buf += p_f64.pack(v)
    with open(path, "wb") as f:
        f.write(bytes(buf))
