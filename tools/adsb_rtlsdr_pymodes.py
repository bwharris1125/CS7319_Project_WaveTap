#!/usr/bin/env python3
"""Experimental RTL-SDR -> pyModeS demodulator prototype.

This is a best-effort proof-of-concept. Demodulation in Python is hard to
make robust; this script implements a simple envelope/matched-filter based
preamble detector tuned for sample_rate=2e6 and then samples symbol windows
to form candidate messages which are handed to pyModeS for CRC/ICAO parsing.

Use this only for experimentation. For production use, a native demodulator
like dump1090 or gr-air-modes is strongly recommended.

Example:
  python tools/adsb_rtlsdr_pymodes.py --sample-rate 2000000 --gain 40

Requirements: pyrtlsdr, numpy, pyModeS
"""

from __future__ import annotations

import argparse
import time
from typing import List, Optional

import numpy as np

try:
    from rtlsdr import RtlSdr
except Exception as exc:  # pragma: no cover - runtime dependency
    raise RuntimeError("pyrtlsdr is required to run this script") from exc

try:
    import pyModeS as pms
except Exception as exc:  # pragma: no cover - runtime dependency
    raise RuntimeError("pyModeS is required to run this script") from exc


def bits_to_hex(bits: List[int]) -> str:
    """Convert list of bits (MSB first) to lowercase hex string (no 0x).

    bits: sequence of 0/1, length can be any; will be padded on the left to
    full bytes with leading zeros if needed.
    """
    if not bits:
        return ""
    bstr = "".join("1" if b else "0" for b in bits)
    # pad to full bytes
    pad = (-len(bstr)) % 8
    if pad:
        bstr = ("0" * pad) + bstr
    # convert to bytes
    val = int(bstr, 2)
    length = len(bstr) // 8
    raw = val.to_bytes(length, byteorder="big")
    return raw.hex()


def envelope(iq: np.ndarray, window: int) -> np.ndarray:
    """Compute a simple envelope (moving-average of magnitude).

    window: number of samples for the moving average.
    """
    mag = np.abs(iq)
    # use convolution for moving average
    kernel = np.ones(window, dtype=float) / float(window)
    env = np.convolve(mag, kernel, mode="same")
    return env


def estimate_freq_offset(iq: np.ndarray, fs: float) -> float:
    """Estimate the average frequency offset (Hz) from phase differences.

    Use the mean complex phase difference between adjacent samples to get a
    coarse frequency estimate. Works well for small offsets and is cheap.
    """
    if iq.size < 2:
        return 0.0
    prod = np.vdot(iq[:-1], iq[1:])  # sum conj(a)*b
    phase = np.angle(prod)
    # frequency in cycles per sample = phase / (2*pi)
    freq_hz = (phase / (2.0 * np.pi)) * fs
    return float(freq_hz)


def agc(iq: np.ndarray, target_rms: float = 1.0) -> np.ndarray:
    """Return IQ normalized by measured RMS to achieve target RMS.

    This is a simple AGC that scales the complex samples so the RMS of the
    magnitudes equals ``target_rms``.
    """
    mag = np.abs(iq)
    rms = float(np.sqrt(np.mean(mag * mag))) if mag.size else 1.0
    if rms <= 0:
        return iq
    return iq * (target_rms / rms)


def find_preambles(env: np.ndarray, sps: int, threshold: float) -> List[int]:
    """Find candidate preamble start indices using a simple matched filter.

    sps: samples per microsecond (samples per symbol)
    threshold: correlation threshold (relative)
    Returns indices in samples where a preamble is probably located.
    """
    # preamble has pulses at microsecond positions [0,1,3,4,6,7]
    # build template of length 8 us
    template = np.zeros(8 * sps, dtype=float)
    pulse_positions = [0, 1, 3, 4, 6, 7]
    for p in pulse_positions:
        start = p * sps
        template[start : start + sps] = 1.0

    # normalized cross-correlation (via convolution)
    corr = np.convolve(env, template[::-1], mode="same")
    # normalize by template energy and local energy
    t_energy = np.sum(template * template)
    if t_energy > 0:
        corr = corr / float(t_energy)

    # dynamic thresholding: use median + 3*std as floor if user threshold is
    # low
    if threshold <= 0.0:
        med = float(np.median(corr))
        std = float(np.std(corr))
        thresh = med + 3.0 * std
    else:
        thresh = float(threshold)

    # find peaks above threshold
    peaks = np.where(corr > thresh)[0]
    if peaks.size == 0:
        return []
    # compress contiguous regions to single indices
    groups = np.split(peaks, np.where(np.diff(peaks) != 1)[0] + 1)
    starts = [int(g[0]) for g in groups]
    return starts


