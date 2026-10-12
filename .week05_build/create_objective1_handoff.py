"""Create an ID-linked reuse package; keep frozen models unchanged and excluded respondents unassigned."""
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd
from frozen_assignment import load_frozen_package,sha256

root=Path(__file__).resolve().parent.parent
info=json.loads((root/'.week05_build/transfer_run.json').read_text())
package=root/info['package_directory'];transfer=root/info['output_directory']
bundle,manifest=load_frozen_package(package)
folder=root/'course_artifacts/week05_objective1_handoff_v1'/manifest['context'][:16]
folder.mkdir(parents=True,exist_ok=True)
parts=[]
for split,source in [('train',package/'development_eligibility_and_assignments_all_respondents.parquet'),
                     ('heldout_country',transfer/'heldout_eligibility_and_assignments_all_respondents.parquet')]:
    frame=pd.read_parquet(source)
    weights_source=root/('course_artifacts/week03_development_data.parquet' if split=='train' else 'course_artifacts/week03_heldout_country_data.parquet')
    raw=pd.read_parquet(weights_source,columns=['WPID_RANDOM','WGT'])
    frame=frame.merge(raw,on='WPID_RANDOM',validate='one_to_one')
    frame['country_split']=split
    for name in ['B','E']:
        frame[name+'_cluster']=frame[name+'_cluster'].astype('Int16')
        frame[name+'_profile_name']=frame[name+'_cluster'].map(bundle['models'][name]['profile_names'])
        frame[name+'_profile_id']=frame[name+'_cluster'].map(lambda c:f'{name}_C{int(c)}' if pd.notna(c) else None)
    parts.append(frame)
all_rows=pd.concat(parts,ignore_index=True)
assert len(all_rows)==146910 and all_rows.WPID_RANDOM.is_unique
assert all_rows.COUNTRY_ISO3.nunique()==142 and all_rows.complete_case.sum()==137460
eligible=all_rows.loc[all_rows.complete_case].copy()
mass=eligible.groupby('COUNTRY_ISO3').WGT.transform('sum')
split_countries=eligible.groupby('country_split').COUNTRY_ISO3.transform('nunique')
eligible['equal_country_weight_within_split']=eligible.WGT/mass/split_countries
eligible['equal_country_weight_all_included_countries']=eligible.WGT/mass/142
for split,g in eligible.groupby('country_split'):
    assert np.isclose(g.equal_country_weight_within_split.sum(),1)
assert np.isclose(eligible.equal_country_weight_all_included_countries.sum(),1)
all_rows=all_rows.merge(eligible[['WPID_RANDOM','equal_country_weight_within_split','equal_country_weight_all_included_countries']],
    on='WPID_RANDOM',how='left',validate='one_to_one')
for name in ['B','E']:
    assert all_rows.loc[all_rows.complete_case,name+'_cluster'].notna().all()
    assert all_rows.loc[~all_rows.complete_case,name+'_cluster'].isna().all()
all_rows.to_parquet(folder/'all_respondents_eligibility_and_frozen_profiles.parquet',index=False)
all_rows.loc[all_rows.complete_case].to_parquet(folder/'profile_assigned_respondents.parquet',index=False)
objects=folder/'frozen_models';objects.mkdir(exist_ok=True)
for source in package.iterdir():
    if source.is_file():
        dest=objects/source.name
        if not dest.exists():shutil.copy2(source,dest)
        assert sha256(dest)==sha256(source)
load_frozen_package(objects)
completion={
    'objective1_status':'completed with qualified descriptive transfer conclusions',
    'freeze_context':manifest['context'],'final_scope':['B4','E8'],
    'development_prepared':116820,'development_assigned':109488,'heldout_prepared':30090,'heldout_assigned':27972,
    'all_prepared_respondents':146910,'all_assigned_respondents':137460,'excluded_unassigned':9450,
    'countries':142,'heldout_validation_countries':29,
    'conclusion':'Broad aggregate descriptive transfer with material country-specific representation limitations; not universal natural types',
    'B_role':'joint worry/harm description with stronger development individual-profile recovery',
    'E_role':'complementary thematic description; fragile re-estimated crime-related profiles remain an explicit limitation',
    'major_country_distance_limits':['Sierra Leone','Somalia','Namibia'],
    'regional_models':'contextual exploratory evidence only; do not replace the frozen global labels',
    'ARI_threshold_unchanged':.8,'ARI_used_as_holdout_threshold':False,'models_refitted':False,
    'reuse_rules':[
        'Join by unique WPID_RANDOM; keep COUNTRY_ISO3 and country_split.',
        'Excluded respondents have no B/E profile; do not fill missing profiles by imputation.',
        'Preserve B_C0..B_C3 and E_C0..E_C7 IDs; model order and names are not re-ranked by prevalence.',
        'Use equal_country_weight_within_split for split-specific summaries.',
        'Use equal_country_weight_all_included_countries for a country-balanced pooled assigned-cohort analysis; do not concatenate split-normalized weights unchanged.',
        'An all-country operational model would be a new artifact; no centre refitting is performed here.',
        'Later supervised modelling still requires an explicit country-level validation design; these descriptive labels do not authorize predictive leakage.'
    ],
    'transfer_record_sha256':sha256(transfer/'transfer_complete.json'),
    'files':{p.name:sha256(p) for p in sorted(folder.glob('*.parquet'))},
    'frozen_model_seal_sha256':sha256(objects/'freeze_seal.json')}
(folder/'objective1_completion_and_reuse.json').write_text(json.dumps(completion,indent=2,sort_keys=True))
(root/'.week05_build/handoff_run.json').write_text(json.dumps({'output_directory':str(folder.relative_to(root)),
    'freeze_context':manifest['context']},indent=2))
print('Objective 1 reuse package:',folder)
print('Preserved all 146,910 IDs; assigned 137,460; excluded 9,450 remain unassigned. Frozen model hashes unchanged.')
