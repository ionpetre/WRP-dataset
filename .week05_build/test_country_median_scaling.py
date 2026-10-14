"""Validate saved median-relative matrices without data access or model fitting."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
OUT=ROOT/'course_artifacts/week05_country_median_scaling_v1/e1ecf01551bcf2da'
manifest=json.loads((OUT/'median_scaling_manifest.json').read_text())
assert not manifest['models_refitted'] and manifest['reference_countries']==142
full={k:pd.read_csv(RAW/f'{k}_all_countries_post_validation_matrix.csv',index_col=0) for k in ['worry','self','known','B','E']}
pairs={k:d.to_numpy()[np.triu_indices(len(d),1)] for k,d in full.items()}
shared=np.median(np.r_[pairs['B'],pairs['E']])
assert abs(shared-.1550977480973838)<1e-14
assert manifest['reference_medians']['B']==manifest['reference_medians']['E']==shared
for k in ['worry','self','known']:
    assert manifest['reference_medians'][k]==np.median(pairs[k])
for name,digest in manifest['files'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
for k,d in full.items():
    denominator=manifest['reference_medians'][k]
    for scope in ['development','all_countries_post_validation']:
        r=pd.read_csv(OUT/f'{k}_{scope}_median_relative_matrix.csv',index_col=0)
        assert np.max(np.abs(r.to_numpy()-d.loc[r.index,r.columns].to_numpy()/denominator))<1e-14
        assert np.allclose(r,r.T) and np.allclose(np.diag(r),0)
        a,b,c=np.random.default_rng(20261014).integers(0,len(r),size=(3,500))
        values=r.to_numpy();assert np.all(values[a,c]<=values[a,b]+values[b,c]+1e-12)
    assert (d.to_numpy()/denominator).max()>2,'Values above the colour ceiling must remain uncapped.'
examples=pd.read_csv(OUT/'illustrative_median_relative_comparisons.csv')
assert abs(examples.query("reference=='USA' and peer=='CAN' and metric=='B'").median_relative_distance.iloc[0]-.40914335312111344)<1e-12
print('Passed: reference medians, pooled B/E median, 10 uncapped matrices, symmetry, scope invariance, triangle checks and examples.')
