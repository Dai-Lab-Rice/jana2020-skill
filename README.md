# `jana2020-skill` — Agent Skill for Jana2020 Single-Crystal Refinement

A modular, version-controlled AI Agent Skill for pair-programming crystallographic refinements in **Jana2020** (and **Jana2006**), covering both single-crystal X-ray diffraction and time-of-flight (TOF) neutron diffraction (e.g., ORNL SNS TOPAZ / Corelli).

Because `Jana2020.exe` is an interactive GUI Fortran application without headless command-line batch execution, this skill establishes a streamlined **Native GUI automation + Agent File Engineering** workflow:

1. **Phase 1 — Importing Reflection Data (Native GUI Controls)**:
   - Uses native control automation, with user-guided fallback when needed, through the *actual, verified* Jana2020 Import Wizard dialogs and buttons to generate `.m95` and `.m90` reflection files without triggering `READCIF` Fortran crashes.
2. **Phase 2 — Structure Setup, Refinement & Diagnostics (Agent File Engineering)**:
   - Directly constructs and modifies `.m50` (symmetry, scattering tables, extinction, constraint equations), `.m40` (atomic coordinates, site multiplicities, 10-digit refinement flags), and `.m90` (wavelength/$d$-spacing cutoffs) on disk.
   - Reloads edited projects to avoid Jana2020's in-memory state caching so disk edits are cleanly loaded.
   - Provides automated Python utilities to parse `.ref` and `.m40` outputs, inspect 3D Difference Fourier binary maps (`.m81`), and diagnose secondary extinction across wavelength (`.m83` + `.hkl`).

---

## Repository Structure

```text
jana2020-skill/
├── SKILL.md                                  # Main agent skill entrypoint (YAML frontmatter + core workflow)
├── README.md                                 # Repository overview and quick start
├── references/
│   ├── import_wizard_guide.md                # Verified step-by-step Import Wizard & GUI menu reference
│   ├── file_formats_m40_m50_m90.md           # Technical specification of .m50, .m40, .m90, .m83, .m81
│   └── crystallographic_pitfalls.md          # GUI caching traps, matrix singularities & neutron contrast math
├── scripts/
│   ├── parse_jana_ref.py                     # Automated .ref & .m40 parser (R-factors, ADPs, occupancies, s.u.)
│   ├── edit_jana_files.py                    # Programmatic .m40 / .m50 modifier and flag builder
│   ├── filter_m90_wavelength.py              # Wavelength (lambda) and d-spacing cutoff tool for TOF .m90 files
│   ├── analyze_fourier_m81.py                # Binary .m81 3D Difference Fourier reader, interpolator & PNG plotter
│   └── plot_extinction_wavelength.py         # Fobs/Fcalc vs wavelength diagnostic plotter from .m83 & .hkl
└── examples/
    ├── sample_MnTe_340K.m50                  # Annotated reference .m50 file (P63/mmc, neutron formtab -62)
    └── sample_MnTe_340K.m40                  # Annotated reference .m40 file (flags, equations & s.u. block)
```

---

## Quick Usage of Bundled Scripts

All scripts are designed for Python 3 (`numpy`, `matplotlib`):

```powershell
# 1. Parse a single refinement directory or compare an entire tree of trials
C:\Users\hplfz\miniconda3\python.exe scripts/parse_jana_ref.py path/to/refinement_dir --mult 12

# 2. Modify atom flags, occupancies, or equations in .m40 / .m50
C:\Users\hplfz\miniconda3\python.exe scripts/edit_jana_files.py path/to/project.m40 --set-flag Te1=1000101000

# 3. Filter a TOF .m90 file by maximum wavelength (e.g. lambda <= 1.8 A)
C:\Users\hplfz\miniconda3\python.exe scripts/filter_m90_wavelength.py --hkl data.hkl --m90-in orig.m90 --m90-out active.m90 --max-lambda 1.8

# 4. Analyze a 3D Difference Fourier map (.m81) and plot 2D contour slices (PNG)
C:\Users\hplfz\miniconda3\python.exe scripts/analyze_fourier_m81.py path/to/project.m81 --nx 42 --ny 42 --nz 67 --out-png fourier_slices.png

# 5. Plot normalized intensity ratios (Iobs/Icalc) vs wavelength (PNG)
C:\Users\hplfz\miniconda3\python.exe scripts/plot_extinction_wavelength.py --hkl data.hkl --m83 project.m83 --out-png wavelength_dependence.png
```

## Validated helper boundaries

See `SKILL.md` and the format reference for supported layouts. Chemical site fractions require an explicit occupancy multiplier. Repeated hkl requires a verified sequence-keyed observation map. Legacy editing/filtering refuses unsupported multi-phase or multi-block input before writing. Joint datasets and measurement diagnostics have dedicated references.
