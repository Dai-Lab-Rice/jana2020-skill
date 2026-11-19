#!/usr/bin/env python
"""
parse_jana_ref.py - Comprehensive parser for Jana2020 / Jana2006 (.ref + .m40).

Extracts R-factors, GOF, reflection/parameter counts, scale & extinction (Giso),
active user equations, singularity warnings, high correlations (>0.90), and
atomic occupancies, coordinates, and ADPs with standard uncertainties (handling
the 5-token s.u. block offset in .m40).

Usage:
  C:\\Users\\hplfz\\miniconda3\\python.exe parse_jana_ref.py <path_to_dir_or_ref> [--mult 12.0]
"""

import argparse
import glob
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def parse_m40(m40_path, mult=12.0):
    """Parse scale, Giso, and atomic parameters + s.u. block from a .m40 file."""
    if not os.path.exists(m40_path):
        return None

    with open(m40_path, 'r', errors='ignore') as f:
        lines = [l.rstrip('\r\n') for l in f.readlines()]

    su_idx = -1
    end_su_idx = len(lines)
    for i, l in enumerate(lines):
        if 's.u. block' in l:
            su_idx = i
        elif su_idx != -1 and l.startswith('----'):
            end_su_idx = i
            break

    if len(lines) < 5:
        return None

    try:
        n_atoms = int(lines[0].split()[0])
        scale_val = float(lines[1].split()[0])
        ext_val = float(lines[4].split()[0])
    except (ValueError, IndexError):
        return None

    scale_su = 0.0
    ext_su = 0.0
    if su_idx != -1 and su_idx + 4 < end_su_idx:
        try:
            scale_su = float(lines[su_idx + 1].split()[0])
            ext_su = float(lines[su_idx + 4].split()[0])
        except (ValueError, IndexError):
            pass

    atoms = {}
    atom_order = []
    # Parse main atom block (lines 5 to su_idx)
    limit = su_idx if su_idx != -1 else len(lines)
    i = 5
    while i < limit and len(atom_order) < n_atoms:
        line = lines[i].strip()
        if not line or line.startswith('----'):
            break
        parts = line.split()
        # Atom coordinate line has 7 tokens: Name TypeIdx ADPMode occ x y z
        if len(parts) >= 7 and not parts[0][0].isdigit() and not parts[0].startswith('-'):
            tag = parts[0]
            try:
                type_idx = int(parts[1])
                adp_mode = int(parts[2])
                ai = float(parts[3])
                x, y, z = float(parts[4]), float(parts[5]), float(parts[6])
                adp_line = lines[i + 1].split() if (i + 1) < limit else []
                u11 = float(adp_line[0]) if len(adp_line) >= 1 else 0.0
                u33 = float(adp_line[2]) if len(adp_line) >= 3 else 0.0
                flag = adp_line[6] if len(adp_line) >= 7 else ''
                atoms[tag] = {
                    'type_idx': type_idx,
                    'adp_mode': adp_mode,
                    'ai': ai,
                    'occ': ai * mult,
                    'x': x, 'y': y, 'z': z,
                    'u11': u11, 'u33': u33,
                    'flag': flag,
                    'ai_su': 0.0, 'occ_su': 0.0,
                    'x_su': 0.0, 'y_su': 0.0, 'z_su': 0.0,
                    'u11_su': 0.0, 'u33_su': 0.0,
                }
                atom_order.append(tag)
                i += 2
                continue
            except (ValueError, IndexError):
                pass
        i += 1

    # Parse s.u. block (Note 5-token offset on atom line: Name su_occ su_x su_y su_z)
    if su_idx != -1:
        j = su_idx + 5
        while j < end_su_idx:
            line = lines[j].strip()
            if not line or line.startswith('----'):
                break
            parts = line.split()
            if parts and parts[0] in atoms and len(parts) >= 5:
                tag = parts[0]
                try:
                    ai_su = float(parts[1])
                    x_su, y_su, z_su = float(parts[2]), float(parts[3]), float(parts[4])
                    adp_su = lines[j + 1].split() if (j + 1) < end_su_idx else []
                    u11_su = float(adp_su[0]) if len(adp_su) >= 1 else 0.0
                    u33_su = float(adp_su[2]) if len(adp_su) >= 3 else 0.0
                    atoms[tag].update({
                        'ai_su': ai_su,
                        'occ_su': ai_su * mult,
                        'x_su': x_su, 'y_su': y_su, 'z_su': z_su,
                        'u11_su': u11_su, 'u33_su': u33_su,
                    })
                    j += 2
                    continue
                except (ValueError, IndexError):
                    pass
            j += 1

    return {
        'scale': scale_val, 'scale_su': scale_su,
        'giso': ext_val, 'giso_su': ext_su,
        'atoms': atoms,
        'atom_order': atom_order,
    }


