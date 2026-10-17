"""Portable fixed-model assignment only. This module contains no fitting or tuning code."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits

WORRY_SOURCES = dict(zip(['food','water','crime','severe_weather','traffic','mental_health'],
                       ['WP20720','WP20721','WP20722','WP20723','WP22213','WP20726']))
HARM_SOURCES = dict(zip(list(WORRY_SOURCES)+['work'],
                      ['WP22442','WP22443','WP22444','WP22445','WP22446','WP22447','WP22448']))



def derive_frozen_features(prepared):
    """Original raw codes -> original-unit features; missing values stay missing."""
    result=prepared.copy()
    for domain,source in WORRY_SOURCES.items():
        raw=result[source]
        if not raw.dropna().isin([1,2,3,98,99]).all():raise ValueError('Unexpected raw worry code: '+source)
        expected=raw.map({1:2.,2:1.,3:0.,98:np.nan,99:np.nan})
        column='worry_'+domain
        if column in result and not np.allclose(result[column],expected,equal_nan=True):
            raise ValueError('Prepared worry recoding differs: '+column)
        result[column]=expected
    for domain,source in HARM_SOURCES.items():
        raw=result[source]
        if not raw.dropna().isin([1,2,3,4,98,99]).all():raise ValueError('Unexpected raw harm code: '+source)
        valid=raw.isin([1,2,3,4])
        expected=raw.map({1:1.,2:1.,3:1.,4:0.,98:np.nan,99:np.nan})
        column='harm_'+domain
        if column in result and not np.allclose(result[column],expected,equal_nan=True):
            raise ValueError('Prepared combined harm recoding differs: '+column)
        result[column]=expected
        result[column+'_personal']=np.where(valid,raw.isin([1,3]).astype(float),np.nan)
        result[column+'_known_person']=np.where(valid,raw.isin([2,3]).astype(float),np.nan)
    return result

def frozen_transform(frame,model,feature_order):
    values=frame[feature_order].to_numpy(float)
    if not np.isfinite(values).all():raise ValueError('Assignment requires all 20 original-unit features observed.')
    if not np.isin(values[:,:6],[0,1,2]).all() or not np.isin(values[:,6:],[0,1]).all():
        raise ValueError('Unexpected original-unit feature values.')
    spec=model['spec']
    worry=np.where(values[:,:6]==2,spec['top'],values[:,:6])/spec['top']
    mean=worry.mean(axis=1,keepdims=True)
    return np.column_stack([(worry-mean)*np.sqrt(spec['alpha']/6),mean*np.sqrt(spec['alpha']/6),
                            values[:,6:]*np.sqrt((1-spec['alpha'])/14)])

def frozen_country_weights(frame):
    if not len(frame) or not np.isfinite(frame.WGT).all() or not frame.WGT.gt(0).all():
        raise ValueError('Weights require a nonempty cohort with positive finite WGT.')
    weights=frame.WGT/frame.groupby('COUNTRY_ISO3').WGT.transform('sum')/frame.COUNTRY_ISO3.nunique()
    assert np.isclose(weights.sum(),1)
    assert np.allclose(weights.groupby(frame.COUNTRY_ISO3).sum(),1/frame.COUNTRY_ISO3.nunique())
    return weights.to_numpy()

def assign_frozen(frame,bundle):
    """Keep cluster IDs unchanged; use first centre on exact ties; return geometric diagnostics."""
    output={}
    for name,model in bundle['models'].items():
        matrix=frozen_transform(frame,model,bundle['feature_order'])
        with threadpool_limits(limits=1):distances=cdist(matrix,model['centres'],metric='euclidean')
        labels=distances.argmin(axis=1)
        ordered=np.sort(distances,axis=1)
        first,second=ordered[:,0],ordered[:,1]
        margin=np.divide(second-first,second,out=np.zeros_like(second),where=second>0)
        cutoff=np.array([model['profile_distance_p95'][int(c)] for c in labels])
        result=frame[['WPID_RANDOM','COUNTRY_ISO3','GlobalRegion']].copy()
        result['candidate']=name;result['cluster']=labels.astype('int16')
        result['nearest_distance']=first;result['second_nearest_distance']=second
        result['margin']=margin;result['beyond_development_profile_p95']=first>cutoff
        result['equal_country_weight']=frozen_country_weights(frame)
        output[name]=result
    return output
