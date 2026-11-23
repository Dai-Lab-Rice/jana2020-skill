"""Parse SNS TOF nuclear exports and join observations by native identity."""
import argparse
import csv
import math
import re
from collections import Counter

HKL_LAYOUTS = ("sns-tof-hkl", "corelli-garnet")


def add_hkl_arguments(parser):
    parser.add_argument("--hkl", required=True, help="Companion 22-field SNS TOF nuclear export")
    parser.add_argument(
        "--hkl-layout", required=True, choices=HKL_LAYOUTS,
        help="Use sns-tof-hkl for the verified nuclear export (corelli-garnet is an alias)",
    )
    parser.add_argument("--observations", help="CSV: sequence,h,k,l,wavelength_A,d_A")


def fixed_hkl(line):
    fields = [line[start:start + 4].strip() for start in (0, 4, 8)]
    if len(line) < 12 or any(not re.fullmatch(r"[+-]?[0-9]+", field) for field in fields):
        raise ValueError("expected three four-character integer indices")
    return tuple(map(int, fields))


def mantid_records(path, layout):
    if layout not in HKL_LAYOUTS:
        raise ValueError(f"Unsupported HKL layout: {layout!r}")
    rows = []
    terminated = False
    with open(path) as f:
        for number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                if terminated:
                    raise ValueError("unexpected record after all-zero terminator")
                hkl = fixed_hkl(line.rstrip("\r\n"))
                payload = line[12:].split()
                if len(payload) != 19:
                    raise ValueError(
                        f"expected 19 payload fields, found {len(payload)}"
                        " (six-index satellite rows are unsupported)"
                    )
                values = list(map(float, payload))
                if not all(map(math.isfinite, values)):
                    raise ValueError("nonfinite HKL payload")
                if hkl == (0, 0, 0):
                    if any(values):
                        raise ValueError("expected an all-zero terminator for (0, 0, 0)")
                    terminated = True
                    continue

                lam, d = values[3], values[16]
                if lam <= 0 or d <= 0:
                    raise ValueError("wavelength and d-spacing must be positive")
                rows.append(dict(hkl=hkl, intensity=values[0], lam=lam, d=d))
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc

    if not rows:
        raise ValueError(f"{path}: no SNS TOF nuclear observations")
    return rows


def mapping(path):
    result = {}
    columns = {"sequence", "h", "k", "l", "wavelength_A", "d_A"}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or columns.difference(reader.fieldnames):
            raise ValueError(f"{path}: expected CSV columns sequence,h,k,l,wavelength_A,d_A")
        for row in reader:
            try:
                seq = int(row["sequence"])
                hkl = tuple(int(row[key]) for key in ("h", "k", "l"))
                lam, d = float(row["wavelength_A"]), float(row["d_A"])
                if seq in result or seq <= 0:
                    raise ValueError(f"duplicate/invalid observation sequence {seq}")
                if not all(math.isfinite(x) and x > 0 for x in (lam, d)):
                    raise ValueError("invalid mapped wavelength or d-spacing")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{reader.line_num}: {exc}") from exc
            result[seq] = dict(hkl=hkl, lam=lam, d=d)
    return result


def source_signature(record):
    return record["hkl"], round(record["lam"], 8), round(record["d"], 8)


def join(records, source, observations=None, *, allow_listing_subset=False):
    """Match full native sequence tags when a map is supplied, preserving native order."""
    tags = [record["sequence"] for record in records]
    if any(tag <= 0 for tag in tags):
        raise ValueError("Invalid native sequence tag")
    if len(set(tags)) != len(tags):
        raise ValueError("Duplicate native sequence tag")
    if len({tag % 1000 for tag in tags}) != 1:
        raise ValueError("Unsupported multiple data blocks")

    if observations is not None:
        explicit = mapping(observations)
        missing = set(tags).difference(explicit)
        if missing:
            raise ValueError(f"Missing observation map entry for native tag {min(missing)}")
        if not allow_listing_subset and set(explicit).difference(tags):
            raise ValueError("Extra mapped observation IDs")
        if Counter(map(source_signature, explicit.values())) != Counter(map(source_signature, source)):
            raise ValueError("Mapped observations do not match companion source wavelength/d multiset")
        matched = []
        for record in records:
            tag = record["sequence"]
            row = explicit[tag]
            if row["hkl"] != record["hkl"]:
                raise ValueError(f"Sequence/HKL mismatch for native tag {tag}")
            matched.append(dict(record, lam=row["lam"], d=row["d"]))
        return matched

    lookup = {row["hkl"]: row for row in source}
    if len(lookup) != len(source) or len({row["hkl"] for row in records}) != len(records):
        raise ValueError("Repeated HKL requires --observations sequence-keyed CSV")
    matched = []
    for record in records:
        hkl = record["hkl"]
        if hkl not in lookup:
            raise ValueError(f"Unmatched HKL {hkl} for native tag {record['sequence']}")
        row = lookup[hkl]
        matched.append(dict(record, lam=row["lam"], d=row["d"]))
    return matched


def legacy_m40(lines):
    """Validate the narrow layout supported by legacy parameter helpers."""
    try:
        n=int(lines[0].split()[0]);assert len(lines[0].split())==5
        assert len(lines[1].split())==7
        assert len(lines[2].split())==4
        assert len(lines[3].split())==7 and len(lines[4].split())==7
        for j in range(n):
            line=lines[5+2*j];assert len(line[:10].strip())>0
            # Fixed coordinate fields validate adjacent negative values too.
            assert int(line[10:11])>0 and int(line[11:14]) in (1,2)
            assert all(math.isfinite(float(line[k:k+9])) for k in range(18,54,9))
        assert 's.u. block' in lines[5+2*n]
    except (AssertionError,ValueError,IndexError) as e:
        raise ValueError('Unsupported M40 layout: requires legacy single-phase/single-scale, no commands preamble') from e
    return n
