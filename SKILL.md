---
name: jana2020-skill
description: >-
  Comprehensive guide, file-format specification, and toolkit for pair-programming
  single-crystal X-ray and time-of-flight (TOF) neutron diffraction refinements
  in Jana2020 (and Jana2006). Activate this skill whenever the user works with
  Jana2020/Jana2006, imports .hkl reflection data (such as TOPAZ/Corelli),
  modifies or parses .m40, .m50, .m81, .m83, .m90, .m95, or .ref files, sets up
  site occupancy constraints, extinction models, or Difference Fourier maps.
---

# Jana2020 Pair-Programming & Refinement Skill

`Jana2020.exe` is an interactive GUI Fortran program without headless command-line batch flags for running `REFINE` or `FOURIER`. To work efficiently and accurately with a user in Jana2020, follow a strict **two-phase division of labor**:

1. **Phase 1: Importing Reflection Data (User-Guided GUI)**
   - Creating the binary/text reflection repository (`.m95` and `.m90`) from raw diffractometer `.hkl` files requires the Jana2020 Import Wizard.
   - Guide the user step-by-step using the **exact, verified dialog labels** in [references/import_wizard_guide.md](./references/import_wizard_guide.md). Never guess menu names or tell the user to import a CIF containing parenthesized standard uncertainties.
2. **Phase 2: Structure Setup, Refinement & Analysis (Agent File Engineering)**
   - Once `.m95` and `.m90` exist on disk, **do not make the user click through GUI menus** to enter space group operators, atomic coordinates, ADP tensors, refinement flags, or constraint equations.
   - Directly write or edit the `.m50`, `.m40`, and `.m90` files on disk following [references/file_formats_m40_m50_m90.md](./references/file_formats_m40_m50_m90.md).
   - Instruct the user to reload (`File -> Open`) and click **`Refinement -> Run refinement`**, wait for the user to reply `"Done"`, and immediately parse the output `.ref` and `.m40` files using [scripts/parse_jana_ref.py](./scripts/parse_jana_ref.py).

---

## Mandatory Golden Rules

### 1. Beware of Jana2020's In-Memory GUI State Caching
When a project is already open in the Jana2020 GUI, editing `.m50` or `.m40` on disk **does not** automatically update Jana2020's in-memory state (especially `equation` constraints and `iext` extinction settings). If the user clicks `Refinement -> Run refinement` without reloading, Jana2020 will use its cached in-memory equations and overwrite your disk changes!
- **Always instruct the user**:
  - Re-open the project via **`File -> Open`** (selecting `<project>.m50`), **OR**
  - Clear stale equations in the GUI via **`Refinement -> Refinement Commands -> Equations -> Delete all -> OK`**.

### 2. Never Trigger the `READCIF` Fortran Crash
Jana2020's Fortran CIF parser (`ReadCIF.f90`) crashes with `forrtl: severe (59): list-directed I/O syntax error` when reading CIF files that contain standard uncertainties in parentheses (e.g. `4.1532(3)`).
- **Best Practice**: Skip CIF import completely. After the Import Wizard writes `.m95` and `.m90` and opens the `"Run Superflip"` dialog, have the user click **`"Quit"`**, and directly write the complete `.m50` and `.m40` files to disk.

### 3. Always Use Crystallographic Occupancy ($a_i$) in `.m40` and `.m50` Equations
In Jana2020, the occupancy value stored in `.m40` (and referenced by `occ[Atom]` in `.m50` equations) is **not** $1.0$ for a fully occupied special position. It is weighted by the Wyckoff site multiplicity $M_{\text{site}}$ divided by the number of space-group symmetry operations $N_{\text{sym}}$:
$$a_i = f_{\text{site}} \times \frac{M_{\text{site}}}{N_{\text{sym}}}$$
- Example in $P6_3/mmc$ ($N_{\text{sym}} = 24$):
  - For a $2a, 2b, 2c, 2d$ site ($M_{\text{site}} = 2$), full occupancy ($f_{\text{site}} = 1.0$) is $a_i = \frac{2}{24} = \mathbf{0.083333}$ (multiplier $= 12$).
  - A substitutional sum constraint $f_{\text{Mn1}} + f_{\text{Li1}} = 1.0$ on $2a$ **must** be written in `.m50` as:
    ```text
    equation : occ[Li1]=0.083333-occ[Mn1]
    ```
    Writing `1.0-occ[Mn1]` will force the site to $1200\%$ occupancy!

