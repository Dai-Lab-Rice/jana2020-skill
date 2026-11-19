# Jana2020 File Formats & Programmatic Modification Specification

This reference documents the exact layout and syntax of Jana2020's core project files:
- **`.m50`**: Crystal symmetry, unit cell, scattering tables, and `refine`/`fourier` directives.
- **`.m40`**: Scale factor, extinction parameter, atomic positions/occupancies/ADPs, 10-digit refinement flags, and standard uncertainties (`s.u. block`).
- **`.m90`** & **`.m95`**: Refinement reflection file and master reflection repository.
- **`.m83`**: Plaintext observed vs. calculated structure factors ($F_{\text{obs}}, F_{\text{calc}}, \sigma$).
- **`.m81`**: Binary 3D Fourier nuclear/electron density map ($\Delta\rho(\mathbf{r})$).

---

## 1. The `.m50` File (Structure & Directives)

### Annotated `.m50` Example ($P6_3/mmc$ TOF Neutron Refinement)
```text
Version Jana2020
title LiMnTe_340K
cell 4.1532 4.1532 6.719 90 90 120
esdcell 0.0003 0.0003 0.0008 0 0 0
spgroup P63/mmc 194 6
lattice P
symmetry x y z
symmetry -y x-y z
symmetry -x+y -x z
symmetry -x -y z+1/2
symmetry y -x+y z+1/2
symmetry x-y x z+1/2
symmetry y x -z
symmetry x-y -y -z
symmetry -x -x+y -z
symmetry -y -x -z+1/2
symmetry -x+y y -z+1/2
symmetry x x-y -z+1/2
symmetry -x -y -z
symmetry y -x+y -z
symmetry x-y x -z
symmetry x y -z+1/2
symmetry -y x-y -z+1/2
symmetry -x+y -x -z+1/2
symmetry -y -x z
symmetry -x+y y z
symmetry x x-y z
symmetry y x z+1/2
symmetry x-y -y z+1/2
symmetry -x -x+y z+1/2
unitsnumb 2
atlist Mn Te Li
formtab -62
atom Mn atradius 1.37 color 168008158 donor 0 acceptor 0
atom Te atradius 1.37 color 173162081 donor 0 acceptor 0
atom Li atradius 1.57 color 134224116 donor 0 acceptor 0
roundmethod 1 autrefkeys 1
end
*******************************************************************************
refine
  cycles 100 damp 0.2
  iext 1 itypex 1 idistr 1 radius 0.01
  equation : occ[Li1]=0.083333-occ[Mn1]
  equation : u11[Li1]=u11[Mn1]
  equation : u33[Li1]=u11[Mn1]
end refine
fourier
end fourier
dist
end dist
contour
end contour
```

### Key `.m50` Directives
- **`formtab -62`**: Selects **Neutron coherent scattering lengths** ($b_c$). If omitted, Jana defaults to X-ray atomic form factors ($f(s)$)!
- **`atlist <El1> <El2> ...`**: Defines the 1-based integer chemical type index (`TypeIdx`) used in `.m40` (`1` = `El1`, `2` = `El2`, `3` = `El3`, etc.).
- **`unitsnumb <Z>`**: Formula units per unit cell ($Z$).
- **`iext` (Extinction directive inside `refine ... end refine`)**:
  - `iext 0`: Extinction turned OFF. (Also set the actual extinction refinement flag in `.m40` to `000000`).
  - `iext 1 itypex 1 idistr 1 radius 0.01`: **Isotropic Becker-Coppens** (`iext 1`), Type 1 mosaic-spread dominated (`itypex 1`; use `2` for Type 2 particle-size dominated), Gaussian mosaic distribution (`idistr 1`; use `2` for Lorentzian), crystal radius in cm (`radius 0.01`).
  - `iext 2 itypex 1 idistr 1 radius 0.01`: **Anisotropic Becker-Coppens** (`iext 2`).
- **`equation : <lhs>=<rhs>`**:
  - Constrains dependent parameters during least-squares refinement.
  - Common parameter names: `occ[AtomName]`, `x[AtomName]`, `y[AtomName]`, `z[AtomName]`, `u11[AtomName]`, `u22[AtomName]`, `u33[AtomName]`, `u12[AtomName]`, `u13[AtomName]`, `u23[AtomName]`, `uiso[AtomName]`.
  - **CRITICAL EQUATION SCALING RULE**: `occ[AtomName]` in an equation refers to the raw crystallographic occupancy $a_i = f_{\text{site}} \times \frac{M_{\text{site}}}{N_{\text{sym}}}$ stored in `.m40`, **NOT** a universal chemical fraction!
    - On a 2-fold site ($M_{\text{site}} = 2$) in $P6_3/mmc$ ($N_{\text{sym}} = 24$), full site occupancy is $2/24 = 0.083333$.
    - Therefore, $\text{occ}(\text{Mn1}) + \text{occ}(\text{Li1}) = 1$ **must** be written as:
      `equation : occ[Li1]=0.083333-occ[Mn1]`

