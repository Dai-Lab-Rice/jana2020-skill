"""Explicit, one-to-one observation joins for legacy reflection helpers."""
import csv
import math
from collections import Counter

def mantid_records(path):
    rows=[]
    with open(path) as f:
        for line in f:
            p=line.split()
            if len(p)<20:continue
            try:
                h=tuple(map(int,p[:3]));lam=float(p[18]);d=float(p[19])
            except ValueError:continue
            if h==(0,0,0):continue
            if not all(math.isfinite(x) and x>0 for x in (lam,d)):
                raise ValueError('Nonfinite/nonpositive wavelength or d')
            rows.append(dict(hkl=h,lam=lam,d=d))
    if not rows:raise ValueError('No supported Mantid records')
    return rows

def mapping(path):
    if not path:return None
    result={}
    with open(path,newline='') as f:
        for r in csv.DictReader(f):
            seq=int(r['sequence']);h=tuple(int(r[k]) for k in ('h','k','l'))
            lam=float(r['wavelength_A']);d=float(r['d_A'])
            if seq in result or seq<=0:raise ValueError('Duplicate/invalid observation sequence')
            if not all(math.isfinite(x) and x>0 for x in (lam,d)):raise ValueError('Invalid mapped wavelength/d')
            result[seq]=dict(hkl=h,lam=lam,d=d)
    return result

def join(records,source,observations=None):
    """records contain full native sequence tags and hkl; preserve native order."""
    if len({r['sequence'] for r in records})!=len(records):raise ValueError('Duplicate native sequence tag')
    if len({r['sequence']%1000 for r in records})!=1:raise ValueError('Unsupported multiple data blocks')
    explicit=mapping(observations)
    if explicit is not None:
        if set(explicit)!=set(r['sequence'] for r in records):raise ValueError('Missing/extra mapped observation IDs')
        out=[]
        for r in records:
            q=explicit[r['sequence']]
            if q['hkl']!=r['hkl']:raise ValueError('Sequence/hkl mismatch')
            out.append(dict(r,**{k:q[k] for k in ('lam','d')}))
        # A sidecar must describe the companion source observations, not a different dataset.
        def signature(q):return (q['hkl'],round(q['lam'],8),round(q['d'],8))
        if Counter(map(signature,out))!=Counter(map(signature,source)):
            raise ValueError('Mapped observations do not match companion source wavelength/d multiset')
        return out
    a=Counter(r['hkl'] for r in records);b=Counter(r['hkl'] for r in source)
    if any(v!=1 for v in a.values()) or any(v!=1 for v in b.values()):
        raise ValueError('Repeated hkl requires --observations sequence-keyed CSV')
    lookup={r['hkl']:r for r in source};out=[]
    for r in records:
        if r['hkl'] not in lookup:raise ValueError('Unmatched hkl; positional fallback is forbidden')
        q=lookup[r['hkl']];out.append(dict(r,lam=q['lam'],d=q['d']))
    return out

def legacy_m40(lines):
    """Validate the narrow layout supported by legacy parameter helpers."""
    try:
        n=int(lines[0].split()[0]);assert len(lines[0].split())==5
        assert len(lines[1].split())==7
        assert len(lines[2].split())==4
        assert len(lines[3].split())==7 and len(lines[4].split())==7
        for j in range(n):
            line=lines[5+2*j];assert len(line[:10].strip())>0
            # Fixed coordinate fields validate adjacent negative values too.
            assert int(line[10:11])>0 and int(line[11:14]) in (1,2)
            assert all(math.isfinite(float(line[k:k+9])) for k in range(18,54,9))
        assert 's.u. block' in lines[5+2*n]
    except (AssertionError,ValueError,IndexError) as e:
        raise ValueError('Unsupported M40 layout: requires legacy single-phase/single-scale, no commands preamble') from e
    return n
