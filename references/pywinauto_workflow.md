# Preferred Jana2020 Windows automation

## Environment and execution

Use pywinauto before computer-use tools or asking the user to click. The existing dedicated Miniconda environment is:

- Environment: `jana-ui`
- Prefix: `C:\Users\hplfz\miniconda3\envs\jana-ui`
- Interpreter: `C:\Users\hplfz\miniconda3\envs\jana-ui\python.exe`
- Verified packages: Python 3.11, pywinauto 0.6.9, pywin32 312.

Call the interpreter by absolute path; activation is unnecessary. Check it exists before use. Do not recreate the environment or install packages when it is already usable. If moved, discover the replacement with Conda rather than silently using base Python.

In the tested Codex session a sandboxed shell saw zero desktop windows, while an authorized unsandboxed shell could control Jana. An empty window list alone does not mean Jana is closed. Use the execution tool's approval mechanism for desktop access when necessary; never bypass a denial. User authorization for Jana automation persists within its stated scope.

## Reliable control sequence

1. Inspect windows with `Desktop(backend='win32')`; identify Jana by process, exact title, or handle. Inspect UIA controls separately with `Desktop(backend='uia')` when needed. Avoid broad clicks on whichever window happens to be active.
2. After editing project files, reopen the intended absolute `.m50` path. In the tested build the menu was `Structure->Open`. Native `menu_select` sometimes failed to gain foreground; resolving `main.menu_item('Structure->Open').item_id()` and posting `WM_COMMAND` with `win32gui.PostMessage` opened the dialog reliably.
3. Wait for the Open dialog, set its filename Edit (tested control ID 1148), and click Open (tested Button ID 1). Poll for the expected state with a bounded timeout. Verify the main title identifies the intended trial folder and there is no Error dialog before refinement. IDs are observations from this build: inspect controls if they differ.
4. Invoke the UIA Button named `Run refinement`. Wait for completion dialogs and newly written trial `.ref`/`.m40` files. A button invocation returning is not proof that refinement succeeded. Check output timestamps, final cycle, shift/s.u., singularities, and high correlations.
5. A post-run `Question` dialog can coexist with `Information from refinement` and disable the main window. Inspect the question before answering; in the tested run `No` declined an optional listing. Wait until Jana is enabled before opening another project.
6. For CIF export, the tested native tree was `SysTreeView32`, ID 1121. Expand `\CIF utilities` and double-click `\CIF utilities\CIF make`. Inspect options, accept the intended export settings, then fill the CIF filename (tested Edit ID 1001) and Save (Button ID 1). Validate the exported formula, symmetry, atom sites, cell, refinement statistics, and reflection count.

Use short scripts and output only relevant titles, control identifiers, and result summaries. If control metadata is insufficient, request explicit image-viewing authorization before inspecting any screenshot. Generating a figure or operating a GUI does not authorize image review. Preserve each trial in its own directory before running.

## Observed errors and limits

- `Incorrect flag for atomic type (=0)` was resolved by fixing the `.m40` ten-character atom-name field; the type index must immediately follow it.
- `forrtl: severe (64): input conversion error` at `REFLOOP` line 2090 occurred while the parent P1 import project was still open. It is not a unique diagnosis: verify the active project, fixed-column fields, reflection formatting, and scale layout before retrying.
- Preserve the imported `commands / maxsc / end` preamble and all scale and s.u. rows. The 360 K CORELLI example used 60 scales, not a universal count.
- Enable E-format through Jana's reflection-file creation dialog. Changing the `.m90` header alone does not convert data or prove a crash was caused by E-format. Validate count, numeric fields, absence of overflow asterisks, and sequence tags.
- For a commensurate magnetic hypothesis, an integration vector in `.int`/`.mat` is not independent evidence of measured satellite centers. Inspect fitted centroids or reciprocal-space profiles before changing q. At 340 K the exports recorded qz=0.4913; qz=0.5 remained unverified without the peak workspace or volume.

## Native controls, isolated execution and failures

Re-discover the application window/process after restarts; never hard-code a prior
PID or handle. Where foreground input is unavailable, native Button.click(),
Edit.set_edit_text(), posted menu commands and UIA invoke may work without
click_input()/set_focus(). This is normal control automation within the authorized
desktop session, not a reason to bypass access controls. IDs and menu commands
are observations from a particular build and must be rediscovered if they fail.

Treat CIF parenthesized-uncertainty and short-import crashes as observed build/input
failures, not universal CIF limitations. Prefer validated native construction or
a sanitized isolated copy; never strip source CIF uncertainties in place.
After a Fortran failure capture text diagnostics, preserve the failed trial, then
restart/reopen the intended independent project and verify its complete state.
Do not reuse a partially imported repository just because output files exist.

On Windows, absolute Python executable paths do not isolate DLL resolution from
PATH. An observed 0xc06d007f Python startup failure was avoided with a dedicated
numerical environment and a child-process PATH containing that environment's DLL
directories before other Conda entries. Diagnose environment/DLL collisions before
blaming diffraction data; avoid globally changing PATH or reinstalling environments.
Keep GUI automation and numerical analysis environments distinct when needed.