---

## 2. The `.m40` File (Parameters, Flags & `s.u. block`)

### Layout checks before editing

The example below is a single-scale layout, not a universal line-number specification. Preserve any imported `commands`, `maxsc N`, `end` preamble and all detector-scale rows and their matching s.u. rows. A CORELLI import with `maxsc 60` used ten rows of six scale values. Determine the actual layout before indexing extinction or atom records.

Atom records use a fixed ten-character name field immediately followed by the type index, for example `f"{name:<10}{type_idx}..."`. Tokenization helps analysis but is insufficient to validate output column placement. An extra space before the type index caused Jana to read type zero. Validate generated files by reopening them in Jana before refinement.

### Annotated `.m40` Example
```text
    3    0    0    1    0
 2.848967 0.000000 0.000000 0.000000 0.000000 0.000000      100000
 0.000000 0.000000 0.000000                                 000
 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000      000000
 0.001250 0.000000 0.000000 0.000000 0.000000 0.000000      100000
Mn1       1  2     0.083333 0.000000 0.000000 0.000000
 0.018750 0.018750 0.015500 0.009375 0.000000 0.000000      0000101000
Te1       2  2     0.079923 0.333333 0.666667 0.250000
 0.009120 0.009120 0.011842 0.004560 0.000000 0.000000      1000101000
Li1       3  1     0.002500 0.333333 0.666667 0.892784
 0.037323 0.000000 0.000000 0.000000 0.000000 0.000000      1001100000
--------------------------   s.u. block   --------------------------------------
 0.014714 0.000000 0.000000 0.000000 0.000000 0.000000
 0.000000 0.000000 0.000000
 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
 0.000047 0.000000 0.000000 0.000000 0.000000 0.000000
Mn1                0.000000 0.000000 0.000000 0.000000
 0.000217 0.000217 0.000281 0.000109 0.000000 0.000000
Te1                0.000290 0.000000 0.000000 0.000000
 0.000108 0.000108 0.000153 0.000054 0.000000 0.000000
Li1                0.001100 0.000000 0.000000 0.015910
 0.026600 0.000000 0.000000 0.000000 0.000000 0.000000
```

### Line-by-Line Anatomy of `.m40`
1. **Line 1 (Header Counts)**: `    3    0    0    1    0`
   - First integer (`3`) is the **total number of atoms** in the `.m40` file. **Whenever you add or remove an atom block, you MUST update this integer!**
2. **Line 2 (Scale Factors)**: ` 2.848967 0.000000 ... 100000`
   - Token 0 is `scale1`. Token 6 (`100000`) refines `scale1` and fixes `scale2..scale6`.
3. **Line 3 (Overall Temperature Factor / Twins)**: ` 0.000000 0.000000 0.000000 000`
4. **Line 4**: Reserved header line (`000000`).
5. **Line 5 (Extinction Parameters)**: ` 0.001250 0.000000 ... 100000`
   - For isotropic extinction (`iext 1`), Token 0 is $G_{\text{iso}}$ and flag is `100000`.
   - For anisotropic extinction (`iext 2`), Tokens 0..5 are $G_{11}, G_{22}, G_{33}, G_{12}, G_{13}, G_{23}$ (e.g. flag `101000` in hexagonal symmetry).
   - For no extinction (`iext 0`), set flag to `000000`.