def parse_ref(ref_path, mult=12.0):
    """Parse a Jana .ref file and its companion .m40 file."""
    if not os.path.exists(ref_path):
        return None

    with open(ref_path, 'r', errors='ignore') as f:
        content = f.read()

    res = {
        'file': ref_path,
        'r_obs': None, 'wr2_obs': None,
        'r_all': None, 'wr2_all': None,
        'gof_obs': None, 'gof_all': None,
        'nobs': None, 'nall': None, 'np': None,
        'max_shift_su': None, 'max_shift_param': None,
        'equations': [],
        'singularities': [],
        'correlations': [],
        'm40': None,
    }

    # User equations
    res['equations'] = re.findall(r'=>equation\s*:\s*(.+?)<=', content)

    # R-factors
    r_m = re.search(
        r'R\(obs\)=\s*([\d.]+)\s+wR2?\(obs\)=\s*([\d.]+)\s+R\(all\)=\s*([\d.]+)\s+wR2?\(all\)=\s*([\d.]+)',
        content
    )
    if r_m:
        res['r_obs'] = float(r_m.group(1))
        res['wr2_obs'] = float(r_m.group(2))
        res['r_all'] = float(r_m.group(3))
        res['wr2_all'] = float(r_m.group(4))

    gof_m = re.search(r'GOF\(obs\)=\s*([\d.]+)\s+GOF\(all\)=\s*([\d.]+)', content)
    if gof_m:
        res['gof_obs'] = float(gof_m.group(1))
        res['gof_all'] = float(gof_m.group(2))

    cnt_m = re.search(r'R factors\s*:\s*\[(\d+)=(\d+)\+(\d+)/(\d+)\]', content)
    if cnt_m:
        res['nall'] = int(cnt_m.group(1))
        res['nobs'] = int(cnt_m.group(2))
        res['np'] = int(cnt_m.group(4))

    sh_m = re.search(r'Maximum change/s\.u\.\s*:\s*([-\d.]+)\s*(?:for\s+([^\n\r|]+))?', content)
    if sh_m:
        res['max_shift_su'] = float(sh_m.group(1))
        res['max_shift_param'] = sh_m.group(2).strip() if sh_m.group(2) else ''

    # Singularities
    sing_matches = re.findall(
        r'In the cycle #(\d+) there was one singularity:\s*\r?\n\s*element #\d+\s*:\s*([^\r\n]+)',
        content
    )
    for cyc, param in sing_matches:
        res['singularities'].append(f"Cycle #{cyc}: {param.strip()}")

    # High correlations (>0.90)
    corr_matches = re.findall(r'([-\d.]+)\s+correlation\s*:\s*([^\s\r\n]+)', content)
    for val_str, pair in corr_matches:
        try:
            res['correlations'].append((pair.strip(), float(val_str)))
        except ValueError:
            pass

    # Companion .m40
    m40_path = os.path.splitext(ref_path)[0] + '.m40'
    res['m40'] = parse_m40(m40_path, mult=mult)
    return res


def print_detailed_report(res_list):
    headers = ["Trial", "N_obs/N_all", "R(obs)%", "wR2(obs)%", "GOF", "Giso", "Atom Summary (occ)" ]
    print("\n" + "=" * 110)
    print(f"{headers[0]:<26} | {headers[1]:<11} | {headers[2]:>7} | {headers[3]:>9} | {headers[4]:>5} | {headers[5]:>12} | {headers[6]}")
    print("-" * 110)

    for r in res_list:
        trial_name = os.path.basename(os.path.dirname(r['file'])) or os.path.basename(r['file'])
        n_str = f"{r['nobs']}/{r['nall']}" if r['nobs'] is not None else "N/A"
        robs = f"{r['r_obs']:.2f}" if r['r_obs'] is not None else "N/A"
        wr2 = f"{r['wr2_obs']:.2f}" if r['wr2_obs'] is not None else "N/A"
        gof = f"{r['gof_obs']:.2f}" if r['gof_obs'] is not None else "N/A"

        giso_str = "N/A"
        atom_summary = []
        if r['m40']:
            m = r['m40']
            giso_su_int = int(round(m['giso_su'] * 1e6))
            giso_str = f"{m['giso']:.6f}({giso_su_int})"
            for tag in m['atom_order']:
                d = m['atoms'][tag]
                occ_su_int = int(round(d['occ_su'] * 1e4))
                atom_summary.append(f"{tag}:{d['occ']:.4f}({occ_su_int})")

        print(f"{trial_name[:26]:<26} | {n_str:<11} | {robs:>7} | {wr2:>9} | {gof:>5} | {giso_str:>12} | {', '.join(atom_summary)}")

        if r['equations']:
            print(f"   [Equations]     : {'; '.join(r['equations'])}")
        if r['singularities']:
            print(f"   [SINGULARITIES] : {'; '.join(r['singularities'])}")
        if r['correlations']:
            corr_str = ", ".join([f"{p} ({v:+.3f})" for p, v in r['correlations']])
            print(f"   [Correlations]  : {corr_str}")
        if r['m40']:
            for tag in r['m40']['atom_order']:
                d = r['m40']['atoms'][tag]
                z_su_int = int(round(d['z_su'] * 1e5))
                u11_su_int = int(round(d['u11_su'] * 1e5))
                u33_su_int = int(round(d['u33_su'] * 1e5))
                u_label = "Uiso" if d['adp_mode'] == 1 else "U11"
                print(
                    f"     -> {tag:<4} (flag {d['flag']}): occ={d['occ']:.4f}({int(round(d['occ_su']*1e4))}), "
                    f"pos=({d['x']:.4f}, {d['y']:.4f}, {d['z']:.5f}({z_su_int})), "
                    f"{u_label}={d['u11']:.5f}({u11_su_int}), U33={d['u33']:.5f}({u33_su_int})"
                )
    print("=" * 110)


def main():
    parser = argparse.ArgumentParser(description="Parse Jana2020 .ref and .m40 files.")
    parser.add_argument("target", nargs="?", default=".", help="File (.ref) or directory to scan.")
    parser.add_argument("--mult", type=float, default=12.0, help="Multiplier from crystallographic ai to formula-unit occ (default: 12.0).")
    args = parser.parse_args()

    if os.path.isfile(args.target):
        ref_files = [args.target]
    else:
        ref_files = sorted(glob.glob(os.path.join(args.target, "**", "*.ref"), recursive=True))

    if not ref_files:
        print(f"No .ref files found in {args.target}")
        return

    parsed = [res for rf in ref_files if (res := parse_ref(rf, mult=args.mult)) is not None]
    print_detailed_report(parsed)


if __name__ == "__main__":
    main()
