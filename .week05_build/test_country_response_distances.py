"""Numerical checks for the direct-response extension; no model fitting."""
from pathlib import Path
import base64
import json
import numpy as np
import pandas as pd
from country_response_distances import response_matrices, pair_percentiles

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
payload=json.loads((OUT/'response_map_payload.json').read_text())
q=np.frombuffer(base64.b64decode(payload['probabilities_f64_base64']),dtype='<f8').reshape(payload['shape'])
matrices=response_matrices(q)
metadata=pd.read_csv(OUT/'country_metadata.csv').set_index('COUNTRY_ISO3').loc[payload['country_order']]
for key,matrix in matrices.items():
    saved=pd.read_csv(OUT/f'{key}_all_countries_post_validation_matrix.csv',index_col=0).to_numpy()
    assert np.max(np.abs(saved-matrix))<1e-14
    dev=np.flatnonzero(metadata.country_split.eq('train'))
    saved_dev=pd.read_csv(OUT/f'{key}_development_matrix.csv',index_col=0).to_numpy()
    assert np.max(np.abs(saved_dev-matrix[np.ix_(dev,dev)]))<1e-14
    for scope,selected in [('development',dev),('all_countries_post_validation',np.arange(len(q)))]:
        sub=matrix[np.ix_(selected,selected)]
        p=pair_percentiles(sub)
        oracle=pd.read_csv(OUT/f'{key}_{scope}_percentiles.csv',index_col=0).to_numpy()
        assert np.allclose(p,oracle,equal_nan=True)
        assert np.isnan(np.diag(p)).all()
        assert np.isfinite(p[~np.eye(len(p),dtype=bool)]).all()
    rng=np.random.default_rng(20261014)
    for a,b,c in rng.integers(0,len(matrix),size=(1000,3)):
        assert matrix[a,c]<=matrix[a,b]+matrix[b,c]+1e-12

# Construct valid 46-category laws with only one block differing.
low=[];high=[]
for count in [3]*6+[2]*14:
    low.extend([1.]+[0.]*(count-1));high.extend([0.]*(count-1)+[1.])
toy=response_matrices(np.array([low,high,low]))
assert all(toy[k][0,1]==1 and toy[k][0,2]==0 for k in toy)
self_only=np.array(low);self_only[18:32]=np.array(high)[18:32]
toy=response_matrices(np.array([low,self_only]))
assert toy['worry'][0,1]==0 and toy['self'][0,1]==1 and toy['known'][0,1]==0
assert toy['B'][0,1]==.25 and toy['E'][0,1]==.125
examples=pd.read_csv(OUT/'illustrative_country_comparisons.csv')
assert examples.query("reference=='USA' and peer=='CAN' and metric=='B'").iloc[0]['rank']==1
assert examples.query("reference=='USA' and peer=='IRN' and metric=='B'").iloc[0]['rank']==19
assert examples.query("reference=='FIN' and peer=='ISL'")['rank'].eq(1).all()
print('Passed: exact aggregate encoding, all five distance matrices, symmetry, bounds, 5,000 triangle checks, both percentile pools, component budgets and recorded examples.')