### 4. Account for the `.m40` `s.u. block` Column Offset When Parsing
In `.m40`, the main atom line has **7 tokens**:
`Name  TypeIdx  ADPMode  occ  x  y  z` (`parts[3]` is `occ`).
In the `s.u. block` at the bottom of `.m40`, `TypeIdx` and `ADPMode` are omitted, leaving **5 tokens**:
`Name  su_occ  su_x  su_y  su_z` (`parts[1]` is `su_occ`, `parts[4]` is `su_z`).

### 5. Watch Out for Least-Squares Matrix Singularities
Always inspect the bottom of `.ref` for:
- `List of parameters blocked due to singularity`
- `Correlations larger than 0.900`
Refining the overall scale factor alongside all sublattice occupancies, or refining two co-located atoms on the same Wyckoff site without a sum equation, produces a singular normal matrix ($r = -1.000$). Read [references/crystallographic_pitfalls.md](./references/crystallographic_pitfalls.md) before designing substitutional or defect trials.

---

## Reference Documentation (Progressive Disclosure)

Read the specific reference file below corresponding to your current task:

1. **[references/import_wizard_guide.md](./references/import_wizard_guide.md)**
   - Read this when guiding a user through importing `.hkl` data (e.g., TOPAZ/Corelli TOF neutron data), setting up a new project, or navigating Jana2020's actual GUI menus and dialogs.
2. **[references/file_formats_m40_m50_m90.md](./references/file_formats_m40_m50_m90.md)**
   - Read this when constructing or editing `.m50`, `.m40`, or `.m90` files, setting 10-digit refinement flags, configuring Becker-Coppens extinction, or reading `.m83` and binary `.m81` Difference Fourier maps.
3. **[references/crystallographic_pitfalls.md](./references/crystallographic_pitfalls.md)**
   - Read this when troubleshooting refinement singularities, circular occupancy traps, $-1.000$ correlations on shared sites, or negative neutron scattering lengths ($b_c < 0$).

---

## Bundled Scripts & Examples

Use these ready-to-run utilities in `scripts/` and templates in `examples/`:

- **[scripts/parse_jana_ref.py](./scripts/parse_jana_ref.py)**: Parses `.ref` and `.m40` across one or more trial directories; outputs Markdown summary tables of $R(\text{obs})$, $wR_2(\text{obs})$, $\text{GOF}$, $G_{\text{iso}}$, chemical occupancies with s.u., ADPs, singularities, and high correlations.
- **[scripts/edit_jana_files.py](./scripts/edit_jana_files.py)**: Programmatically updates `.m40` atom flags/occupancies and `.m50` `refine` blocks (`iext`, `equation` lines).
- **[scripts/filter_m90_wavelength.py](./scripts/filter_m90_wavelength.py)**: Filters `.m90` reflections by TOF wavelength $\lambda$ or $d$-spacing and re-indexes `nref` and the `idx * 1000 + 1` sequence column.
- **[scripts/analyze_fourier_m81.py](./scripts/analyze_fourier_m81.py)**: Unpacks binary `.m81` 3D Difference Fourier maps, interpolates $\Delta\rho(x,y,z)$ in $\text{fm/\AA}^3$ and $\sigma$ units at specific Wyckoff holes, and exports 2D contour sections as PNGs.
- **[scripts/plot_extinction_wavelength.py](./scripts/plot_extinction_wavelength.py)**: Joins `.m83` and `.hkl` to plot normalized intensity ratios ($I_{\text{obs}}/I_{\text{calc}}$) vs. wavelength $\lambda$ and $d$-spacing as PNGs.
- **[examples/sample_MnTe_340K.m50](./examples/sample_MnTe_340K.m50)** & **[examples/sample_MnTe_340K.m40](./examples/sample_MnTe_340K.m40)**: Clean reference templates for hexagonal $P6_3/mmc$ TOF neutron refinements.
