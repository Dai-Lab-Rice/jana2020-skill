#!/usr/bin/env python
"""
plot_extinction_wavelength.py - Wavelength & d-spacing residual diagnostic for Jana2020.

Joins a Jana2020 .m83 file (observed vs. calculated structure factors) with a
22-column Mantid TOF .hkl file to analyze normalized intensity ratios across
wavelength lambda and d-spacing, separating reflections by parity (e.g., l=odd
vs. l=even in hexagonal P63/mmc). Optionally outputs a diagnostic PNG plot.

Usage:
  C:\\Users\\hplfz\\miniconda3\\python.exe plot_extinction_wavelength.py \\
      --hkl path/to/data.hkl --m83 path/to/Project.m83 --out-png wavelength_dep.png
"""

import argparse
import os
import sys
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def analyze_wavelength_dependence(hkl_path, m83_path, out_png=None):
    hkl_data = []
    with open(hkl_path, 'r', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 20:
                try:
                    h, k, l = int(parts[0]), int(parts[1]), int(parts[2])
                    if h == 0 and k == 0 and l == 0:
                        continue
                    i_obs = float(parts[3])
                    sig_i = float(parts[4])
                    tbar = float(parts[16])
                    lam = float(parts[18])
                    d_sp = float(parts[19])
                    hkl_data.append({
                        'h': h, 'k': k, 'l': l,
                        'I': i_obs, 'sigI': sig_i,
                        'lam': lam, 'd': d_sp, 'tbar': tbar
                    })
                except ValueError:
                    pass

    m83_dict = {}
    with open(m83_path, 'r', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 12:
                try:
                    h, k, l = int(parts[0]), int(parts[1]), int(parts[2])
                    fobs = float(parts[9])
                    fcalc = float(parts[10])
                    sig = float(parts[11])
                    m83_dict[(h, k, l)] = (fobs, fcalc, sig)
                except ValueError:
                    pass

    matched = []
    for r in hkl_data:
        key = (r['h'], r['k'], r['l'])
        if key in m83_dict:
            fobs, fcalc, sig = m83_dict[key]
            if fobs > 3 * sig and fcalc > 1.0:
                matched.append({**r, 'fobs': fobs, 'fcalc': fcalc, 'ratio': fobs / fcalc})

    l_odd = [r for r in matched if r['l'] % 2 != 0]
    l_even = [r for r in matched if r['l'] % 2 == 0]

    bins = np.linspace(0.5, 2.5, 9)
    print("=" * 84)
    print("WAVELENGTH DEPENDENCE OF NORMALIZED INTENSITY (Fobs^2 / Fcalc^2)")
    print("=" * 84)
    hdr = f"{'Wavelength [A]':<16} | {'l=odd (N)':<11} | {'l=odd Mean':<12} | {'l=even (N)':<11} | {'l=even Mean':<12} | {'Diff (%)':<10}"
    print(hdr)
    print("-" * len(hdr))

    bin_centers = []
    odd_means = []
    even_means = []

    for i in range(len(bins) - 1):
        l_min, l_max = bins[i], bins[i + 1]
        odd_b = [r['ratio'] for r in l_odd if l_min <= r['lam'] < l_max]
        even_b = [r['ratio'] for r in l_even if l_min <= r['lam'] < l_max]
        m_odd = float(np.mean(odd_b)) if odd_b else np.nan
        m_even = float(np.mean(even_b)) if even_b else np.nan
        diff_pct = (m_even - m_odd) * 100.0 if (odd_b and even_b) else 0.0
        print(
            f"{l_min:4.2f} - {l_max:4.2f} A   | {len(odd_b):9d}   | "
            f"{m_odd if not np.isnan(m_odd) else 0.0:10.4f}   | {len(even_b):9d}   | "
            f"{m_even if not np.isnan(m_even) else 0.0:10.4f}   | {diff_pct:+8.2f}%"
        )
        bin_centers.append(0.5 * (l_min + l_max))
        odd_means.append(m_odd)
        even_means.append(m_even)

    print("=" * 84)

    if out_png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 4.5), dpi=200)
        ax.plot(bin_centers, odd_means, 'o-', label=r'$l = \mathrm{odd}$ (Pure Anion)', linewidth=2)
        ax.plot(bin_centers, even_means, 's-', label=r'$l = \mathrm{even}$ (Mixed)', linewidth=2)
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)
        ax.set_xlabel(r'Neutron Wavelength $\lambda$ (\AA)')
        ax.set_ylabel(r'Mean $I_{\mathrm{obs}} / I_{\mathrm{calc}}$')
        ax.set_title('Wavelength Dependence of Normalized Bragg Intensities')
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_png, dpi=200)
        plt.close(fig)
        print(f"Saved wavelength diagnostic plot to {out_png}")


def main():
    parser = argparse.ArgumentParser(description="Analyze and plot Fobs/Fcalc vs wavelength from .m83 and .hkl.")
    parser.add_argument("--hkl", required=True, help="Path to 22-column Mantid .hkl file.")
    parser.add_argument("--m83", required=True, help="Path to Jana2020 .m83 file.")
    parser.add_argument("--out-png", default=None, help="Optional output PNG path.")
    args = parser.parse_args()

    analyze_wavelength_dependence(args.hkl, args.m83, out_png=args.out_png)


if __name__ == "__main__":
    main()