def extract_bits(
    env: np.ndarray,
    env_or_samples: np.ndarray,
    start: int,
    sps: int,
    nbits: int,
    symbol_offset: int = 8,
) -> List[int]:
    """Extract nbits starting after a preamble at sample index ``start``.

    ``symbol_offset`` is the number of microseconds after the preamble
    end to start sampling (default 8 us). Returns a list of 0/1 ints.
    """
    bits: List[int] = []
    # env_or_samples may be either env (float) or complex samples; handle both
    is_complex = np.iscomplexobj(env_or_samples)
    first = start + symbol_offset * sps
    # compute local noise floor from a region before the preamble
    noise_idx = max(0, start - 8 * sps)
    if env_or_samples.size > 0 and noise_idx < start:
        noise_win = np.abs(env_or_samples[noise_idx:start])
    else:
        noise_win = np.array([0.0])
    noise_level = float(np.median(noise_win)) if noise_win.size else 0.0

    for i in range(nbits):
        center = int(first + i * sps + sps // 2)
        lo = max(0, center - sps // 2)
        hi = min(env_or_samples.size, center + sps // 2 + 1)
        w = env_or_samples[lo:hi]
        if w.size == 0:
            bits.append(0)
            continue
        if is_complex:
            val = float(np.mean(np.abs(w)))
        else:
            val = float(np.mean(w))
        # decide bit using noise_floor-based adaptive threshold
        thresh = max(
            0.5 * (noise_level + np.mean(np.abs(w))),
            noise_level + 1e-6,
        )
        bits.append(1 if val > thresh else 0)
    return bits


def try_decode_candidate(bits: List[int]) -> Optional[str]:
    """Try decoding candidate bits as Mode-S short and long frames.

    Returns ICAO hex string if successful, else None.
    """
    # try both 56-bit and 112-bit messages
    for nbits in (56, 112):
        if len(bits) < nbits:
            continue
        candidate = bits[:nbits]
        hexmsg = bits_to_hex(candidate)
        if not hexmsg:
            continue
        try:
            icao = pms.modeS.icao(hexmsg)
        except Exception:
            icao = None
        if icao:
            return icao
    return None


def main() -> None:
    """Capture IQ from an RTL-SDR and print decoded ICAO addresses.

    This is experimental and intended as a proof-of-concept only.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=2_000_000,
        help=("Sample rate in samples/sec. Recommended: 2000000."),
    )
    parser.add_argument(
        "--gain",
        type=float,
        default=40.0,
        help=("RTL-SDR gain in dB; set to a positive value or 0 for auto."),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="Preamble detection threshold (0..1)",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=256 * 1024,
        help="Samples per read",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=0,
        help="Exit after N decoded messages (0 = run forever)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity; show raw bits/hex for candidates",
    )
    args = parser.parse_args()

    sps = int(round(args.sample_rate / 1_000_000.0))  # samples per microsecond
    if sps < 1:
        raise SystemExit(
            "sample-rate too low; need >= 1e6 to get at least 1 sample/µs"
        )

    print("Starting experimental RTL-SDR capture")
    print(
        "sample_rate=%s, sps=%s, gain=%s, block_size=%s"
        % (args.sample_rate, sps, args.gain, args.block_size)
    )

    decoded = set()
    msg_count = 0

    sdr = RtlSdr()
    try:
        sdr.sample_rate = float(args.sample_rate)
        sdr.center_freq = 1090000000.0
        # gain: if <=0, set to 'auto' by letting method choose
        try:
            sdr.gain = float(args.gain)
        except Exception:
            sdr.gain = "auto"

        while True:
            samples = sdr.read_samples(args.block_size)
            env = envelope(samples, window=max(1, sps // 2))
            starts = find_preambles(env, sps=sps, threshold=args.threshold)
            for st in starts:
                # extract candidate bits (try long frame length)
                bits = extract_bits(env, st, sps=sps, nbits=112)
                # prepare hex candidates for display
                hex112 = bits_to_hex(bits[:112])
                hex56 = bits_to_hex(bits[:56])

                icao = try_decode_candidate(bits)

                if args.verbose:
                    # show summary: index, lengths and hex candidates
                    print(
                        "candidate@%d: bits=%d hex56=%s hex112=%s"
                        % (st, len(bits), hex56 or "-", hex112 or "-"),
                    )
                    if args.verbose > 1:
                        # show raw bitstring (truncate if too long)
                        bstr = "".join("1" if b else "0" for b in bits)
                        if len(bstr) > 256:
                            bstr = bstr[:256] + "..."
                        print("bits: %s" % bstr)

                if icao and icao not in decoded:
                    decoded.add(icao)
                    print(f"ICAO: {icao}")
                    msg_count += 1
                    if args.max_messages and msg_count >= args.max_messages:
                        return
            # small sleep to let the system breathe
            time.sleep(0.01)
    finally:
        sdr.close()


if __name__ == "__main__":
    main()
