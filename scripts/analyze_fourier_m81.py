#!/usr/bin/env python
"""
analyze_fourier_m81.py - Binary .m81 3D Difference Fourier Map Reader & Plotter.

Reads Jana2020's binary .m81 3D density grid, reports map statistics (max, min,
RMS noise sigma), performs trilinear interpolation at candidate Wyckoff sites,
and optionally generates a 2D contour PNG slice.

Usage:
  C:\\Users\\hplfz\\miniconda3\\python.exe analyze_fourier_m81.py path/to/Project.m81 \\
      --nx 42 --ny 42 --nz 67 --out-png fourier_slices.png
"""

import argparse
import os
import struct
import sys
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_m81_grid(m81_path, nx=42, ny=42, nz=67):
    with open(m81_path, 'rb') as f:
        data = f.read()

    plane_size = nx * ny * 4
    expected_bytes = (nz + 1) * plane_size
    if len(data) < expected_bytes:
        raise ValueError(
            f"File size {len(data)} bytes is smaller than expected {(nz + 1) * plane_size} bytes "
            f"for grid ({nx}, {ny}, {nz}). Check grid dimensions in .fou."
        )

    grid = np.zeros((nx, ny, nz), dtype=np.float32)
    for z in range(nz):
        start = (z + 1) * plane_size
        end = start + plane_size
        floats = struct.unpack(f'<{nx * ny}f', data[start:end])
        grid[:, :, z] = np.array(floats).reshape((nx, ny), order='F')

    return grid


def trilinear_interp(grid, x, y, z):
    nx, ny, nz = grid.shape
    x = x % 1.0
    y = y % 1.0
    z = z % 1.0

    ix = int(np.floor(x * nx))
    iy = int(np.floor(y * ny))
    iz = int(np.floor(z * nz))

    fx = (x * nx) - ix
    fy = (y * ny) - iy
    fz = (z * nz) - iz

    ix1 = (ix + 1) % nx
    iy1 = (iy + 1) % ny
    iz1 = (iz + 1) % nz

    val = (
        grid[ix, iy, iz] * (1 - fx) * (1 - fy) * (1 - fz)
        + grid[ix1, iy, iz] * fx * (1 - fy) * (1 - fz)
        + grid[ix, iy1, iz] * (1 - fx) * fy * (1 - fz)
        + grid[ix1, iy1, iz] * fx * fy * (1 - fz)
        + grid[ix, iy, iz1] * (1 - fx) * (1 - fy) * fz
        + grid[ix1, iy, iz1] * fx * (1 - fy) * fz
        + grid[ix, iy1, iz1] * (1 - fx) * fy * fz
        + grid[ix1, iy1, iz1] * fx * fy * fz
    )
    return float(val)


def plot_fourier_slice_png(grid, z_frac, out_png):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    nx, ny, nz = grid.shape
    slice_2d = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            slice_2d[i, j] = trilinear_interp(grid, i / nx, j / ny, z_frac)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=200)
    x_vals = np.linspace(0, 1, nx)
    y_vals = np.linspace(0, 1, ny)
    X, Y = np.meshgrid(x_vals, y_vals, indexing='ij')

    vmax = max(abs(grid.max()), abs(grid.min()))
    cs = ax.contourf(X, Y, slice_2d, levels=25, cmap='RdBu_r', vmin=-vmax, vmax=vmax)
    fig.colorbar(cs, ax=ax, label=r'$\Delta\rho\ (\mathrm{fm/\AA^3})$')
    ax.set_xlabel('Fractional $x$')
    ax.set_ylabel('Fractional $y$')
    ax.set_title(f'Difference Fourier Section at $z = {z_frac:.2f}$')
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    print(f"Saved 2D Difference Fourier contour plot to {out_png}")


def main():
    parser = argparse.ArgumentParser(description="Analyze a Jana2020 binary .m81 Difference Fourier map.")
    parser.add_argument("m81", help="Path to .m81 file.")
    parser.add_argument("--nx", type=int, default=42, help="Grid points along a (default: 42).")
    parser.add_argument("--ny", type=int, default=42, help="Grid points along b (default: 42).")
    parser.add_argument("--nz", type=int, default=67, help="Grid points along c (default: 67).")
    parser.add_argument("--site", action="append", default=[], help="Custom site Label=x,y,z to interpolate.")
    parser.add_argument("--z-slice", type=float, default=0.75, help="Fractional z for 2D PNG slice (default: 0.75).")
    parser.add_argument("--out-png", default=None, help="Output PNG path for 2D slice contour plot.")
    args = parser.parse_args()

    grid = load_m81_grid(args.m81, nx=args.nx, ny=args.ny, nz=args.nz)
    rms = float(np.sqrt(np.mean(grid ** 2)))

    print("=" * 68)
    print(f"DIFFERENCE FOURIER ANALYSIS: {args.m81}")
    print("=" * 68)
    print(f"  Grid dimensions          : ({args.nx}, {args.ny}, {args.nz})")
    print(f"  Maximum positive peak    : {grid.max():+8.4f} fm/A^3 ({grid.max()/rms:+5.1f} sigma)")
    print(f"  Minimum negative well    : {grid.min():+8.4f} fm/A^3 ({grid.min()/rms:+5.1f} sigma)")
    print(f"  RMS background noise     : {rms:8.4f} fm/A^3")
    print("-" * 68)

    default_sites = [
        ("Mn1 (2a)", 0.0, 0.0, 0.0),
        ("Te1 (2c)", 1 / 3, 2 / 3, 0.25),
        ("Interstitial 2d", 1 / 3, 2 / 3, 0.75),
        ("Interstitial 4f", 1 / 3, 2 / 3, 0.893),
        ("Octahedral 2b", 0.0, 0.0, 0.25),
    ]
    for item in args.site:
        label, coords = item.split("=", 1)
        sx, sy, sz = (float(c) for c in coords.split(","))
        default_sites.append((label, sx, sy, sz))

    for name, sx, sy, sz in default_sites:
        val = trilinear_interp(grid, sx, sy, sz)
        sig = val / rms if rms > 0 else 0.0
        print(f"  {name:<20} ({sx:6.3f}, {sy:6.3f}, {sz:6.3f}) : {val:+8.4f} fm/A^3  ({sig:+5.1f} sigma)")
    print("=" * 68)

    if args.out_png:
        plot_fourier_slice_png(grid, args.z_slice, args.out_png)


if __name__ == "__main__":
    main()
