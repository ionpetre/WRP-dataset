"""Fixed all-country diameter normalization of saved aggregates; no fitting."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

RAW_CONTEXT='e1ecf01551bcf2da'
SCOPES=['development','all_countries_post_validation']
METRICS=['worry','self','known','B','E']

def normalize_country_distances(root):
    root=Path(root).resolve()
    source=root/'course_artifacts/week05_country_response_distances_v1'/RAW_CONTEXT
    output=root/'course_artifacts/week05_country_distance_normalization_v1'/RAW_CONTEXT
    tables={key:pd.read_csv(source/f'{key}_all_countries_post_validation_matrix.csv',index_col=0) for key in METRICS}
    assert all(len(t)==142 for t in tables.values())
    diameters={key:float(table.to_numpy().max()) for key,table in tables.items()}
    shared=max(diameters['B'],diameters['E'])
    denominators={**diameters,'B':shared,'E':shared}
    output.mkdir(parents=True,exist_ok=True)
    for scope in SCOPES:
        for key in METRICS:
            table=pd.read_csv(source/f'{key}_{scope}_matrix.csv',index_col=0)
            norm=table/denominators[key] if denominators[key]>0 else table*0
            assert np.isfinite(norm.to_numpy()).all()
            assert norm.to_numpy().min()>=0 and norm.to_numpy().max()<=1+1e-12
            norm.to_csv(output/f'{key}_{scope}_normalized_matrix.csv')
    examples=pd.read_csv(source/'illustrative_country_comparisons.csv')
    examples['normalization_denominator']=examples.metric.map(denominators)
    examples['normalized_distance']=examples.distance/examples.normalization_denominator
    for key in ['worry','self','known']:
        examples[key+'_normalized']=examples[key]/denominators[key]
    examples.to_csv(output/'illustrative_normalized_comparisons.csv',index=False)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'version':1,'raw_context':RAW_CONTEXT,'reference_countries':142,
              'reference_scope':'all_countries_post_validation',
              'metric_diameters':diameters,'normalization_denominators':denominators,
              'normalization':'D_normalized(c,d)=D(c,d)/fixed_denominator; zero if denominator is zero',
              'overall_rule':'one shared maximum across B and E; never recompute per selected country or displayed subset',
              'component_rule':'each component uses its own all-country diameter; do not recombine normalized components',
              'display':'fixed seven equal-width bands on [0,1]; spell out distance names; no raw-distance/percentile clutter',
              'limits':'observed reference maximum, not theoretical dissimilarity or percentage similarity; post-validation display refinement',
              'models_refitted':False,'raw_results_overwritten':False,
              'source_manifest_sha256':sha(source/'analysis_manifest.json'),
              'implementation_sha256':sha(root/'.week05_build/country_distance_normalization.py'),
              'files':{p.name:sha(p) for p in output.iterdir() if p.name!='normalization_manifest.json'}}
    (output/'normalization_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    print(normalize_country_distances(args.root))
