# Jana2020 Verified Import Wizard & GUI Navigation Guide

AI agents frequently guess or hallucinate Jana2020 menu names and wizard prompts based on generic crystallography software (like SHELXL, FullProf, or Olex2). Every dialog title, radio button, checkbox, and menu path in this guide has been **verified against the live Jana2020 GUI**.

---

## 1. Step-by-Step HKL Import Wizard (Creating `.m95` & `.m90`)

When starting from a raw reflection file (such as a 22-column ORNL SNS TOPAZ / Corelli Mantid `.hkl` file), guide the user through these exact steps:

### Step 1: Create a New Structure
1. Open **Jana2020** $\rightarrow$ click **`File -> Structure -> New`** (or `File -> New structure`).
2. Browse to the target project directory and type the structure name (e.g., `MnTe_340K`).

### Step 2: Select Reflection Format Type
- **Actual Radio Option**: Select **`"Single crystal: known diffractometer formats"`** (do *not* tell the user to look for a plain `"Single crystal"` option).
- Click **`Next`**.

### Step 3: Select Diffractometer & Input `.hkl` File
- **`"Data reduction file from:"`** dropdown: Select **`"TOPAZ, Corelli"`** (for SNS TOF Laue Mantid `.hkl` files) or the appropriate diffractometer format.
- **`"Input file name:"`** file picker:
  - *Quirk*: By default, Jana pre-fills this box with `<structure_name>.hkl`. If the actual `.hkl` file has a different filename (e.g., `MnTe_340K_Hexagonal_P.hkl`), instruct the user to click **`Browse`** and select the real `.hkl` file.
-Click **`Next`**.

### Step 4: Complete / Correct Experimental Parameters (Manual Cell Entry!)
- **Critical Quirk**: On the `"complete / correct experimental parameters"` screen, the **`"cell parameters:"`** field is **blank by default** for TOPAZ `.hkl` imports (because Mantid `.hkl` files do not embed unit cell headers).
- **Agent Action**: Always provide the exact $a, b, c, \alpha, \beta, \gamma$ values upfront in your instructions so the user can type them directly into `"cell parameters:"` (space-separated, e.g., `4.1522 4.1522 6.7162 90 90 120`).
- Click **`Next`**.

### Step 5: Derived Lattice Parameters, Twins & Data Repository
1. Jana displays the lattice parameters and `"derived lattice parameters from actual"` and asks if there are any twins.
2. Instruct the user to click **`Next`**, then **`Next`** again.
3. Jana shows the **`"Data repository"`** table listing `(File, Type of data, Used radiation)` — e.g., `(MnTe_*.hkl, Single crystal, Neutrons TOF)`.
4. Click **`OK`** (or **`Next`**).

### Step 6: Create Refinement Reflection File (`.m90`)
Jana opens the reflection file creation dialog:
- **Unobserved threshold**: `Reflections I < [ 3 ] * sig(I) will be sorted as unobserved.` (Set to `3`).
- **Checkboxes**:
  - **`[x] use in output file E-format (recommended for data with large dynamical range)`** — **ALWAYS CHECK THIS** for TOF neutron data! TOF reflections span many orders of magnitude; leaving E-format unchecked can cause `******` fixed-point format overflows in `.m90`.
  - **`[ ] run in silent mode`**
- Click **`OK`** / **`Next`**.
- Jana reports the number of reflections read and written (e.g., `1462/1472 reflections read / written, no rejections due to systematic extinctions` — zero rejections occur here because the space group is still $P1$ during initial import).

### Step 7: Accept the DatBlock
Jana presents three radio buttons:
- `( ) Accept the new DatBlock and calculate coverage`
- `(*) Accept the new DatBlock`
- `( ) Discard the new DatBlock`
- Instruct the user to select **`"Accept the new DatBlock"`** (or calculate coverage) and click **`Finish`**.

### Step 8: Quit Superflip
1. Jana displays an info prompt: *"In the next step, the program opens Superflip for structure solution by charge flipping. Other structure solution methods can be started in the Structure Solution section in the left pane, which collects structure solution programs defined by the User via Settings->Programs."* $\rightarrow$ Click **`OK`** / **`Next`**.
2. Jana opens the **`"Run Superflip"`** dialog.
3. When refining a known structure, instruct the user to click **`"Quit"`** to land in the main Jana2020 window.

---

## 2. Why CIF Import Crashes (`READCIF` Error 59) & How to Bypass It

