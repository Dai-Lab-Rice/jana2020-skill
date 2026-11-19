#!/usr/bin/env python
"""
filter_m90_wavelength.py - Filter a Jana2020 TOF .m90 reflection file by wavelength or d-spacing.

Matches reflections against the companion 22-column Mantid TOPAZ/Corelli .hkl file
(where column 18 is wavelength lambda [A] and column 19 is d-spacing [A]),
filters out reflections outside the specified bounds, re-indexes the trailing
sequence column as (idx * 1000 + 1), and updates `nref` in the .m90 header.

Usage:
  C:\\Users\\hplfz\\miniconda3\\python.exe filter_m90_wavelength.py \\
      --hkl path/to/data.hkl \\
      --m90-in path/to/template.m90 \\
      --m90-out path/to/active.m90 \\
      --max-lambda 1.8
"""

import argparse
import os
import sys


def filter_m90(hkl_path, m90_in, m90_out, min_lambda=0.0, max_lambda=999.0, min_d=0.0, max_d=999.0):
    with open(hkl_path, 'r', errors='ignore') as f:
        hkl_lines = [l.strip() for l in f if l.strip()]

    # Build lookup by (h, k, l) list in file order, and also direct line index
    hkl_records = []
    for l in hkl_lines:
        parts = l.split()
        if len(parts) >= 20:
            try:
                h, k, l_idx = int(parts[0]), int(parts[1]), int(parts[2])
                if h == 0 and k == 0 and l_idx == 0:
                    continue
                lam = float(parts[18])
                d_sp = float(parts[19])
                hkl_records.append((h, k, l_idx, lam, d_sp))
            except ValueError:
                pass

    with open(m90_in, 'r', errors='ignore') as f:
        m90_all = f.readlines()

    header = []
    data_lines = []
    in_data = False
    for l in m90_all:
        if l.strip().startswith('Data'):
            in_data = True
            header.append(l)
        elif not in_data:
            header.append(l)
        else:
            if l.strip():
                data_lines.append(l)

    # Map (h, k, l) queue for exact matching when systematic extinctions were removed
    from collections import defaultdict, deque
    hkl_queue = defaultdict(deque)
    for h, k, l_idx, lam, d_sp in hkl_records:
        hkl_queue[(h, k, l_idx)].append((lam, d_sp))

    filtered = []
    idx = 1
    for i, line in enumerate(data_lines):
        parts = line.split()
        h, k, l_idx = int(parts[0]), int(parts[1]), int(parts[2])
        if hkl_queue[(h, k, l_idx)]:
            lam, d_sp = hkl_queue[(h, k, l_idx)].popleft()
        elif i < len(hkl_records):
            _, _, _, lam, d_sp = hkl_records[i]
        else:
            continue

        if (min_lambda <= lam <= max_lambda) and (min_d <= d_sp <= max_d):
            last_tok = parts[-1]
            prefix = line[:line.rfind(last_tok)]
            new_line = f"{prefix}{idx * 1000 + 1}\n"
            filtered.append(new_line)
            idx += 1

    new_header = []
    for l in header:
        if l.startswith('nref'):
            parts = l.split()
            parts[1] = str(len(filtered))
            new_header.append(' '.join(parts) + '\n')
        else:
            new_header.append(l)

    with open(m90_out, 'w') as f:
        f.writelines(new_header + filtered)

    print(
        f"Filtered {m90_in} -> {m90_out}: {len(filtered)} / {len(data_lines)} reflections retained "
        f"(lambda in [{min_lambda}, {max_lambda}] A, d in [{min_d}, {max_d}] A)."
    )


def main():
    parser = argparse.ArgumentParser(description="Filter a Jana2020 .m90 file by wavelength or d-spacing.")
    parser.add_argument("--hkl", required=True, help="Path to 22-column Mantid .hkl file.")
    parser.add_argument("--m90-in", required=True, help="Input template .m90 file.")
    parser.add_argument("--m90-out", required=True, help="Output filtered .m90 file.")
    parser.add_argument("--min-lambda", type=float, default=0.0, help="Minimum wavelength [A].")
    parser.add_argument("--max-lambda", type=float, default=999.0, help="Maximum wavelength [A].")
    parser.add_argument("--min-d", type=float, default=0.0, help="Minimum d-spacing [A].")
    parser.add_argument("--max-d", type=float, default=999.0, help="Maximum d-spacing [A].")
    args = parser.parse_args()

    filter_m90(
        args.hkl, args.m90_in, args.m90_out,
        min_lambda=args.min_lambda, max_lambda=args.max_lambda,
        min_d=args.min_d, max_d=args.max_d
    )


if __name__ == "__main__":
    main()
