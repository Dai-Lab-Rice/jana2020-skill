# Measurement-level intensity diagnostics

Keep a unique observation key across source reflections, native inputs and
residual output. Signed hkl is not unique: the same reflection can be measured at
different wavelengths, runs, orientations and detectors. Never overwrite repeats
in an hkl dictionary or assume file ordering after filtering. Distinguish exact
hkl repeats from symmetry/Friedel equivalents under the justified scattering model.

## Wavelength dependence

First compare measured intensities within individual reflections, without Fcalc:
show raw intensities or I divided by a reflection's median, with error bars,
run/detector labels and wavelength coverage. Distinguish input measurement errors
from uncertainty in estimated normalization. Example selection should depend on
coverage, not the size/sign of the trend.

An independent mean per reflection separates structural strength from measurement
response. Compare run factors alone against run factors plus a simple wavelength
response, then preselected interactions for resolution, strength, run or detector.
Use intensity-space fitting to retain weak/nonpositive observations; log fitting
requires explicit treatment of positivity/selection bias. Vary weights and examine
whether a few strong reflections dominate. Strength groups based on measured means
are descriptive because the response itself can affect classification.

Hold out complete symmetry families to avoid leakage. Test within-run equivalents
with independent family/run means to remove constant run offsets. Report overlap,
design rank, sparse tails and confounding. At fixed d, lambda=2d sin(theta): changing
wavelength changes scattering angle, so angle and wavelength are not independent
causes. Apparent common curves do not prove all reflections respond identically.
Bootstrap at family level; label linearized bootstrap intervals as approximate.
Do not promote an exploratory response fit into a data correction without validation.

## Multiple diffraction / Renninger screening

For a primary reciprocal vector H, an elastic two-step path is k -> k+G -> k+H,
with second transfer H-G at the SAME wavelength. Exclude G=0 and G=H. Require
both legs to have nonzero scattering under the candidate structure/symmetry.
Use real/complex scattering appropriate to the experiment; magnetic, other-grain
and environment paths require separate treatment.

Evaluate the extra Ewald coincidence with recorded UB/orientation and wavelength.
Rounded primary centroids may miss the exact Ewald surface: report primary closure
and compare nominal geometry with a documented minimal primary-lock adjustment.
Do not confuse arithmetic vector closure with two-leg elastic satisfaction. Test
cell conventions, angular/wavelength tolerances and reciprocal-space cutoffs.
Large geometry adjustments relative to the assumed width limit conclusions.

F2(G)*F2(H-G) times angular proximity is a heuristic opportunity score, not a
predicted intensity or sign: enhancement and depletion require more physics.
More candidate paths occur at short wavelength, so control wavelength, run,
detector, resolution and reflection strength before linking scores to residuals.
Compare both structural residuals and model-independent repeat discrepancies.
A low score in a bounded search does not establish freedom from multiple scattering.
Use the result to select azimuthal or wavelength scans and obtain mosaicity and
resolution information before attempting quantitative corrections.

Sources: [IUCr multiple diffraction](https://onlinelibrary.wiley.com/iucr/itc/Cb/ch5o3v0001/sec5o3o3o6/),
[finite-resolution geometry](https://journals.iucr.org/a/issues/2015/01/00/td5022/).
