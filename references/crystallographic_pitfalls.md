# Crystallographic & Least-Squares Pitfalls in Jana2020

This reference documents critical numerical, GUI, and physical pitfalls encountered during single-crystal refinements in Jana2020 and how to diagnose and prevent them.

---

## Pitfall 1: GUI In-Memory State Caching (Stale Equations & Extinction Settings)

### Symptom
You remove an `equation : ...` line from `.m50` on disk (for example, transitioning from a substitutional model on site $2a$ where `occ[Li1]=0.083333-occ[Mn1]` to an unconstrained interstitial model on site $2d$ where `Mn1` is fixed at `0.083333`), and set `Li1`'s refinement flag in `.m40` to `1000000000`. The user clicks `Refinement -> Run refinement` in Jana2020, and `occ[Li1]` immediately jumps to `0.000000` with its refinement flag reset to `0000000000`!

### Root Cause
While a project remains open in the Jana2020 GUI, Jana holds its `refine` command tree—especially **user equations** and **extinction flags**—in RAM. Clicking `Refinement -> Run refinement` does **not** re-read `.m50` from disk; instead, Jana writes its in-memory equations back out to `.ref` and `.m50` before starting `REFINE`.
In `.ref`, you will see:
```text
=>equation : occ[Li1]=0.083333-occ[Mn1]<=
  ... the equation not fulfilled, the initial value has been changed : 0.002500 => 0.000000
```

### Mandatory Prevention & Verification
1. **Before running refinement after any `.m50` change**, always instruct the user to either:
   - Re-open the project via **`File -> Open`** and select `<project>.m50` (forces Jana to discard RAM state and reload `.m50` and `.m40` from disk), **OR**
   - Open **`Refinement -> Refinement Commands -> Equations`**, click **`Delete all`**, and click **`OK`**.
2. **After every refinement**, grep the top of `.ref` for `=>equation` to verify that only intended equations were active!

---

## Pitfall 2: Scale–Sublattice Occupancy Singularity & The Circular Fit Trap

### Symptom
In a binary crystal $AB$ (or pseudo-binary $(A_{1-x}D_x)B$), you flag the overall scale factor $K$, the cation site occupancy (`occ[Mn1]` with `occ[Li1] = 0.083333 - occ[Mn1]`), **and** the anion site occupancy (`occ[Te1]`) to refine simultaneously.
The refinement converges quickly and reports your expected numbers, e.g., $\text{Li} = 3.0(7)\%$ and $\text{Te} = 0.947$.

### Why This Is a Circular Trap
Look at the bottom of `<project>.ref`:
```text
*************************************************
* List of parameters blocked due to singularity *
*************************************************
In the cycle #1 there was one singularity:
   element #6 : occ[Te1]
```
And in the `.m40` `s.u. block`, `Te1` has an unphysical s.u. (such as `3.879057`) or `0.000000` in `.ref`!

### Mathematical Explanation
Bragg diffraction intensities $I(\mathbf{h}) \propto K^2 |F(\mathbf{h})|^2$ provide only **two** macroscopic intensity observables across the two sublattices:
1. The overall scale factor $K^2$.
2. The single scalar ratio of sublattice scattering powers:
   $$\mathcal{R} = \frac{\Sigma b_{\text{anion}}}{\Sigma b_{\text{cation}}} = \frac{\text{occ}(\text{Te}) \cdot b_{\text{Te}}}{\text{occ}(\text{Mn}) \cdot b_{\text{Mn}} + \text{occ}(\text{Li}) \cdot b_{\text{Li}}}$$
Because there is **one** contrast ratio $\mathcal{R}$ and **two** compositional degrees of freedom ($\text{occ}(\text{Te})$ and $x_{\text{Li}}$), the normal matrix is singular ($\det = 0$).
- When Jana encounters this singularity in Cycle #1, it **blocks (freezes) `occ[Te1]` at its initial input value** and refines `occ[Mn1]` against it.
- If your initial input value for `occ[Te1]` ($0.947$) was obtained from an earlier trial where Li was fixed at $3.0\%$, then refining Li against that frozen $\text{Te} = 0.947$ **must mathematically return $\text{Li} = 3.0\%$**!
- **Rule**: Never claim that co-axial cation substitution and anion vacancy were refined independently when a singularity blocked one of them. Only an atom at a **third, spatially distinct Wyckoff position** (such as interstitial $2d$ or $4f$, which introduces $l$-dependent phase factors $\cos(2\pi l z)$) breaks the collinearity and allows both interstitial Li and host Te occupancies to refine simultaneously without singularity.

