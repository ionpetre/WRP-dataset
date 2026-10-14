"""Aggregate-only tests for fixed diameter normalization."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
OUT=ROOT/'course_artifacts/week05_country_distance_normalization_v1/e1ecf01551bcf2da'
manifest=json.loads((OUT/'normalization_manifest.json').read_text())
assert manifest['reference_countries']==142 and not manifest['models_refitted']
assert manifest['source_manifest_sha256']==hashlib.sha256((RAW/'analysis_manifest.json').read_bytes()).hexdigest()
denominators=manifest['normalization_denominators']
assert denominators['B']==denominators['E']==max(manifest['metric_diameters'][k] for k in ['B','E'])
for name,digest in manifest['files'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
for key in ['worry','self','known','B','E']:
    full=pd.read_csv(RAW/f'{key}_all_countries_post_validation_matrix.csv',index_col=0)
    assert np.max(full.to_numpy())==manifest['metric_diameters'][key]
    for scope in ['development','all_countries_post_validation']:
        raw=pd.read_csv(RAW/f'{key}_{scope}_matrix.csv',index_col=0)
        scaled=pd.read_csv(OUT/f'{key}_{scope}_normalized_matrix.csv',index_col=0)
        assert np.max(np.abs(scaled.to_numpy()-raw.to_numpy()/denominators[key]))<1e-14
        assert np.allclose(scaled,scaled.T) and np.allclose(np.diag(scaled),0)
        rng=np.random.default_rng(20261014)
        a,b,c=rng.integers(0,len(scaled),size=(3,500))
        d=scaled.to_numpy()
        assert np.all(d[a,c]<=d[a,b]+d[b,c]+1e-12)
        assert np.max(np.abs(d-full.loc[scaled.index,scaled.columns].to_numpy()/denominators[key]))<1e-14
examples=pd.read_csv(OUT/'illustrative_normalized_comparisons.csv')
assert abs(examples.query("reference=='USA' and peer=='CAN' and metric=='B'").normalized_distance.iloc[0]-.118610)<1e-6
print('Passed: fixed full-country denominators, shared B/E scale, 10 matrices, scope invariance, symmetry, triangle inequalities and examples; no fitting.')
