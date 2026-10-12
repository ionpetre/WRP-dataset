"""Load the readable publication export; no fitting, tuning or private seal replay."""
from pathlib import Path
import json
import numpy as np
from assignment import derive_frozen_features, assign_frozen

def load_public_models(folder=None):
    folder=Path(folder) if folder is not None else Path(__file__).resolve().parent
    bundle=json.loads((folder/'models.json').read_text())
    for model in bundle['models'].values():
        model['centres']=np.asarray(model['centres'],dtype=float)
        model['profile_names']={int(k):v for k,v in model['profile_names'].items()}
        model['profile_distance_p95']={int(k):float(v) for k,v in model['profile_distance_p95'].items()}
    return bundle

def assign_complete_cases(prepared, folder=None):
    """Return eligible assignments only, plus the eligibility mask for transparent exclusions."""
    bundle=load_public_models(folder)
    features=derive_frozen_features(prepared)
    eligible=features[bundle['feature_order']].notna().all(axis=1)
    if not eligible.any(): return {},eligible
    return assign_frozen(features.loc[eligible].copy(),bundle),eligible
