#!/usr/bin/env python3
"""Write a payload.bin + meta.msgpack pair for the producer CLI.

Example:
    python kafka/tools/make_fixture.py \
        --payload-out /tmp/p.bin --meta-out /tmp/m.msgpack \
        --payload-size 1024 \
        --sbi sbi-real --beam beam-42 --mjd 60123.25 --dm 77.5
"""
import argparse
import os
import struct
import sys

import msgpack


def _float32(x: float) -> float:
    """Round-trip through a 4-byte IEEE-754 float so msgpack picks FLOAT32."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload-out", required=True,
                    help="where to write the payload blob")
    ap.add_argument("--meta-out",    required=True,
                    help="where to write the msgpack meta sidecar")
    ap.add_argument("--payload-size", type=int, default=2_300_000,
                    help="bytes of /dev/urandom to write (default: 2.3 MB)")
    ap.add_argument("--payload-from",
                    help="copy bytes from this file instead of /dev/urandom")
    ap.add_argument("--sbi",   dest="scheduling_block_id",
                    help="override SPCCL scheduling_block_id")
    ap.add_argument("--beam",  dest="beam_id",
                    help="override SPCCL beam_id")
    ap.add_argument("--mjd",   type=float,
                    help="override SPCCL mjd (packed as float64)")
    ap.add_argument("--dm",    type=float,
                    help="override SPCCL dm (packed as float32)")
    ap.add_argument("--width", type=float,
                    help="override SPCCL width (packed as float32)")
    ap.add_argument("--snr",   type=float,
                    help="override SPCCL snr (packed as float32)")
    args = ap.parse_args()

    # Payload
    if args.payload_from:
        with open(args.payload_from, "rb") as src, open(args.payload_out, "wb") as dst:
            dst.write(src.read())
    else:
        with open(args.payload_out, "wb") as dst:
            dst.write(os.urandom(args.payload_size))

    # Meta: only include keys the user set. float32 fields are pinned via
    # use_single_float=True; float64 keys (mjd) are packed with a separate
    # packer so both widths land correctly in one map.
    meta = {}
    if args.scheduling_block_id is not None: meta["scheduling_block_id"] = args.scheduling_block_id
    if args.beam_id             is not None: meta["beam_id"]             = args.beam_id
    if args.mjd   is not None: meta["mjd"]   = float(args.mjd)           # float64
    if args.dm    is not None: meta["dm"]    = _float32(args.dm)
    if args.width is not None: meta["width"] = _float32(args.width)
    if args.snr   is not None: meta["snr"]   = _float32(args.snr)

    # Build the map manually so we can pack each value with the correct width.
    # Pack map header, then key/value pairs individually.
    buf = bytearray()
    p_f32 = msgpack.Packer(use_single_float=True,  use_bin_type=True)
    p_f64 = msgpack.Packer(use_single_float=False, use_bin_type=True)
    # map header for N entries
    buf += p_f64.pack_map_header(len(meta))
    for k, v in meta.items():
        buf += p_f64.pack(k)
        if k in ("dm", "width", "snr"):
            buf += p_f32.pack(v)
        else:
            buf += p_f64.pack(v)

    with open(args.meta_out, "wb") as f:
        f.write(bytes(buf))

    return 0


if __name__ == "__main__":
    sys.exit(main())
