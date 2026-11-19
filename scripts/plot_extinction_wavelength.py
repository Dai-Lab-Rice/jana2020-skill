"""Mantid/M83 diagnostics with explicit observation joins; generate only."""
import argparse
import math
import numpy as np
from observation_mapping import mantid_records,join
def analyze_wavelength_dependence(hkl_path,m83_path,out_png=None,observations=None):
    records=[]
    with open(m83_path) as f:
        for line in f:
            p=line.split()
            if len(p)<12:continue
            try:
                h=tuple(map(int,p[:3]));seq=int(p[-1]);fo,fc,sig=map(float,p[9:12])
            except ValueError:continue
            if not all(math.isfinite(v) for v in (fo,fc,sig)):raise ValueError('Nonfinite M83 amplitude')
            records.append(dict(hkl=h,sequence=seq,Fo=fo,Fc=fc,sigma_Fo=sig))
    if not records:raise ValueError('No supported M83 records')
    matched=join(records,mantid_records(hkl_path),observations);usable=[]
    for r in matched:
        if r['Fc']<=0:continue
        a=r['Fo']/r['Fc'];usable.append(dict(r,amplitude_ratio=a,intensity_ratio=a*a))
    if not usable:raise ValueError('No positive calculated amplitudes')
    print(f'Matched {len(matched)}; {len(usable)} positive Fc; no significance cut.')
    print('Intensity ratio=(Fo/Fc)^2; amplitude ratio=Fo/Fc. Parity has no universal chemical meaning.')
    for parity in (0,1):
        rr=[r for r in usable if r['hkl'][2]%2==parity]
        if rr:print('l parity',parity,'N',len(rr),'median intensity ratio',np.median([r['intensity_ratio'] for r in rr]))
    if out_png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots()
        for parity in (0,1):
            rr=[r for r in usable if r['hkl'][2]%2==parity]
            ax.scatter([r['lam'] for r in rr],[r['intensity_ratio'] for r in rr],s=8,label=f'l parity {parity}')
        ax.axhline(1,color='gray');ax.set(xlabel='Wavelength (Å)',ylabel='(Fo/Fc)²');ax.legend();fig.tight_layout();fig.savefig(out_png);plt.close(fig)
    return usable
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hkl',required=True);p.add_argument('--m83',required=True);p.add_argument('--out-png');p.add_argument('--observations',help='CSV: sequence,h,k,l,wavelength_A,d_A')
    a=p.parse_args();analyze_wavelength_dependence(a.hkl,a.m83,a.out_png,a.observations)
if __name__=='__main__':main()
