"""Complete the established regional protocol under the frozen T5 geometry."""
from pathlib import Path
from dataclasses import asdict
import copy
import fcntl
import json
import numpy as np
import pandas as pd
from sklearn.metrics import pairwise_distances_argmin
import week05_core as a
import local_resolution as b

ROOT = Path(__file__).resolve().parents[1]
lock = (ROOT / '.week05_build/T5_regions.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
frozen = ROOT / 'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240'
data, audit, regions, old_refs, provenance = a.prepare_development(ROOT)
spec = json.loads((frozen / 'frozen_model/specification.json').read_text())
seal = json.loads((frozen / 'frozen_model/freeze_seal.json').read_text())
for filename, digest in seal['files'].items():
    assert a.file_sha256(frozen / 'frozen_model' / filename) == digest
registry = pd.read_parquet(frozen / 'all_respondents_T5_eligibility_and_frozen_profiles.parquet')
labels = registry.set_index('WPID_RANDOM').loc[data.WPID_RANDOM, 'T5_cluster'].to_numpy(int)
t5 = a.Specification('T5','optimized',spec['spec']['t'],'optimized',spec['spec']['alpha'],5)
a.SPECIFICATIONS = {'T5':t5}
a.WORKING_PROFILE_LABELS['T5'] = {int(k):v for k,v in spec['profile_names'].items()}
b.SPECIFICATIONS = a.SPECIFICATIONS
design = copy.deepcopy(a.REGIONAL_DESIGN)
design.update(version=4, specifications={'T5':asdict(t5)})
centres = np.load(frozen / 'frozen_model/centres.npy')
assert np.array_equal(pairwise_distances_argmin(a.transform(data,t5),centres),labels)
refs = {'T5':{'labels':labels,'centres':centres,'spec':asdict(t5)}}
context = a.digest_json({'data':provenance,'design':design,'frozen_seal':a.file_sha256(frozen/'frozen_model/freeze_seal.json'),
    'regional_code':a.file_sha256(ROOT/'.week05_build/week05_core.py'),
    'selection_code':a.file_sha256(ROOT/'.week05_build/local_resolution.py'),
    'runner':a.file_sha256(Path(__file__))})
out = ROOT / 'course_artifacts/week05_T5_completion' / context[:16]
(out/'fits').mkdir(parents=True,exist_ok=True)
a.atomic_json({'output':str(out.relative_to(ROOT)),'context':context},out.parent/'current_run.json')
a.atomic_json({'context':context,'regional_design':design,'local_selection':b.LOCAL_SELECTION_DESIGN,
    'frozen_global_model_refitted':False,'regional_fitting_uses_development_only':True,
    'country_distance_heldout_role':'post-validation descriptive extension', 'provenance':provenance},out/'protocol.json')
regions.to_csv(out/'development_regions.csv',index=False)
prevalence, profiles, semantics = a.fixed_global_geographical_results(data,refs,regions,out)
reference_summary, fitted = a.regional_references(data,refs,design,out,context)
reference_profiles = pd.read_csv(out/'regional_original_profiles.csv')
decisions, diagnostics = b.select_local_resolutions(reference_summary,reference_profiles)
decisions.to_csv(out/'additional_local_shortlist.csv',index=False)
diagnostics.to_csv(out/'all_local_resolution_diagnostics.csv',index=False)
matched = [(int(r),'T5',5) for r in regions.GlobalRegion]
shortlist = sorted(set(matched + list(decisions[['region','candidate','k']].itertuples(index=False,name=None))))
print('Recorded before stability:',len(shortlist),'cases',flush=True)
b.selection_profile_review(data,decisions,fitted,out)
stability = a.regional_stability(data,fitted,shortlist,design,out,context,n_jobs=1)
recovery = b.cluster_recovery_summary(data,shortlist,fitted,out/'fits',context,out)
supported = b.supported_resolution_summary(data,regions,stability,recovery,reference_summary,out)
a.matched_regional_semantics(reference_profiles,profiles,pd.read_csv(out/'regional_overlaps.csv'),out)
b.plot_local_stability_grid(supported,regions,out)
results = {'status':'regional_complete','context':context,'reference_cases':len(reference_summary),
    'tested_stability_cases':len(shortlist),'successful_stability_fits':int(stability.successful_fits.sum()),
    'failed_stability_fits':int(stability.failed_fits.sum()),
    'both_full_tests_supported':int(supported.status.eq('both full stability benchmarks met').sum()),
    'limited_diagnostics':int(supported.status.ne('not qualified by the applicable stability benchmarks').sum()
                              -supported.status.eq('both full stability benchmarks met').sum()),
    'global_T5_refits':0}
a.atomic_json(results,out/'regional_complete.json')
print(json.dumps(results),flush=True)
