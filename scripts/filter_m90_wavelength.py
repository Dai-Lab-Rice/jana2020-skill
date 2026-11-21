"""Create single-block Jana E-format M90 sensitivity subsets from SNS TOF exports."""
import argparse
from decimal import Decimal
from pathlib import Path
import re

from observation_mapping import add_hkl_arguments, fixed_hkl, join, mantid_records


M90_WAVELENGTH = slice(62, 70)
M90_TRAILING_FIELDS = 118
M90_WAVELENGTH_HALF_UNIT = Decimal("0.00005")


def m90_record(path, number, line):
    try:
        hkl = fixed_hkl(line)
        wavelength = line[M90_WAVELENGTH].strip()
        if not re.fullmatch(r"[0-9]+\.[0-9]{4}", wavelength) or Decimal(wavelength) <= 0:
            raise ValueError("expected a positive incident wavelength at columns 63–70")
        tail = line[M90_TRAILING_FIELDS:]
        tag = re.search(r"(?:^|\s)([0-9]+)\s*$", tail)
        if not tag:
            raise ValueError("expected a trailing native sequence tag after the direction cosines")
    except ValueError as exc:
        raise ValueError(f"{path}:{number}: unsupported E-format M90 row: {exc}") from exc
    return dict(
        hkl=hkl, sequence=int(tag[1]), native_lambda=Decimal(wavelength),
        line=line, line_number=number,
        tag_start=M90_TRAILING_FIELDS + tag.start(1), tag_end=M90_TRAILING_FIELDS + tag.end(1),
    )


def filter_m90(
    hkl_path, m90_in, m90_out, min_lambda=0., max_lambda=999.,
    min_d=0., max_d=999., observations=None, *, hkl_layout,
):
    if Path(m90_in).resolve() == Path(m90_out).resolve():
        raise ValueError("Input overwrite is forbidden")
    with open(m90_in, newline="") as f:
        lines = f.readlines()
    starts = [i for i, line in enumerate(lines) if line.strip().startswith("Data")]
    if len(starts) != 1:
        raise ValueError("Filter requires exactly one data block")
    start = starts[0] + 1
    header = lines[:start]
    records = [
        m90_record(m90_in, number, line)
        for number, line in enumerate(lines[start:], start + 1) if line.strip()
    ]
    counts = [re.match(r"^(\s*nref\s+)([0-9]+)(?=\s|$)", line) for line in header]
    counts = [count for count in counts if count]
    if len(counts) != 1 or not records or int(counts[0][2]) != len(records):
        raise ValueError("Invalid input nref")

    matched = join(records, mantid_records(hkl_path, hkl_layout), observations)
    for row in matched:
        source_lambda = Decimal(str(row["lam"]))
        if abs(source_lambda - row["native_lambda"]) > M90_WAVELENGTH_HALF_UNIT:
            raise ValueError(
                f"{m90_in}:{row['line_number']}: wavelength mismatch for native tag "
                f"{row['sequence']} (HKL {row['hkl']}): "
                f"source {source_lambda} Å, M90 {row['native_lambda']} Å"
            )

    keep = [
        row for row in matched
        if min_lambda <= row["lam"] <= max_lambda and min_d <= row["d"] <= max_d
    ]
    output = []
    for i, row in enumerate(keep, 1):
        tag = str(i * 1000 + row["sequence"] % 1000)
        start, end = row["tag_start"], row["tag_end"]
        output.append(row["line"][:start] + tag.rjust(end - start) + row["line"][end:])

    header = [
        re.sub(r"^(\s*nref\s+)[0-9]+(?=\s|$)", lambda m: m[1] + str(len(keep)), line)
        for line in header
    ]
    with open(m90_out, "w", newline="") as f:
        f.writelines(header + output)
    print(f"Retained {len(keep)}/{len(records)}; source preserved.")
    return len(keep)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_hkl_arguments(parser)
    parser.add_argument("--m90-in", required=True)
    parser.add_argument("--m90-out", required=True)
    parser.add_argument("--min-lambda", type=float, default=0.)
    parser.add_argument("--max-lambda", type=float, default=999.)
    parser.add_argument("--min-d", type=float, default=0.)
    parser.add_argument("--max-d", type=float, default=999.)
    args = parser.parse_args()
    filter_m90(
        args.hkl, args.m90_in, args.m90_out,
        min_lambda=args.min_lambda, max_lambda=args.max_lambda,
        min_d=args.min_d, max_d=args.max_d, observations=args.observations,
        hkl_layout=args.hkl_layout,
    )


if __name__ == "__main__":
    main()
