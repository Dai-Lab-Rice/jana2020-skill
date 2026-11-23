---
name: jana2020-skill
description: >-
  Set up, automate and diagnose Jana2020/Jana2006 single-crystal X-ray and
  TOF neutron refinements, including reflection imports, native parameter
  files, joint datasets, magnetic structures, occupancy constraints, extinction
  and Fourier maps.
---

# Jana2020 refinement

Use native files for model construction and pywinauto for the interactive Windows
program. Do not assume batch REFINE/FOURIER switches exist. Discover the installed
Jana application and the Python environment used for Windows automation.
Read [Windows workflow](references/pywinauto_workflow.md) before GUI control.

## Essential workflow

1. Establish corrected elemental identities, symmetry operators, cell/indexing,
   radiation, temperatures and reduction/correction provenance. Preserve source
   reflections and a reproducible independent baseline.
2. Use Jana's import wizard when creating the native repository. Inspect controls,
   not guessed menu labels. Keep tests isolated and validate counts, numeric
   fields, scales/domains and observation identity before reuse.
3. Construct/edit `.m50`, `.m40` and `.m90` using their actual layout, not fixed
   line numbers from an example project. Read the [format reference](references/file_formats_m40_m50_m90.md).
   Fully occupied special sites use crystallographic occupancy
   ai = chemical_fraction × site_multiplicity / symmetry_order. General sites can
   have ai=1. Supply the appropriate per-site conversion; never assume ×12 globally.
4. Reopen the edited project, verify its full path, then run refinement. Jana caches
   equations and settings in memory and may overwrite disk edits. Confirm a fresh,
   regular end in `.ref`, actual equations/model, parameter counts, shifts,
   singularities, correlations and physical ADPs. Keep trials separate.
5. Compare scale → coordinates → isotropic ADPs before adding parameters. Lower R
   alone does not justify anisotropy, extinction or occupancy freedom. Check tensor
   eigenvalues in the proper Cartesian metric and inspect systematic residuals.

Read [joint datasets and corrections](references/joint_and_corrections.md) for
co-refinement, absorption or extinction. Read [measurement diagnostics](references/measurement_diagnostics.md)
for repeated intensities, wavelength effects, outliers or multiple diffraction.
Read [magnetic refinement](references/magnetic_refinement.md) for satellite
imports, propagation vectors, magnetic model comparisons or joint refinements.
Read [identifiability and pitfalls](references/crystallographic_pitfalls.md) for defects and Fourier interpretation.

Honor the user's image-review boundary: generate/export figures for review, but
view images only with explicit authorization. Prefer Markdown reports with data,
uncertainties, assumptions and artifact links. Never automatically cull large residuals.

## Helpers and supported boundaries

- `scripts/parse_jana_ref.py`: listing summaries and legacy single-phase M40 atoms;
  raw ai by default, chemical fractions only with explicit `--mult`. Unsupported
  M40 layouts are reported, not interpreted with incorrect offsets. Multiple listing
  residual summaries are retained; check the original per-dataset listing.
- `scripts/edit_jana_files.py`: targeted legacy single-phase edits. Unsupported
  preambles, multi-phase and dataset-specific extinction layouts fail before writing.
- Use `--hkl-layout sns-tof-hkl` with the verified 22-field TOPAZ/CORELLI nuclear
  export for both wavelength helpers. Confirm the source column against the native
  `.m90` using the [format reference](references/file_formats_m40_m50_m90.md#sns-tof-nuclear-export-and-observation-mapping).
  Repeated HKL requires an explicit `--observations` CSV keyed by the full native tag.
- `scripts/plot_extinction_wavelength.py` plots amplitude and intensity residual
  diagnostics from the observations listed in `.m83`.
- `scripts/filter_m90_wavelength.py` checks the mapped wavelengths against the
  single-block Jana E-format `.m90` before writing a sensitivity subset.
- `scripts/analyze_fourier_m81.py`: specialized binary-map utility; verify the actual
  binary layout, grid, units and normalization before interpreting its output.
  Supply dimensions from the current map and fractional coordinates for any sites to probe.

The bundled example files illustrate the legacy single-scale layout. See the
format reference for helper interfaces and verified importer-specific conventions.