### The Crash
If the user tries to import a `.cif` file that contains standard uncertainties in parentheses (such as `_cell_length_a 4.1532(3)` or atomic coordinate s.u.'s), Jana2020's Fortran CIF parser (`ReadCIF.f90`) crashes with:
```text
forrtl: severe (59): list-directed I/O syntax error, unit -5, file Internal List-Directed Read
Routine: READCIF (ReadCIF.f90)
```
Even if a stripped CIF is imported via **`Import -> model from CIF`**, Jana prompts an `"Import model"` dialog with two radio options:
- `Transform the model into the current cell` (must be chosen to preserve reflection indexing)
- `Transform reflections files into the imported cell`

### Recommended Agent Bypass (Zero-Click Structure Setup)
Once the user completes **Step 7–8** of the Import Wizard above, Jana has **already written `<project>.m95` and `<project>.m90` to disk**!
Instead of making the user import a CIF or manually add atoms in the GUI:
1. Write the complete `<project>.m50` (with space group symmetry cards, `atlist`, and `formtab -62` for neutrons) and `<project>.m40` (with atomic positions, occupancies, and refinement flags) directly to disk.
2. Have the user open `<project>.m50` via **`File -> Open`** (and if symmetry was changed from $P1$, click `Reflection file -> Create refinement reflection file` or accept the automatic prompt to re-create `.m90` with systematic extinctions filtered).

---

## 3. Verified Main Window Menu Map (When Using the GUI)

If the user is inspecting or modifying settings inside the Jana2020 GUI, use these **exact** menu paths and tab names:

### A. Cell, Symmetry, Composition & Magnetic Options
- **Menu Path**: **`Edit structure parameters -> Edit basic parameters (cell, symmetry, etc.)`**
- **Tabs inside the dialog**:
  1. **`Cell` tab**:
     - `Title of the structure`
     - `Cell parameters`: space-separated (`a b c alpha beta gamma`)
     - `s.u.'s of cell parameters`: space-separated
  2. **`Symmetry` tab**:
     - `Space group`: defaults to `P1`; click **`"select from list"`** to choose e.g. `P63/mmc`.
     - `Origin shift`: `0 0 0`
     - Also includes buttons: `complete the set`, `make test`, `run Stokes & Campbell SG-test`, `define local symmetry operators`.
  3. **`Composition` tab**:
     - `Formula - list of atomic types`: space-separated element symbols (e.g., `"Mn Te"` or `"Mn Te Li"`).
     - `Formula units`: integer $Z$ (defaults to `1`; set to e.g. `2` for NiAs-type unit cell).
  4. **`Magnetic parameters` tab**:
     - Checkbox: `Activate the magnetic option`.
- **Re-creating `.m90` after Symmetry Change**:
  - Closing `"Edit basic parameters"` after changing symmetry triggers a dialog titled **`"Question"`**:
    *"The program has detected a change of the symmetry/twinning which call for re-creation of the reflection file. Do you want to re-create refinement reflection file just now?"*
  - Instruct the user to click **`Yes`**, set `I < 3 * sig(I)`, and check **`[x] use in output file E-format`**. Jana will now reject systematically extinct reflections according to the space group.

### B. Adding & Editing Atoms (`New -> New atom` vs. `Edit atoms`)
- **Critical Quirk**: When a structure has 0 atoms, **`Edit structure parameters -> Edit atoms` DOES NOT EXIST** in the dropdown menu!
- **Adding the First Atom via GUI**:
  1. Click **`New -> New atom`** in the top menu.
  2. Type the fractional coordinates (e.g. `0 0 0`) into the **`"New atom coordinates:"`** box.
  3. Click **`"Include the peak at the specified position"`**.
  4. Enter **`"Name of the atom:"`** (e.g. `Mn1`), chemical type (`Mn`), and keep the pre-filled **`"Occupancy reduction"`** (which Jana auto-calculates as $N_{\text{sym}} / M_{\text{site}}$, e.g. `12` for a 2-fold site in $P6_3/mmc$).
  5. Once at least one atom exists, **`Edit structure parameters -> Edit atoms`** appears in the menu.
- **Wyckoff Letter Display Quirk (`4e` vs `2a`)**:
  - In space group $P6_3/mmc$, an atom placed at $(0, 0, 0)$ (true Wyckoff position $2a$, multiplicity 2) is displayed as **`4e`** in the `Edit atoms` GUI window!
  - *Why*: In Jana's internal table, site $4e$ $(0, 0, z)$ is listed before $2a$ $(0, 0, 0)$, and $z = 0$ satisfies $(0, 0, z)$. As long as `.m40` has refinement flags `000` for $(x, y, z)$ and occupancy divisor `12` ($\text{occ} = 0.083333$), it is genuinely treated as $2a$.

### C. Scale Factor & Extinction Dialogs
- **Scale Factor Dialog**:
  - Shows checkboxes: `TOverall: 0 [ ]`, `scale1: 1.535602 [x]`, `scale2: 0 [ ]` ... `scale6: 0 [ ]`, and a spinner `Maximal number of scales: 6 (up/down)` that cannot be reduced below `6`, with `scale2..scale6` greyed out.
  - Explain to the user that `6` is simply Jana's minimum display page size; only `scale1 [x]` is active and refined for a single dataset.
- **Extinction Dialog**:
  - Dropdown **`Extinction model`**:
    - `None`
    - `Isotropic - Becker Coppens`
    - `Anisotropic - Becker Coppens`
    - `SHELX model`
  - Options: **`Type 1`** (mosaic spread dominated) / **`Type 2`** (particle size dominated); **`Gaussian`** / **`Lorentzian`** distribution; **`Radius [cm] 0.01`** *(used only if `tbar` is not present on the `.m90` file)*.
  - Checkbox: **`GIso`** (defaults to `0.01`, checked `[x]`).

### D. Refinement Commands (Equations, Restrictions, Restraints)
- **Menu Path**: **`Refinement -> Refinement Commands`** (NOT `Refinement -> Parameters`).
- **Actual Tabs in `Refinement Commands`**:
  - `Restrictions`
  - `Equations`
  - `Fixed commands`
  - `Dontuse/Useonly command`
  - `Scale command`
  - `Partial RFactors`
  - `Distance restraints`
  - `Angle restraints`
  - `Torsion angle restraints`
  - `Magnetic moment restraints`
  - `Keep commands`

### E. Running Refinement & Reflection File Utilities
- **Run Least-Squares Refinement**:
  - Click **`Refinement -> Run refinement`** (NOT `Refine -> Start`).
  - When finished, Jana prompts: `"Regular end of REFINE program. Open the listing? Yes/No"`.
- **Reflection File Menu (`Reflection file`)**:
  - `Import/modify reflection file`
  - `Run reimport in the silent mode`
  - `Make space group test`
  - `Create refinement reflection file`
  - `View listing from the merging process`
  - `Manual culling`
  - `Run statistic test - Wilson plot`
  - `List of observed vs. calculated intensities`
