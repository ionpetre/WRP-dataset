"""Run the existing Objective 2 design with the frozen T5 target only."""
from pathlib import Path
import fcntl
import hashlib
import importlib.util
import json
import time

root = Path(__file__).resolve().parents[1]
source = root / '.week06_build/week06_t5_core.py'
spec = importlib.util.spec_from_file_location('week06_t5_core', source)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
lock = (root / '.week06_build/T5_run.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
start = time.monotonic()
context, out = core.initialise(root, hashlib.sha256(source.read_bytes()).hexdigest())
print('Results:', out, flush=True)
development, audit = core.load_cohort(root, context, 'train')
audit.to_csv(out / 'development_target_eligibility.csv', index=False)
x = core.prepare_predictors(development)
core.predictor_missingness(development, x, 'development').to_csv(
    out / 'development_predictor_missingness.csv', index=False)
summary, folds = core.development_cv(development, x, context, out, run=True)
print(summary.to_string(index=False), flush=True)
seal = core.freeze_supervised(development, x, summary, context, out, run=True)
print('Development choice:', seal['selection'], flush=True)
core.block_permutation(development, x, folds, seal, context, out, run=True)
heldout = core.heldout_test(root, context, out, seal, run=True)
core.make_figures(out)
record = {'status':'complete', 'results':str(out.relative_to(root)),
          'fingerprint':context['fingerprint'], 'implementation_sha256':context['implementation_sha256'],
          'selection':seal['selection'], 'elapsed_seconds':time.monotonic()-start,
          'profile_refits':False, 'heldout_retuning':False}
core.json_write(record, root / '.week06_build/T5_run_complete.json')
print(heldout.to_string(index=False), flush=True)
print(json.dumps(record), flush=True)
