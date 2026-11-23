# Crystallographic & Least-Squares Pitfalls in Jana2020

This reference documents critical numerical, GUI, and physical pitfalls encountered during single-crystal refinements in Jana2020 and how to diagnose and prevent them.

---

## Pitfall 1: GUI In-Memory State Caching (Stale Equations & Extinction Settings)

### Symptom
You remove an occupancy equation from `.m50` and free the dependent
atom's occupancy in `.m40`. After clicking `Refinement -> Run refinement`,
Jana restores the old equation or changes the initial occupancy and flags.
### Root Cause
While a project remains open in the Jana2020 GUI, Jana holds its `refine` command tree—especially **user equations** and **extinction flags**—in RAM. Clicking `Refinement -> Run refinement` does **not** re-read `.m50` from disk; instead, Jana writes its in-memory equations back out to `.ref` and `.m50` before starting `REFINE`.
In `.ref`, you will see:
```text
=>equation : occ[D1]=0.083333-occ[A1]<=
  ... the equation not fulfilled, the initial value has been changed : 0.002500 => 0.000000
```

### Mandatory Prevention & Verification
1. Reopen the edited project through the verified native Open command; clearing equations alone does not reload extinction or other settings. Prefer automation over requiring user clicks.
2. Verify the full project path and the active equations/settings in the new listing.

---

## Pitfall 2: Scale–Sublattice Occupancy Singularity & The Circular Fit Trap

### Symptom
In a binary structure with substitution on one site, you simultaneously
refine the overall scale, the substitution fraction, and occupancy of the
other sublattice. The refinement can converge even when the parameters
are underdetermined.
### Why This Is a Circular Trap
Look at the bottom of `<project>.ref`:
```text
*************************************************
* List of parameters blocked due to singularity *
*************************************************
In the cycle #1 there was one singularity:
   element #6 : occ[B1]
```
And in the `.m40` `s.u. block`, `B1` has an unphysical s.u. (such as `3.879057`) or `0.000000` in `.ref`!

### Identifiability

A global change in all site scattering powers can be exchanged against scale.
Co-located species with real, constant neutron scattering lengths and identical
ADPs have proportional occupancy derivatives. Additional coordinates or species
do not automatically make a model identifiable. Check the actual derivative rank,
blocked parameters, correlations, contrast and fitted constraints. A parameter
frozen at a value from a previous fit is not independently redetermined.
Use justified site-sum/composition constraints or additional independent contrast.

---

## Pitfall 3: Co-Located Substitutional Singularity ($r = -1.000$ Correlation)

### Symptom
Two species occupy the same site with identical ADPs. If both
crystallographic occupancies are free and the neutron scattering lengths
are real and constant, their structure-factor derivatives are proportional.
For nonzero $b_A$,

$$\frac{\partial F(\mathbf{h})}{\partial a_B} = \frac{b_B}{b_A}\frac{\partial F(\mathbf{h})}{\partial a_A}.$$

A Jana listing can report a blocked parameter or a correlation near $\pm1$.
The diffraction model determines the weighted site contribution
$a_A b_A + a_B b_B$. A justified chemistry constraint can fix the
total crystallographic occupancy to $M_{\text{site}}/N_{\text{sym}}$ for a
fully occupied site. Independent contrast can also help resolve the species.

---

## Pitfall 4: Negative Neutron Scattering Lengths ($b_c < 0$) in Antisite & Fourier Analysis

Neutron coherent scattering lengths can have either sign. In a
difference Fourier map with $\Delta\rho = \rho_{\text{obs}} - \rho_{\text{calc}}$,
a missing positive scatterer can produce a positive peak and a missing
negative scatterer can produce a negative peak. Inspect both extrema and
check the scattering table used for the current isotope composition.

For substitution of species $B$ onto a site occupied by $A$ with total site
occupancy fixed, the mean scattering length is $b_A + x(b_B-b_A)$, where $x$
is the substitution fraction. Use the sign and magnitude of $b_B-b_A$ to
compare candidate defects. A negative refined fraction is outside the
physical range of the constrained model. Check systematic errors,
weighting, and alternative explanations before interpreting it.
