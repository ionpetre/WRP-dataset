from pathlib import Path
import os
import local_resolution as a

root=Path(__file__).resolve().parent.parent
base_info=a.json.loads((root/'.week05_build/points12_run.json').read_text())
base_output=root/base_info['output_directory']
data,regions,references,provenance,base_context,reference_summary,profiles=a.base_analysis_load(root,base_output)
manifest=a.json.loads((base_output/'run_manifest.json').read_text())
assert a.digest_json({'provenance':provenance,'design':a.REGIONAL_DESIGN,
    'implementation_sha256':a.file_sha256(root/'.week05_build/week05_core.py')})==base_context
decisions,diagnostics=a.select_local_resolutions(reference_summary,profiles)
extension_hash=a.file_sha256(root/'.week05_build/local_resolution.py')
selection_context=a.digest_json({'base_context':base_context,'selection_design':a.LOCAL_SELECTION_DESIGN,
    'shortlist':decisions[['region','candidate','k']].to_dict('records'),'extension_code_sha256':extension_hash})
output=root/'course_artifacts/week05_local_resolutions_v4'/selection_context[:16]
output.mkdir(parents=True,exist_ok=True)
if not (output/'fits').exists():
    (output/'fits').symlink_to(os.path.relpath(base_output/'fits',output),target_is_directory=True)
a.atomic_json({'base_output':str(base_output.relative_to(root)),'base_context':base_context,
    'selection_context':selection_context,'selection_design':a.LOCAL_SELECTION_DESIGN,
    'extension_code_sha256':extension_hash,'heldout_responses_used':False},output/'selection_manifest.json')
a.atomic_json({'output_directory':str(output.relative_to(root)),'base_output_directory':str(base_output.relative_to(root)),
              'selection_context':selection_context},root/'.week05_build/local_selection_run.json')
a.table_write(decisions,output/'additional_local_shortlist.csv')
a.table_write(diagnostics,output/'all_local_resolution_diagnostics.csv')
print('Selection recorded before new fits:',len(decisions),'additional resolutions.',flush=True)
fitted={}
for region,name,k in decisions[['region','candidate','k']].itertuples(index=False,name=None):
    frame=data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
    fitted[(region,name,k)]=a.reference_cache(frame,region,name,k,base_output/'fits',base_context)
review=a.selection_profile_review(data,decisions,fitted,output)
print('Reference profile review saved; no new reference fits.',flush=True)
if '--review-only' in __import__('sys').argv:raise SystemExit(0)
shortlist=decisions[['region','candidate','k']].itertuples(index=False,name=None)
shortlist=list(shortlist)
additional=a.regional_stability(data,fitted,shortlist,a.REGIONAL_DESIGN,output,base_context,n_jobs=2)
matched=[(int(region),name,spec.global_k) for region in sorted(data.GlobalRegion.unique()) for name,spec in a.SPECIFICATIONS.items()]
all_shortlist=sorted(set(shortlist+matched))
for region,name,k in matched:
    frame=data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
    fitted[(region,name,k)]=a.reference_cache(frame,region,name,k,base_output/'fits',base_context)
combined=a.pd.concat([a.pd.read_csv(base_output/'regional_stability_summary.csv'),additional],ignore_index=True)
a.table_write(combined,output/'combined_regional_stability_summary.csv')
recovery=a.cluster_recovery_summary(data,all_shortlist,fitted,base_output/'fits',base_context,output)
supported=a.supported_resolution_summary(data,regions,combined,recovery,reference_summary,output)
a.atomic_json({'additional_resolutions':len(decisions),'additional_successful_fits':int(additional.successful_fits.sum()),
    'additional_failed_fits':int(additional.failed_fits.sum()),'tested_resolutions_including_matched':len(all_shortlist),
    'both_full_benchmark_count':int(supported.status.eq('both full stability benchmarks met').sum()),
    'heldout_responses_used':False},output/'local_selection_complete.json')
print('Local resolution selection computations complete.',flush=True)
