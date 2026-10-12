from pathlib import Path
import week05_core as w
import json

root=Path(__file__).resolve().parent.parent
data,audit,regions,references,provenance=w.prepare_development(root)
implementation=w.file_sha256(Path(__file__).with_name('week05_core.py'))
context=w.digest_json({'provenance':provenance,'design':w.REGIONAL_DESIGN,'implementation_sha256':implementation})
output=root/'course_artifacts/week05_regional_validation_v3'/context[:16]
output.mkdir(parents=True,exist_ok=True)
w.atomic_json({'context':context,'provenance':provenance,'regional_design':w.REGIONAL_DESIGN,
               'implementation_sha256':implementation,'design_approved':True,'heldout_responses_used':False},output/'run_manifest.json')
w.atomic_json({'output_directory':str(output.relative_to(root)),'context':context},root/'.week05_build/points12_run.json')
print('OUTPUT',output,flush=True)
prevalence,profiles,semantics=w.fixed_global_geographical_results(data,references,regions,output)
quality,thresholds=w.fixed_assignment_quality(data,references,regions,output)
print('Fixed-global prevalence and representation quality complete.',flush=True)
summary,fitted=w.regional_references(data,references,w.REGIONAL_DESIGN,output,context)
shortlist=[(int(region),name,spec.global_k) for region in sorted(data.GlobalRegion.unique()) for name,spec in w.SPECIFICATIONS.items()]
stability=w.regional_stability(data,fitted,shortlist,w.REGIONAL_DESIGN,output,context,n_jobs=2)
local_profiles=w.pd.read_csv(output/'regional_original_profiles.csv')
overlaps=w.pd.read_csv(output/'regional_overlaps.csv')
w.matched_regional_semantics(local_profiles,profiles,overlaps,output)
w.atomic_json({'reference_candidates':len(summary),'reference_successes':int(summary.status.eq('ok').sum()),
               'successful_stability_fits':int(stability.successful_fits.sum()),
               'failed_stability_fits':int(stability.failed_fits.sum()),
               'heldout_responses_used':False},output/'points12_computation_complete.json')
print('Points 1/2 numerical computation complete.',flush=True)
