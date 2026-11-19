# Joint datasets, absorption and extinction

## Controlled co-refinement

Start with independent fits and a combined-file independent control reproducing
each fit at reporting precision. Retain each dataset's cell, radiation/scattering
table, temperature, observation selection, weights and correction provenance.
Share only physically justified coordinates; keep scale, ADPs and extinction
dataset-specific initially. Different temperatures need not have identical coordinates.
Release selected equalities as diagnostic trials rather than forcing an unphysical ADP.
Report sensitivity to weighting instead of adjusting weights to obtain a desired model.

One verified native implementation uses separate structural phase copies, identity
domain machinery and fixed dataset selectors so each dataset sees only its own
copy. These are computational copies, not physical phase coexistence or refined
volume fractions. Native cards include `phasetwin` and dataset-specific `extlabel`;
generate a representative layout through Jana and verify its meaning. Do not
reuse a two-copy M40's line numbers or interpret selector rows as additional scales.
Check shared equations, selectors, expected parameter count and residuals per dataset.

## Absorption is not an extinction mean path

Transmission A = <exp[-mu(Lin+Lout)]>. A corrected intensity and its standard
uncertainty both divide by A. An absorption-weighted mean path is
Tbar = <(Lin+Lout) exp[-mu(Lin+Lout)]>/A; it is a separate extinction input.
Verified SXD/Jana Tbar and radius inputs use cm. Positive per-observation Tbar
supplies the path; radius is a fallback when a path is absent. Validate behavior
for the actual extinction model/build. Shape changes require refitting the mosaic
parameter; its numerical rescaling is not evidence of a physical crystal change.

Audit empirical absorption/frame scaling before adding another correction. Ones
in a transmission export and zeros in Tbar do not prove no upstream correction.
Record composition/isotopes, shape dimensions, axis assignment, illumination,
mount/flux contributions and mu(lambda). A 1/v approximation is not valid near
absorption resonances without checking cross sections. Do not transfer the neutron
crystal's dimensions to a different X-ray specimen.

Validate direction conventions against independent scattering angles and the
primary Ewald condition before integrating a shape. Document UB row/column and
goniometer conventions, raw-header versus structural-cell differences and finite
precision. Test quadrature convergence and ambiguous edge assignments.

X-ray reduction files can document empirical spherical-harmonic absorption and
frame scaling; a recorded movie alone does not establish numerical shape correction.
Retain weak/forbidden observations separately when assessing symmetry: missing
rows are not measured extinctions. Build compatible models with full operator,
basis/origin, multiplicity and stoichiometry checks, not space-group-name replacement.
Real nuclear scattering gives identical intensities for inverted enantiomorphs;
absolute handedness needs appropriate additional contrast/information.

Sources: [Jana cookbook](https://jana.fzu.cz/workshops/Jana2006%20Cookbook.pdf),
[Mantid weighted path lengths](https://docs.mantidproject.org/v6.3.0/algorithms/AddAbsorptionWeightedPathLengths-v1.html),
[ILL neutron booklet](https://www.ill.eu/media/old_files/user_upload/ILL/1_About_ILL/Documentation/ILL_brochure/NeutronDataBooklet.pdf).
