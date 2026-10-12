from pathlib import Path
import sys
import json
import frozen_transfer as a

root=Path(__file__).resolve().parent.parent
existing=root/'.week05_build/transfer_run.json'
if existing.exists() and '--freeze-only' not in sys.argv:
    info=json.loads(existing.read_text())
    package=root/info['package_directory'];output=root/info['output_directory']
    bundle,manifest=a.load_frozen_package(package)
    record=json.loads((output/'transfer_complete.json').read_text())
    assert record['freeze_context']==manifest['context']
    for key in ['tables','assignments']:
        for name,value in record[key].items():assert a.file_sha256(output/name)==value
    print('Completed sealed transfer already exists and its hashes verify; no repeated holdout execution.',flush=True)
    raise SystemExit(0)
folder,bundle,manifest,development,regions=a.freeze_existing_models(root)
print('Frozen package sealed and development replay verified:',folder,flush=True)
print('Held-out responses used at freeze:',manifest['heldout_responses_used_at_freeze'],flush=True)
if '--freeze-only' in sys.argv:raise SystemExit(0)
output,complete,assignments=a.run_heldout_transfer(root,folder,bundle,manifest,development,regions)
print('Fixed-model held-out transfer complete:',output,flush=True)
print('Assigned respondents:',len(complete),'countries:',complete.COUNTRY_ISO3.nunique(),flush=True)
