"""Explicitly requested single-block Mantid/M90 sensitivity subsets."""
import argparse
import re
from pathlib import Path
from observation_mapping import mantid_records,join
def filter_m90(hkl_path,m90_in,m90_out,min_lambda=0.,max_lambda=999.,min_d=0.,max_d=999.,observations=None):
    if Path(m90_in).resolve()==Path(m90_out).resolve():raise ValueError('Input overwrite is forbidden')
    lines=Path(m90_in).read_text().splitlines(keepends=True)
    starts=[j for j,l in enumerate(lines) if l.strip().startswith('Data')]
    if len(starts)!=1:raise ValueError('Legacy filter requires exactly one data block')
    j=starts[0];header=lines[:j+1];records=[]
    for line in lines[j+1:]:
        if not line.strip():continue
        p=line.split()
        try:records.append(dict(hkl=tuple(map(int,p[:3])),sequence=int(p[-1]),line=line))
        except (ValueError,IndexError) as e:raise ValueError('Unsupported reflection row') from e
    count=[l for l in header if l.strip().startswith('nref ')]
    if len(count)!=1 or int(count[0].split()[1])!=len(records):raise ValueError('Invalid input nref')
    matched=join(records,mantid_records(hkl_path),observations)
    keep=[r for r in matched if min_lambda<=r['lam']<=max_lambda and min_d<=r['d']<=max_d];new=[]
    for i,r in enumerate(keep,1):
        block=r['sequence']%1000
        new.append(re.sub(r'\d+\s*$',str(i*1000+block)+'\n',r['line']))
    header=[re.sub(r'^(\s*nref\s+)\d+',lambda m:m[1]+str(len(keep)),l) if l.strip().startswith('nref ') else l for l in header]
    Path(m90_out).write_text(''.join(header+new));print(f'Retained {len(keep)}/{len(records)}; source preserved.')
    return len(keep)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hkl',required=True);p.add_argument('--m90-in',required=True);p.add_argument('--m90-out',required=True)
    p.add_argument('--min-lambda',type=float,default=0.);p.add_argument('--max-lambda',type=float,default=999.)
    p.add_argument('--min-d',type=float,default=0.);p.add_argument('--max-d',type=float,default=999.)
    p.add_argument('--observations',help='CSV: sequence,h,k,l,wavelength_A,d_A')
    a=p.parse_args();filter_m90(a.hkl,a.m90_in,a.m90_out,a.min_lambda,a.max_lambda,a.min_d,a.max_d,a.observations)
if __name__=='__main__':main()
