#!/usr/bin/env python
"""
edit_jana_files.py - Programmatic modifier for Jana2020 .m40 and .m50 files.

Allows agents and scripts to safely modify:
  - 10-digit refinement flags for specific atoms in .m40
  - Crystallographic occupancies (ai) and fractional coordinates (x, y, z) in .m40
  - Extinction refinement flag on Line 5 of .m40
  - Extinction directive (iext) and constraint equations inside .m50

Usage Examples:
  # Set B1 flag to refine occ + aniso ADPs, and clear all equations in .m50
  python edit_jana_files.py path/to/Project \\
      --set-flag B1=1000101000 --set-flag D1=1001100000 --clear-equations

  # Set substitutional equation on 2a site
  python edit_jana_files.py path/to/Project \\
      --set-flag A1=1000101000 --set-flag D1=0000000000 --clear-equations \\
      --add-equation "occ[D1]=0.083333-occ[A1]" \\
      --add-equation "u11[D1]=u11[A1]" \\
      --add-equation "u33[D1]=u33[A1]"
"""

import argparse
import os
import re
import sys
import math
from observation_mapping import legacy_m40


def update_m40(m40_path, flag_updates=None, occ_updates=None, pos_updates=None, ext_flag=None):
    """Modify atom flags, occupancies, positions, or extinction flag in a .m40 file."""
    with open(m40_path, 'r', errors='ignore') as f:
        lines = f.readlines()

    legacy_m40(lines)
    su_idx = len(lines)
    for i, l in enumerate(lines):
        if 's.u. block' in l:
            su_idx = i
            break

    if ext_flag is not None and len(lines) >= 5:
        parts = lines[4].split()
        if len(parts) >= 7:
            parts[6] = ext_flag
            lines[4] = f" {float(parts[0]):8.6f} {float(parts[1]):8.6f} {float(parts[2]):8.6f} {float(parts[3]):8.6f} {float(parts[4]):8.6f} {float(parts[5]):8.6f}      {parts[6]}\n"

    flag_updates = flag_updates or {}
    occ_updates = occ_updates or {}
    pos_updates = pos_updates or {}

    i = 5
    while i < su_idx:
        line = lines[i].strip()
        if not line or line.startswith('----'):
            break
        parts = re.sub(r'(?<=\d)(?=[+-]\d*\.)', ' ', line).split()
        if len(parts) >= 7 and not parts[0][0].isdigit() and not parts[0].startswith('-'):
            tag = parts[0]
            type_idx = int(parts[1])
            adp_mode = int(parts[2])
            ai = float(parts[3])
            x, y, z = float(parts[4]), float(parts[5]), float(parts[6])

            if tag in occ_updates:
                ai = float(occ_updates[tag])
            if tag in pos_updates:
                x, y, z = pos_updates[tag]

            values=(ai,x,y,z)
            if not all(math.isfinite(v) and len(f'{v:9.6f}')==9 for v in values):
                raise ValueError('Nonfinite or overflowing fixed-width parameter')
            lines[i] = lines[i][:18] + ''.join(f'{v:9.6f}' for v in values) + lines[i][54:]

            if i + 1 < su_idx and tag in flag_updates:
                new_flag = flag_updates[tag]
                if not re.fullmatch(r'[01]{10}',new_flag):raise ValueError('Expected ten binary flags')
                lines[i+1]=lines[i+1][:60]+new_flag+lines[i+1][70:]
            i += 2
        else:
            i += 1

    with open(m40_path, 'w') as f:
        f.writelines(lines)


def update_m50(m50_path, iext_line=None, clear_equations=False, add_equations=None):
    """Modify the refine ... end refine block in a .m50 file."""
    with open(m50_path, 'r', errors='ignore') as f:
        lines = f.readlines()

    validate_m50(lines)
    new_lines=[];inside=False;seen=False
    for line in lines:
        s=line.strip()
        if s=='refine':inside=True
        if inside and s.startswith('iext') and iext_line is not None:
            new_lines.append(iext_line);seen=True;continue
        if inside and s.startswith('equation') and clear_equations:continue
        if s=='end refine':
            if iext_line is not None and not seen:new_lines.append(iext_line)
            for eq in add_equations or []:new_lines.append('  equation : '+eq+'\n')
            inside=False
        new_lines.append(line)
    with open(m50_path,'w') as f:f.writelines(new_lines)

def validate_m50(lines):
    text=''.join(lines)
    if text.count('\nrefine\n')!=1 or any(line.strip().startswith(('phase','extlabel','twin')) for line in lines):
        raise ValueError('Legacy editor rejects multi-phase/domain or dataset-specific layouts')


def main():
    parser = argparse.ArgumentParser(description="Programmatically modify Jana2020 .m40 and .m50 files.")
    parser.add_argument("project", help="Project base path (with or without .m40/.m50 extension).")
    parser.add_argument("--set-flag", action="append", default=[], help="Atom=10DigitFlag (e.g. B1=1000101000).")
    parser.add_argument("--set-occ", action="append", default=[], help="Atom=CrystallographicAi (e.g. D1=0.002500).")
    parser.add_argument("--set-pos", action="append", default=[], help="Atom=x,y,z (e.g. D1=0.333333,0.666667,0.750000).")
    parser.add_argument("--ext-flag", default=None, help="6-digit extinction flag on Line 5 of .m40 (e.g. 100000 or 000000).")
    parser.add_argument("--iext", type=int, choices=[0, 1, 2], default=None, help="Set iext mode in .m50 (0=off, 1=iso BC, 2=aniso BC).")
    parser.add_argument("--clear-equations", action="store_true", help="Remove all equation lines in .m50.")
    parser.add_argument("--add-equation", action="append", default=[], help="Add an equation line to .m50 (e.g. 'occ[D1]=0.083333-occ[A1]').")
    args = parser.parse_args()

    base = os.path.splitext(args.project)[0] if args.project.endswith(('.m40', '.m50', '.ref')) else args.project
    m40_path = base + ".m40"
    m50_path = base + ".m50"

    # Validate both project files before either can be changed.
    if os.path.exists(m40_path):
        with open(m40_path) as f:legacy_m40(f.read().splitlines())
    if os.path.exists(m50_path):
        with open(m50_path) as f:validate_m50(f.readlines())
    flag_updates = dict(item.split("=", 1) for item in args.set_flag)
    occ_updates = {k: float(v) for k, v in (item.split("=", 1) for item in args.set_occ)}
    pos_updates = {
        k: tuple(float(x) for x in v.split(","))
        for k, v in (item.split("=", 1) for item in args.set_pos)
    }

    if os.path.exists(m40_path) and (flag_updates or occ_updates or pos_updates or args.ext_flag is not None):
        update_m40(m40_path, flag_updates, occ_updates, pos_updates, args.ext_flag)
        print(f"Updated {m40_path}")

    iext_str = None
    if args.iext == 0:
        iext_str = "  iext 0\n"
    elif args.iext == 1:
        iext_str = "  iext 1 itypex 1 idistr 1 radius 0.01\n"
    elif args.iext == 2:
        iext_str = "  iext 2 itypex 1 idistr 1 radius 0.01\n"

    if os.path.exists(m50_path) and (iext_str is not None or args.clear_equations or args.add_equation):
        update_m50(m50_path, iext_line=iext_str, clear_equations=args.clear_equations, add_equations=args.add_equation)
        print(f"Updated {m50_path}")


if __name__ == "__main__":
    main()
