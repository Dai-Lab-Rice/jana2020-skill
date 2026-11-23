"""Plot Jana M83 diagnostics using observations from SNS TOF nuclear exports."""
import argparse
import math
from statistics import median

from observation_mapping import add_hkl_arguments, join, mantid_records


def analyze_wavelength_dependence(hkl_path, m83_path, out_png=None, observations=None, *, hkl_layout):
    records = []
    with open(m83_path) as f:
        for number, line in enumerate(f, 1):
            fields = line.split()
            if len(fields) < 3:
                continue
            try:
                hkl = tuple(map(int, fields[:3]))
            except ValueError:
                continue  # Listing headers do not start with three integer indices.
            try:
                if len(fields) < 13:
                    raise ValueError("missing amplitude fields or sequence tag")
                tag = int(fields[-1])
                fo, fc, sig = map(float, fields[9:12])
                if not all(math.isfinite(value) for value in (fo, fc, sig)):
                    raise ValueError("nonfinite M83 amplitude")
            except ValueError as exc:
                raise ValueError(f"{m83_path}:{number}: unsupported M83 row: {exc}") from exc
            records.append(dict(hkl=hkl, sequence=tag, Fo=fo, Fc=fc, sigma_Fo=sig))
    if not records:
        raise ValueError("No supported M83 records")
    matched = join(
        records, mantid_records(hkl_path, hkl_layout), observations, allow_listing_subset=True,
    )
    usable = []
    for row in matched:
        if row["Fc"] <= 0:
            continue
        ratio = row["Fo"] / row["Fc"]
        usable.append(dict(row, amplitude_ratio=ratio, intensity_ratio=ratio * ratio))
    if not usable:
        raise ValueError("No positive calculated amplitudes")
    print(f"Matched {len(matched)}; {len(usable)} positive Fc; no significance cut.")
    print("Intensity ratio=(Fo/Fc)^2; amplitude ratio=Fo/Fc. Parity has no universal chemical meaning.")
    for parity in (0, 1):
        group = [row for row in usable if row["hkl"][2] % 2 == parity]
        if group:
            print("l parity", parity, "N", len(group),
                  "median intensity ratio", median(row["intensity_ratio"] for row in group))
    if out_png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        for parity in (0, 1):
            group = [row for row in usable if row["hkl"][2] % 2 == parity]
            if group:
                ax.scatter([row["lam"] for row in group], [row["intensity_ratio"] for row in group],
                           s=8, label=f"l parity {parity}")
        ax.axhline(1, color="gray")
        ax.set(xlabel="Wavelength (Å)", ylabel="(Fo/Fc)²")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_png)
        plt.close(fig)
    return usable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_hkl_arguments(parser)
    parser.add_argument("--m83", required=True)
    parser.add_argument("--out-png")
    args = parser.parse_args()
    analyze_wavelength_dependence(
        args.hkl, args.m83, args.out_png, args.observations, hkl_layout=args.hkl_layout,
    )


if __name__ == "__main__":
    main()