### Atom Blocks (2 Lines per Atom)
- **Line A (Coordinates & Occupancy)**:
  `<AtomName> <TypeIdx> <ADPMode> <ai> <x> <y> <z>`
  - `AtomName`: Up to 10 characters (e.g. `Mn1`, `Te1`, `Li1`).
  - `TypeIdx`: 1-based index into `atlist` in `.m50` (`1`, `2`, `3`, ...).
  - `ADPMode`:
    - `1` = Isotropic thermal parameter ($U_{\text{iso}}$).
    - `2` = Anisotropic harmonic thermal tensor ($U_{11}, U_{22}, U_{33}, U_{12}, U_{13}, U_{23}$).
  - `ai`: Crystallographic occupancy parameter.
    - **Site Occupancy Fraction ($f_{\text{site}} \in [0, 1]$)**:
      $$a_i = f_{\text{site}} \times \frac{M_{\text{site}}}{N_{\text{sym}}}$$
    - **Formula-Unit Stoichiometry ($c_{\text{f.u.}}$ atoms per formula unit, with $Z$ formula units per cell)**:
      $$a_i = c_{\text{f.u.}} \times \frac{Z}{N_{\text{sym}}}$$
      *Note*: Notice that if you want a fixed stoichiometry per formula unit (e.g., $c_{\text{f.u.}} = 0.03$ Li per $\text{MnTe}$ formula unit in $P6_3/mmc$ where $Z=2, N_{\text{sym}}=24$), $a_i = 0.03 \times \frac{2}{24} = 0.002500$ regardless of whether Li is placed on a 2-fold site ($2a, 2c, 2d$, where $f_{\text{site}} = 3\%$) or a 4-fold split site ($4f$, where $f_{\text{site}} = 1.5\%$ across twice as many sites)! Conversely, when reporting the *site occupancy fraction* $f_{\text{site}}$ from $a_i$, multiply $a_i$ by $\frac{N_{\text{sym}}}{M_{\text{site}}}$ ($12$ for $2a/2c/2d$; $6$ for $4f$), whereas when reporting *stoichiometry per formula unit* $c_{\text{f.u.}}$, multiply $a_i$ by $\frac{N_{\text{sym}}}{Z}$ ($12$ for $Z=2$).
- **Line B (ADPs & 10-Digit Refinement Flag)**:
  `<U11/Uiso> <U22> <U33> <U12> <U13> <U23>      <10-digit flag>`

| Digit Position (1-based) | Parameter Controlled | Notes |
| :---: | :--- | :--- |
| **1** | `occ` ($a_i$) | `1` = refine occupancy, `0` = fixed (or controlled by equation) |
| **2** | `x` | `1` = refine $x$, `0` = fixed by symmetry |
| **3** | `y` | `1` = refine $y$, `0` = fixed by symmetry |
| **4** | `z` | `1` = refine $z$, `0` = fixed by symmetry |
| **5** | `U11` (or `Uiso` if `ADPMode=1`) | `1` = refine $U_{11}$ (or $U_{\text{iso}}$), `0` = fixed |
| **6** | `U22` | `0` when constrained to $U_{11}$ by trigonal/hexagonal/tetragonal/cubic symmetry |
| **7** | `U33` | `1` = refine $U_{33}$, `0` = fixed (always `0` if `ADPMode=1`) |
| **8** | `U12` | `0` when constrained to $\frac{1}{2}U_{11}$ by hexagonal symmetry |
| **9** | `U13` | `0` when fixed to $0$ by special position symmetry |
| **10** | `U23` | `0` when fixed to $0$ by special position symmetry |

### Common 10-Digit Flag Patterns
- `0000101000`: Fixed occupancy, fixed special position $(x,y,z)$, refine anisotropic $U_{11}$ and $U_{33}$ (hexagonal $2a, 2c, 2d$).
- `1000101000`: Free occupancy, fixed position $(x,y,z)$, refine anisotropic $U_{11}$ and $U_{33}$.
- `0001100000`: Fixed occupancy, fixed $(x,y)$, free $z$ coordinate (e.g. $4f$), refine isotropic $U_{\text{iso}}$ (`ADPMode=1`).
- `1001100000`: Free occupancy, fixed $(x,y)$, free $z$ coordinate, refine isotropic $U_{\text{iso}}$ (`ADPMode=1`).
- `0000000000`: All parameters fixed or slaved to another atom via `equation` lines in `.m50`.

### Parsing the `s.u. block` (Column Offset Warning!)
Below `--------------------------   s.u. block   --------------------------------------`:
- Lines 1â€“4 give the s.u.'s of the global parameters (Line 1 Token 0 = $\sigma(\text{scale1})$; Line 4 Token 0 = $\sigma(G_{\text{iso}})$).
- For each atom, Line A has **5 whitespace-separated tokens** (unlike the 7 tokens in the main block because `TypeIdx` and `ADPMode` are integers without uncertainties):
  ```text
  Te1                0.000290 0.000000 0.000000 0.000000
  ```
  - `parts[0]` = Atom name (`Te1`)
  - `parts[1]` = $\sigma(a_i)$ (crystallographic occupancy s.u.)
  - `parts[2]` = $\sigma(x)$
  - `parts[3]` = $\sigma(y)$
  - `parts[4]` = $\sigma(z)$
- Line B has 6 tokens corresponding directly to $\sigma(U_{11}/\text{iso}), \sigma(U_{22}), \sigma(U_{33}), \sigma(U_{12}), \sigma(U_{13}), \sigma(U_{23})$.

---


## 3. Reflection identity and verified layouts