---

## Pitfall 3: Co-Located Substitutional Singularity ($r = -1.000$ Correlation)

### Symptom
Two atoms (`Mn1` and `Li1`) occupy the **exact same coordinates** $(0, 0, 0)$ with equal ADPs ($U_{ij}(\text{Li1}) = U_{ij}(\text{Mn1})$), and you allow **both** `occ[Mn1]` and `occ[Li1]` to refine freely without a sum equation (`occ[Mn1] + occ[Li1] = 1`).

### What Happens in Jana2020
Because $\mathbf{r}_{\text{Mn}} = \mathbf{r}_{\text{Li}}$ and $W_{\text{Mn}}(\mathbf{h}) = W_{\text{Li}}(\mathbf{h})$, their partial derivatives with respect to the structure factor $F(\mathbf{h})$ are strictly proportional for **every** reflection $(h, k, l)$:
$$\frac{\partial F(\mathbf{h})}{\partial \text{occ}(\text{Li})} = \frac{b_{\text{Li}}}{b_{\text{Mn}}} \frac{\partial F(\mathbf{h})}{\partial \text{occ}(\text{Mn})}$$
In `<project>.ref`, Jana reports:
```text
In the cycle #1 there was one singularity: element #8 : occ[Li1]
-1.000 correlation : occ[Mn1]/occ[Li1]
```
The individual occupancies drift to arbitrary numbers with $>100\%$ error bars (e.g., $\text{Mn} = 0.67 \pm 1.26$, $\text{Li} = 0.73 \pm 2.47$), while their **effective site scattering length** remains strictly invariant:
$$b_{\text{site}} = \text{occ}(\text{Mn}) \cdot b_{\text{Mn}} + \text{occ}(\text{Li}) \cdot b_{\text{Li}} = \text{constant}$$
- **Rule**: Co-located atoms on the same Wyckoff site **cannot** have both occupancies refined independently from single-wavelength/TOF neutron Bragg intensities without a total site occupancy constraint (`equation : occ[B] = max_occ - occ[A]`).

---

## Pitfall 4: Negative Neutron Scattering Lengths ($b_c < 0$) in Antisite & Fourier Analysis

Unlike X-ray atomic form factors ($f(s) > 0$, proportional to $Z$), neutron coherent scattering lengths $b_c$ can be **negative** (a $180^\circ$ phase shift in scattered neutron waves):
- $b_{\text{Mn}} = \mathbf{-3.73\text{ fm}}$ (negative)
- $b_{\text{Li}} = \mathbf{-1.90\text{ fm}}$ (negative)
- $b_{\text{Te}} = \mathbf{+5.80\text{ fm}}$ (positive)

This has two major consequences in Jana2020 refinements:

### 1. Difference Fourier Maps ($\Delta\rho = \rho_{\text{obs}} - \rho_{\text{calc}}$)
- A **missing positive scatterer** (like Te) appears as a **positive peak** ($+\Delta\rho > 0$) in `.fou` / `.m81`.
- A **missing negative scatterer** (such as interstitial $\text{Mn}_i$ or $\text{Li}_i$ in an empty Wyckoff hole) appears as a **deep negative well** ($-\Delta\rho < 0$)!
- When inspecting `.m81` for interstitial Mn or Li, always search for the **deepest minima ($\Delta\rho_{\min}$)** as well as maxima!

### 2. Antisite Defect Refinements ($\text{Te}_{\text{Mn}}$ vs. $\text{Mn}_{\text{Te}}$)
- Substituting Te ($+5.80\text{ fm}$) onto a Mn site ($-3.73\text{ fm}$) produces an enormous contrast change of $\Delta b = +9.53\text{ fm}$ per atom:
  $$b_{\text{site}}(2a) = (1 - x)(-3.73) + x(+5.80) = -3.73 + 9.53 x$$
- If the experimental diffraction data requires the cation sublattice to have *more* negative scattering power relative to Te (e.g., $b_{\text{site}} = -3.87\text{ fm}$ due to interstitial Mn or Te deficiency), a $\text{Te}_{\text{Mn}}$ antisite model (`equation : occ[Te2]=0.083333-occ[Mn1]`) will refine $x$ to a **statistically significant negative occupancy** (e.g. $x = -1.44(14)\%$, $-10.4\sigma$). A negative refined occupancy under a valid site-sum constraint is a definitive statistical rejection of that antisite defect.
