"""Median-relative scaling of cached country summaries; never refit profiles."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

CONTEXT='e1ecf01551bcf2da'
METRICS=['worry','self','known','B','E']
SCOPES=['development','all_countries_post_validation']

def median_country_scaling(root):
    root=Path(root).resolve()
    source=root/'course_artifacts/week05_country_response_distances_v1'/CONTEXT
    out=root/'course_artifacts/week05_country_median_scaling_v1'/CONTEXT
    full={k:pd.read_csv(source/f'{k}_all_countries_post_validation_matrix.csv',index_col=0) for k in METRICS}
    assert all(len(d)==142 for d in full.values())
    pools={k:d.to_numpy()[np.triu_indices(len(d),1)] for k,d in full.items()}
    medians={k:float(np.median(v)) for k,v in pools.items()}
    shared=float(np.median(np.concatenate([pools['B'],pools['E']])))
    denominators={**medians,'B':shared,'E':shared}
    assert all(v>0 for v in denominators.values()),'Median-relative scaling requires a positive reference median.'
    out.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for scope in SCOPES:
        for k in METRICS:
            raw=pd.read_csv(source/f'{k}_{scope}_matrix.csv',index_col=0)
            ratio=raw/denominators[k]
            assert np.isfinite(ratio.to_numpy()).all() and ratio.to_numpy().min()>=0
            ratio.to_csv(out/f'{k}_{scope}_median_relative_matrix.csv')
            values=ratio.to_numpy()[np.triu_indices(len(ratio),1)]
            summaries.append({'scope':scope,'metric':k,'reference_median':denominators[k],
                'median_ratio':float(np.median(values)),'maximum_ratio':float(values.max()),
                'share_pairs_above_colour_ceiling':float(np.mean(values>=2)),
                'distinct_pairs':len(values)})
    examples=pd.read_csv(source/'illustrative_country_comparisons.csv')
    examples['reference_median']=examples.metric.map(denominators)
    examples['median_relative_distance']=examples.distance/examples.reference_median
    examples.to_csv(out/'illustrative_median_relative_comparisons.csv',index=False)
    pd.DataFrame(summaries).to_csv(out/'median_relative_display_summary.csv',index=False)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'version':1,'raw_context':CONTEXT,'reference_countries':142,
       'reference_scope':'all_countries_post_validation','separate_metric_medians':medians,
       'reference_medians':denominators,'pooled_BE_values':20022,
       'rule':'R_m(c,d)=D_m(c,d)/fixed all-country median; overall B/E use median of pooled distinct-pair distances',
       'scope_rule':'do not recalibrate for selected countries or development-only display',
       'colour_rule':'seven fixed equal-width bands over [0,2], last colour includes larger values; label endpoint 2 or more',
       'numerical_labels':'uncapped ratios, not percentages of similarity',
       'limits':'post-validation display choice; 2 is not a significance/retention threshold; dependent pairs are not independent samples',
       'models_refitted':False,'raw_results_overwritten':False,'diameter_version_preserved':True,
       'source_manifest_sha256':sha(source/'analysis_manifest.json'),
       'implementation_sha256':sha(root/'.week05_build/country_median_scaling.py'),
       'files':{p.name:sha(p) for p in out.iterdir() if p.name!='median_scaling_manifest.json'}}
    (out/'median_scaling_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args();print(median_country_scaling(args.root))