Scale groups, data blocks, domains and phase selectors are distinct concepts.
A six-value scale row does not prove six independently refined scales; inspect
flags, group assignments and native listing. Jana amplitude scale s corresponds
to intensity factor s². Relative intensity normalization uses (s_run/s_ref)².

In verified single and joint SXD files, a trailing tag is 1000*sequence+block_id.
The low digits identify the data block, not the run or domain. Confirm the actual
convention before reindexing. Multi-block headers/counts and explicit domain fields
must remain consistent. Never concatenate blocks under one count or reuse a
single-block filter for a joint dataset.

For the verified SXD E-format M90 record (zero-based slices): hkl [0:12], I
[12:27], sigma [27:42], scale [42:46], flag [46:50], domain [50:54], Tbar
[54:62], wavelength [62:70], six direction cosines [70:118], then trailing
fields/tag. Whitespace tokens 8 and 9 are Tbar and wavelength respectively.
In the observed non-E variant Tbar was [42:50]. These are importer/build-specific
layouts, not Mantid or universal Jana specifications. Validate representative
records and native settings rather than changing a header to claim E-format.

Probe an importer only in an isolated, structurally consistent repository.
Full-sized sentinel tests can verify field placement; a tiny reflection file
paired with stale master counts may fail. Reject NaN/Inf direction cosines,
overflow stars, count mismatches or ambiguous IDs even when an import completes.

## 4. M83 amplitudes versus intensities

In the verified SXD M83 output, zero-based tokens 9, 10, 11 are Fo, Fc and
sigma(Fo), NOT their squares. Token 8 is native residual D, token 7 is data
block, and the trailing observation tag joins the original measurement. Confirm
these meanings by reconstructing native R1 and relating Fo²/Fc² to input I and
active amplitude scales. An intensity ratio is (Fo/Fc)²; an amplitude ratio is
Fo/Fc. Do not interchange sigma(Fo) and sigma(I). Extinction changes the relation
to uncorrected input intensity, so validate it for the active model.

Legacy diagnostic CLI: `--hkl` remains a Mantid 22-column input (zero-based
wavelength token 18, d token 19). Unique hkl matching is permitted only when both
sides are unique. Repeated hkl requires `--observations map.csv` with columns
`sequence,h,k,l,wavelength_A,d_A`; sequence is the full native trailing tag.
Build that map from verified import provenance, not arbitrary row enumeration.
Missing/duplicate IDs, mismatched hkl and unsupported multiple blocks fail before
output. The legacy filter rejects multi-block inputs and in-place writes.

The parser reports raw ai by default; `--mult` explicitly supplies Nsym/Msite
only for a model where that conversion is appropriate for all reported atoms.
Mixed multiplicities require per-site interpretation outside the legacy helper.
Legacy parser/editor M40 support is single-phase, single-scale, no preamble;
complex layouts must be handled by validated layout-aware code, not guessed offsets.

---

## 5. The `.m81` File (Binary 3D Fourier Density Map)

Generated when running `FOURIER` (e.g., Difference Fourier $\Delta\rho(\mathbf{r}) = \rho_{\text{obs}}(\mathbf{r}) - \rho_{\text{calc}}(\mathbf{r})$).
- **Binary Layout**:
  - Unformatted stream of 32-bit little-endian IEEE floats (`<f4`).
  - Given grid dimensions $(N_x, N_y, N_z)$ (reported in the `.fou` listing or determined from unit-cell grid spacing $\approx 0.1\text{ \AA}$):
    - Each $z$-plane has `plane_size = Nx * Ny * 4` bytes.
    - The file size is `(Nz + 1) * plane_size` bytes.
    - **Block 0** (`bytes[0 : plane_size]`): Header metadata block.
    - **Blocks `1 .. Nz`**: The $N_z$ two-dimensional slices for $z_k = k / N_z$ ($k = 0 \dots N_z - 1$).
    - Each slice of `Nx * Ny` floats must be reshaped in **Fortran column-major order**:
      ```python
      floats = struct.unpack(f'<{Nx*Ny}f', data[(z + 1) * plane_size : (z + 2) * plane_size])
      grid[:, :, z] = np.array(floats).reshape((Nx, Ny), order='F')
      ```
- **Units**: For neutron diffraction (`formtab -62`), $\Delta\rho$ is in $\text{fm/\AA}^3$. Background RMS noise is $\sigma_{\text{RMS}} = \sqrt{\langle \Delta\rho^2 \rangle}$.
- Use [scripts/analyze_fourier_m81.py](../scripts/analyze_fourier_m81.py) to automatically determine/verify grid dimensions, interpolate $\Delta\rho$ at candidate Wyckoff sites, and plot 2D contour maps.
