"""Week 6 Objective 2: predict frozen profiles from external background variables.

This module never fits clusters, changes their labels or imputes missing targets.
All respondent-level outputs and executable fit objects are local protected results.
"""
from pathlib import Path
import hashlib
import json
import platform
import time
import warnings
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, log_loss
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

FREEZE='832b01713bc6b240'
FEATURE_BLOCKS={
    'Demographics and household':['Age','Gender','Education','Urbanicity2','EMP_2010',
        'INCOME_5','HouseholdSize','ChildrenInHousehold','WP1223'],
    'Financial buffer':['WP22228'],
    'Government and neighbour support':['WP22231_ALL','WP22232'],
    'Discrimination':['WP22259','WP22260','WP22261','WP22262','WP22263'],
    'Country income':['CountryIncomeLevel'],
}
PREDICTORS=[c for columns in FEATURE_BLOCKS.values() for c in columns]
NUMERIC=['Age']
CATEGORICAL=[c for c in PREDICTORS if c not in NUMERIC]
VALID_CODES={'Gender':[1,2],'Education':[1,2,3],'Urbanicity2':[1,2],
    'EMP_2010':[1,2,3,4,5,6],'INCOME_5':[1,2,3,4,5],
    'HouseholdSize':[1,2,3,4],'ChildrenInHousehold':[0,1,2,3,4,5],
    'WP1223':[1,2,3,4,5,8],'WP22228':[1,2],
    'WP22231_ALL':[1,2,3],'WP22232':[1,2,3],
    **{c:[1,2,97] for c in FEATURE_BLOCKS['Discrimination']},
    'CountryIncomeLevel':[1,2,3,4,9]}
MISSING_CODES={'Education':[9],'Urbanicity2':[9],'HouseholdSize':[9],
    'ChildrenInHousehold':[9],'WP1223':[6,7],'WP22228':[98,99],
    'WP22231_ALL':[99],'WP22232':[98,99],
    **{c:[98,99] for c in FEATURE_BLOCKS['Discrimination']}}
DESIGN={'version':2,'seed':20261014,'country_folds':5,'predictors':PREDICTORS,
    'models':{'majority':{'strategy':'prior'},
        'logistic':{'solver':'lbfgs','C':1.0,'max_iter':2000,'tol':1e-6},
        'random_forest':{'n_estimators':120,'max_depth':14,'min_samples_leaf':50,
            'max_features':'sqrt','bootstrap':True,'class_weight':None}},
    'numeric_preprocessing':'training equal-country-weighted median; weighted mean/SD; fixed missing indicator',
    'categorical_preprocessing':'explicit missing category; training one-hot encoder; unknown levels ignored',
    'fitting_weights':'equal country, relative WGT retained, mean weight rescaled to one',
    'evaluation_weights':'equal country, relative WGT retained, recomputed within evaluation population',
    'selection':'largest mean development-fold macro-F1; exact ties prefer logistic then forest then majority',
    'tuning':'none; fixed first-draft settings, not an optimized model search',
    'interpretation':'3 joint block permutations per fold on selected model; within-country for individual blocks, across countries for income',
    'heldout_uncertainty':'1000 uniform country bootstrap draws; fixed predictions and models',
    'profile_targets':{'T5':5},'profile_refits':False,
    'holdout_role':'supervised test outside selection; already used for Objective 1 validation',
    'cv_caution':'clustering targets were developed using all development countries; this is prediction of that fixed taxonomy, not a fully nested discovery evaluation'}

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def json_write(value,path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    temp.replace(path)

def country_weights(frame):
    if not frame.WGT.gt(0).all() or not np.isfinite(frame.WGT).all():
        raise ValueError('Survey weights must be positive and finite.')
    w=frame.WGT/frame.groupby('COUNTRY_ISO3').WGT.transform('sum')/frame.COUNTRY_ISO3.nunique()
    assert np.isclose(w.sum(),1)
    assert np.allclose(w.groupby(frame.COUNTRY_ISO3).sum(),1/frame.COUNTRY_ISO3.nunique())
    return w.to_numpy(float)

def initialise(root,implementation_hash):
    root=Path(root).resolve()
    paths={'development':'course_artifacts/week03_development_data.parquet',
        'heldout':'course_artifacts/week03_heldout_country_data.parquet',
        'assignments':f'course_artifacts/week05_t5_secondary_transfer/{FREEZE}/all_respondents_T5_eligibility_and_frozen_profiles.parquet',
        'dictionary':'23_wrp/WRP_2023_data_dictionary.csv',
        'split':'course_artifacts/week03_country_split.csv',
        'freeze_seal':f'course_artifacts/week05_t5_secondary_transfer/{FREEZE}/frozen_model/freeze_seal.json'}
    inputs={key:{'path':relative,'sha256':file_hash(root/relative)} for key,relative in paths.items()}
    reuse=json.loads((root/f'course_artifacts/week05_t5_secondary_transfer/{FREEZE}/transfer_complete.json').read_text())
    assert inputs['assignments']['sha256']==reuse['files']['all_respondents_T5_eligibility_and_frozen_profiles.parquet']
    assert inputs['freeze_seal']['sha256']==reuse['seal_sha256']
    context={'design':DESIGN,'inputs':inputs,'implementation_sha256':implementation_hash,
        'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,
        'pandas':pd.__version__,'frozen_cluster_context':reuse['context']}
    fingerprint=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
    out=root/'course_artifacts/week06_objective2_T5_prediction'/fingerprint[:16]
    out.mkdir(parents=True,exist_ok=True)
    context['fingerprint']=fingerprint
    if (out/'context.json').exists():
        assert json.loads((out/'context.json').read_text())==context
    else:
        json_write(context,out/'context.json')
    dictionary=pd.read_csv(root/paths['dictionary'])
    manifest=dictionary.loc[dictionary.variable.isin(PREDICTORS),['variable','label','value_labels','derivation']].copy()
    manifest['block']=manifest.variable.map({c:b for b,cs in FEATURE_BLOCKS.items() for c in cs})
    manifest['modelling_type']=np.where(manifest.variable.eq('Age'),'continuous with missing indicator','categorical')
    manifest['missing_codes']=manifest.variable.map(lambda c:json.dumps(MISSING_CODES.get(c,[])))
    manifest.to_csv(out/'predictor_manifest.csv',index=False)
    assert len(manifest)==len(PREDICTORS)==18
    return context,out

def load_cohort(root,context,split):
    root=Path(root)
    raw_key='development' if split=='train' else 'heldout'
    source=root/context['inputs'][raw_key]['path']
    assert file_hash(source)==context['inputs'][raw_key]['sha256']
    columns=['WPID_RANDOM','COUNTRY_ISO3','GlobalRegion','WGT','country_split']+PREDICTORS
    raw=pd.read_parquet(source,columns=columns)
    registry=pd.read_parquet(root/context['inputs']['assignments']['path'])
    registry=registry.loc[registry.country_split.eq(split)].copy()
    assert raw.WPID_RANDOM.is_unique and registry.WPID_RANDOM.is_unique
    assert set(raw.WPID_RANDOM)==set(registry.WPID_RANDOM)
    keys=raw[['WPID_RANDOM','COUNTRY_ISO3','WGT','country_split']].merge(
        registry[['WPID_RANDOM','COUNTRY_ISO3','WGT','country_split']],on='WPID_RANDOM',validate='one_to_one',suffixes=('_raw','_registry'))
    assert keys.COUNTRY_ISO3_raw.eq(keys.COUNTRY_ISO3_registry).all()
    assert keys.country_split_raw.eq(keys.country_split_registry).all()
    assert np.array_equal(keys.WGT_raw,keys.WGT_registry)
    frame=raw.merge(registry[['WPID_RANDOM','complete_case','exclusion_reason','T5_cluster','T5_profile_id']],on='WPID_RANDOM',validate='one_to_one')
    for model,k in DESIGN['profile_targets'].items():
        assert frame.loc[frame.complete_case,model+'_cluster'].isin(range(k)).all()
        assert frame.loc[~frame.complete_case,model+'_cluster'].isna().all()
        for label in range(k):
            assert frame.loc[frame[model+'_cluster'].eq(label),model+'_profile_id'].eq(f'{model}_C{label}').all()
    audit=frame.groupby('exclusion_reason',dropna=False).size().rename('respondents').reset_index()
    audit['split']=split
    frame=frame.loc[frame.complete_case].copy().reset_index(drop=True)
    n,countries=(109488,113) if split=='train' else (27972,29)
    assert len(frame)==n and frame.COUNTRY_ISO3.nunique()==countries
    return frame,audit

def prepare_predictors(frame):
    """Deterministic code validation only; no data-dependent fitting here."""
    x=frame[PREDICTORS].copy()
    if not x.Age.dropna().between(15,99).all():
        raise ValueError('Unexpected prepared Age code; do not treat age 100 as substantive.')
    for column in CATEGORICAL:
        allowed=VALID_CODES[column]+MISSING_CODES.get(column,[])
        unexpected=sorted(set(x[column].dropna())-set(allowed))
        if unexpected:
            raise ValueError(f'Unexpected codes in {column}: {unexpected}')
        x[column]=x[column].replace(MISSING_CODES.get(column,[]),np.nan)
        x[column]=x[column].map(lambda value:'missing' if pd.isna(value) else str(int(value)))
    # 97 is not applicable, not an absence of discrimination. 9 is a real
    # unclassified country-income category, not a secretly imputed income group.
    return x

def predictor_missingness(frame,x,scope):
    w=country_weights(frame)
    rows=[]
    for column in PREDICTORS:
        missing=x[column].isna().to_numpy() if column in NUMERIC else x[column].eq('missing').to_numpy()
        country=frame[['COUNTRY_ISO3']].assign(missing=missing)
        rows.append({'scope':scope,'feature':column,'missing_count':int(missing.sum()),
            'missing_fraction':float(missing.mean()),'equal_country_missing_fraction':float(w@missing),
            'countries_all_missing':int(country.groupby('COUNTRY_ISO3').missing.all().sum()),
            'not_applicable_count':int(x[column].eq('97').sum()) if column in CATEGORICAL else 0})
    return pd.DataFrame(rows)

def fit_preprocessor(x,weights):
    values=x.Age.to_numpy(float)
    observed=np.isfinite(values)
    order=np.argsort(values[observed],kind='stable')
    sorted_values=values[observed][order]
    cumulative=np.cumsum(weights[observed][order])
    median=float(sorted_values[np.searchsorted(cumulative,cumulative[-1]/2)])
    filled=np.where(observed,values,median)
    mean=float(weights@filled/weights.sum())
    scale=float(np.sqrt(weights@((filled-mean)**2)/weights.sum())) or 1.
    encoder=OneHotEncoder(handle_unknown='ignore',sparse_output=False,dtype=np.float32)
    encoder.fit(x[CATEGORICAL])
    return {'age_median':median,'age_mean':mean,'age_scale':scale,'encoder':encoder,
        'predictors':PREDICTORS.copy(),'categorical':CATEGORICAL.copy()}

def transform_predictors(x,preprocessor):
    assert list(x.columns)==PREDICTORS
    age=x.Age.to_numpy(float)
    missing=~np.isfinite(age)
    filled=np.where(missing,preprocessor['age_median'],age)
    scaled=(filled-preprocessor['age_mean'])/preprocessor['age_scale']
    matrix=np.column_stack([scaled,missing.astype(float),preprocessor['encoder'].transform(x[CATEGORICAL])]).astype(np.float32)
    assert np.isfinite(matrix).all()
    return matrix

def build_model(kind,seed):
    if kind=='majority':
        return DummyClassifier(**DESIGN['models'][kind])
    if kind=='logistic':
        return LogisticRegression(**DESIGN['models'][kind],random_state=seed)
    return RandomForestClassifier(**DESIGN['models'][kind],random_state=seed,n_jobs=4)

def fit_or_load(path,preprocessor,matrix,y,weights,kind,seed,context,run):
    path=Path(path)
    metadata_path=path.with_suffix('.json')
    if path.exists():
        metadata=json.loads(metadata_path.read_text())
        assert metadata['fingerprint']==context['fingerprint']
        assert metadata['model_sha256']==file_hash(path)
        return joblib.load(path),metadata
    if not run:
        raise RuntimeError('No verified fit cache: '+path.name+'. Enable the appropriate run switch explicitly.')
    start=time.monotonic()
    model=build_model(kind,seed)
    with warnings.catch_warnings(record=True) as captured,threadpool_limits(limits=1):
        warnings.simplefilter('always')
        model.fit(matrix,y,sample_weight=weights*len(weights))
    warning_text=[str(w.message) for w in captured]
    metadata={'fingerprint':context['fingerprint'],'kind':kind,'fit_at_utc':timestamp(),
        'seconds':time.monotonic()-start,'training_respondents':len(y),'warnings':warning_text,
        'convergence_warning':any(issubclass(w.category,ConvergenceWarning) for w in captured)}
    bundle={'preprocessor':preprocessor,'model':model}
    temporary=path.with_suffix('.joblib.tmp')
    joblib.dump(bundle,temporary,compress=3)
    temporary.replace(path)
    metadata['model_sha256']=file_hash(path)
    json_write(metadata,metadata_path)
    return bundle,metadata

def probabilities(bundle,x,k):
    matrix=transform_predictors(x,bundle['preprocessor'])
    with threadpool_limits(limits=1):
        p=bundle['model'].predict_proba(matrix)
    assert np.array_equal(bundle['model'].classes_,np.arange(k))
    assert np.allclose(p.sum(axis=1),1)
    return p

def metrics(y,pred,weights,k,prob=None):
    cm=confusion_matrix(y,pred,labels=np.arange(k),sample_weight=weights)
    support=cm.sum(axis=1)
    recall=np.divide(np.diag(cm),support,out=np.zeros(k),where=support>0)
    precision=np.divide(np.diag(cm),cm.sum(axis=0),out=np.zeros(k),where=cm.sum(axis=0)>0)
    f1=np.divide(2*precision*recall,precision+recall,out=np.zeros(k),where=precision+recall>0)
    result={'balanced_accuracy':float(recall.mean()),'macro_f1':float(f1.mean()),
        'accuracy':float(np.trace(cm)/cm.sum())}
    if prob is not None:
        result['log_loss']=float(log_loss(y,prob,labels=np.arange(k),sample_weight=weights))
    profiles=pd.DataFrame({'cluster':np.arange(k),'precision':precision,'recall':recall,'f1':f1,
        'weighted_true_share':support/support.sum(),'weighted_predicted_share':cm.sum(axis=0)/cm.sum(),
        'respondents':[int((y==c).sum()) for c in range(k)]})
    return result,profiles,cm

def save_confusion(cm,out,model,kind,scope):
    labels=[f'{model}_C{c}' for c in range(len(cm))]
    row_normalised=np.divide(cm,cm.sum(axis=1,keepdims=True),out=np.zeros_like(cm),where=cm.sum(axis=1,keepdims=True)>0)
    pd.DataFrame(cm,index=labels,columns=labels).to_csv(out/f'{model}_{kind}_{scope}_confusion_joint.csv',index_label='true_profile')
    pd.DataFrame(row_normalised,index=labels,columns=labels).to_csv(out/f'{model}_{kind}_{scope}_confusion_recall.csv',index_label='true_profile')

def development_cv(frame,x,context,out,run=False):
    splitter=GroupKFold(n_splits=5,shuffle=True,random_state=DESIGN['seed'])
    folds=list(splitter.split(x,groups=frame.COUNTRY_ISO3))
    assignment=np.full(len(frame),-1,dtype=int)
    fold_rows=[]
    for fold,(train,validation) in enumerate(folds,1):
        train_c=set(frame.iloc[train].COUNTRY_ISO3)
        valid_c=set(frame.iloc[validation].COUNTRY_ISO3)
        assert not train_c&valid_c
        assignment[validation]=fold
        fold_rows.extend({'COUNTRY_ISO3':country,'validation_fold':fold} for country in sorted(valid_c))
    assert np.all(assignment>0)
    pd.DataFrame(fold_rows).to_csv(out/'development_country_folds.csv',index=False)
    all_metrics=[]
    pooled=[]
    profiles=[]
    warnings_and_times=[]
    for model,k in DESIGN['profile_targets'].items():
        y=frame[model+'_cluster'].to_numpy(int)
        for kind in DESIGN['models']:
            oof=np.full((len(frame),k),np.nan)
            for fold,(train,validation) in enumerate(folds,1):
                train_frame,valid_frame=frame.iloc[train],frame.iloc[validation]
                weights=country_weights(train_frame)
                prep=fit_preprocessor(x.iloc[train],weights)
                matrix=transform_predictors(x.iloc[train],prep)
                assert set(y[train])==set(range(k)) and set(y[validation])==set(range(k))
                path=out/f'{model}_{kind}_fold{fold}.joblib'
                print(f'{model} {kind}: development fold {fold}/5',flush=True)
                try:
                    bundle,info=fit_or_load(path,prep,matrix,y[train],weights,kind,
                        DESIGN['seed']+fold,context,run)
                except Exception as error:
                    json_write({'at_utc':timestamp(),'stage':'development_cv','model':model,
                        'kind':kind,'fold':fold,'error':repr(error)},out/f'failure_{model}_{kind}_fold{fold}.json')
                    raise
                warnings_and_times.append({'target':model,'classifier':kind,'fold':fold,**info})
                p=probabilities(bundle,x.iloc[validation],k)
                oof[validation]=p
                scores,_,_=metrics(y[validation],p.argmax(axis=1),country_weights(valid_frame),k,p)
                all_metrics.append({'target':model,'classifier':kind,'fold':fold,
                    'training_countries':train_frame.COUNTRY_ISO3.nunique(),
                    'validation_countries':valid_frame.COUNTRY_ISO3.nunique(),**scores})
            assert np.isfinite(oof).all()
            scores,per_profile,cm=metrics(y,oof.argmax(axis=1),country_weights(frame),k,oof)
            pooled.append({'target':model,'classifier':kind,**scores})
            profiles.append(per_profile.assign(target=model,classifier=kind,scope='development_oof'))
            save_confusion(cm,out,model,kind,'development_oof')
            predictions=frame[['WPID_RANDOM','COUNTRY_ISO3']].copy()
            predictions['true_profile']=y
            predictions['predicted_profile']=oof.argmax(axis=1)
            predictions['validation_fold']=assignment
            for c in range(k):
                predictions[f'probability_C{c}']=oof[:,c]
            predictions.to_parquet(out/f'{model}_{kind}_development_oof_predictions.parquet',index=False)
    fold_scores=pd.DataFrame(all_metrics)
    summary=fold_scores.groupby(['target','classifier'])[['balanced_accuracy','macro_f1','accuracy','log_loss']].agg(['mean','std'])
    summary.columns=['_'.join(c) for c in summary.columns]
    summary=summary.reset_index()
    summary.to_csv(out/'development_cv_summary.csv',index=False)
    fold_scores.to_csv(out/'development_fold_scores.csv',index=False)
    pd.DataFrame(pooled).to_csv(out/'development_pooled_oof_scores.csv',index=False)
    pd.concat(profiles).to_csv(out/'development_per_profile_scores.csv',index=False)
    pd.DataFrame(warnings_and_times).to_csv(out/'fit_warnings_and_times.csv',index=False)
    return summary,folds

def freeze_supervised(frame,x,summary,context,out,run=False):
    seal_path=out/'supervised_freeze_seal.json'
    preference={'logistic':0,'random_forest':1,'majority':2}
    selection={}
    for target in DESIGN['profile_targets']:
        candidates=summary.loc[summary.target.eq(target)].copy()
        candidates['preference']=candidates.classifier.map(preference)
        chosen=candidates.sort_values(['macro_f1_mean','preference'],ascending=[False,True]).iloc[0]
        selection[target]={'classifier':chosen.classifier,'development_macro_f1_mean':float(chosen.macro_f1_mean)}
    if seal_path.exists():
        seal=json.loads(seal_path.read_text())
        assert seal['fingerprint']==context['fingerprint'] and seal['selection']==selection
        for filename,digest in seal['model_hashes'].items():
            assert file_hash(out/filename)==digest
        return seal
    weights=country_weights(frame)
    prep=fit_preprocessor(x,weights)
    matrix=transform_predictors(x,prep)
    hashes={}
    for target,entry in selection.items():
        for kind in dict.fromkeys([entry['classifier'],'majority']):
            path=out/f'{target}_{kind}_final_development.joblib'
            bundle,metadata=fit_or_load(path,prep,matrix,frame[target+'_cluster'].to_numpy(int),
                weights,kind,DESIGN['seed'],context,run)
            if metadata['convergence_warning']:
                raise RuntimeError('Final logistic regression did not converge; no supervised seal created.')
            hashes[path.name]=file_hash(path)
    seal={'fingerprint':context['fingerprint'],'selection':selection,'model_hashes':hashes,
        'frozen_at_utc':timestamp(),'heldout_predictions_used_for_selection':False,
        'profile_context':context['frozen_cluster_context'],'settings':DESIGN}
    json_write(seal,seal_path)
    return seal

def block_permutation(frame,x,folds,seal,context,out,run=False):
    result_path=out/'development_block_permutation.csv'
    if result_path.exists():
        return pd.read_csv(result_path)
    if not run:
        raise RuntimeError('Permutation result cache missing; explicitly enable RUN_INTERPRETATION.')
    records=[]
    for target,k in DESIGN['profile_targets'].items():
        kind=seal['selection'][target]['classifier']
        for fold,(_,valid) in enumerate(folds,1):
            f=frame.iloc[valid].reset_index(drop=True)
            source=x.iloc[valid].reset_index(drop=True)
            y=f[target+'_cluster'].to_numpy(int)
            weights=country_weights(f)
            bundle=joblib.load(out/f'{target}_{kind}_fold{fold}.joblib')
            base_p=probabilities(bundle,source,k)
            base=metrics(y,base_p.argmax(axis=1),weights,k)[0]['macro_f1']
            for block,columns in FEATURE_BLOCKS.items():
                for repetition in range(3):
                    rng=np.random.default_rng(DESIGN['seed']+1000*fold+repetition)
                    shuffled=source.copy()
                    if block=='Country income':
                        countries=sorted(f.COUNTRY_ISO3.unique())
                        income=[source.loc[f.COUNTRY_ISO3.eq(c),'CountryIncomeLevel'].iloc[0] for c in countries]
                        mapping=dict(zip(countries,rng.permutation(income)))
                        shuffled['CountryIncomeLevel']=f.COUNTRY_ISO3.map(mapping)
                    else:
                        for positions in f.groupby('COUNTRY_ISO3',sort=True).indices.values():
                            shuffled.iloc[positions,shuffled.columns.get_indexer(columns)]=source.iloc[rng.permutation(positions)][columns].to_numpy()
                    p=probabilities(bundle,shuffled,k)
                    score=metrics(y,p.argmax(axis=1),weights,k)[0]['macro_f1']
                    records.append({'target':target,'classifier':kind,'fold':fold,'block':block,
                        'repetition':repetition+1,'base_macro_f1':base,'permuted_macro_f1':score,
                        'macro_f1_drop':base-score,
                        'scheme':'whole-country income reassignment' if block=='Country income' else 'joint block shuffle within country'})
            print(f'{target} interpretation: fold {fold}/5 completed',flush=True)
    result=pd.DataFrame(records)
    result.to_csv(result_path,index=False)
    summary=result.groupby(['target','classifier','block']).macro_f1_drop.agg(['mean','std']).reset_index()
    summary.to_csv(out/'development_block_permutation_summary.csv',index=False)
    return result

def heldout_test(root,context,out,seal,run=False):
    complete=out/'heldout_complete.json'
    if complete.exists():
        saved=json.loads(complete.read_text())
        assert saved['fingerprint']==context['fingerprint']
        assert saved['freeze_seal_sha256']==file_hash(out/'supervised_freeze_seal.json')
        return pd.read_csv(out/'heldout_scores.csv')
    if not run:
        raise RuntimeError('No supervised held-out cache. Enable RUN_HELDOUT only after the development seal exists.')
    access_time=timestamp()
    assert access_time>seal['frozen_at_utc']
    json_write({'first_access_utc':access_time,'selection_fixed':seal['selection'],
        'supervised_freeze_sha256':file_hash(out/'supervised_freeze_seal.json')},out/'heldout_first_access.json')
    frame,inclusion=load_cohort(root,context,'heldout_country')
    x=prepare_predictors(frame)
    inclusion.to_csv(out/'heldout_target_eligibility.csv',index=False)
    predictor_missingness(frame,x,'heldout').to_csv(out/'heldout_predictor_missingness.csv',index=False)
    all_scores=[]
    all_profiles=[]
    all_countries=[]
    intervals=[]
    for target,k in DESIGN['profile_targets'].items():
        y=frame[target+'_cluster'].to_numpy(int)
        selected=seal['selection'][target]['classifier']
        for kind in dict.fromkeys(['majority',selected]):
            path=out/f'{target}_{kind}_final_development.joblib'
            assert file_hash(path)==seal['model_hashes'][path.name]
            bundle=joblib.load(path)
            p=probabilities(bundle,x,k)
            pred=p.argmax(axis=1)
            score,profiles,cm=metrics(y,pred,country_weights(frame),k,p)
            all_scores.append({'target':target,'classifier':kind,'selected':kind==selected,**score})
            all_profiles.append(profiles.assign(target=target,classifier=kind,scope='heldout'))
            save_confusion(cm,out,target,kind,'heldout')
            predictions=frame[['WPID_RANDOM','COUNTRY_ISO3']].copy()
            predictions['true_profile']=y
            predictions['predicted_profile']=pred
            for c in range(k):
                predictions[f'probability_C{c}']=p[:,c]
            predictions.to_parquet(out/f'{target}_{kind}_heldout_predictions.parquet',index=False)
            country_confusions=[]
            for country,indices in frame.groupby('COUNTRY_ISO3',sort=True).indices.items():
                w=country_weights(frame.iloc[indices])
                country_score,_,country_cm=metrics(y[indices],pred[indices],w,k,p[indices])
                present=country_cm.sum(axis=1)>0
                recall=np.divide(np.diag(country_cm),country_cm.sum(axis=1),out=np.zeros(k),where=present)
                all_countries.append({'target':target,'classifier':kind,'COUNTRY_ISO3':country,
                    'respondents':len(indices),'true_profiles_present':int(present.sum()),
                    'accuracy':country_score['accuracy'],'balanced_accuracy_present_profiles':float(recall[present].mean())})
                country_confusions.append(country_cm)
            rng=np.random.default_rng(DESIGN['seed'])
            matrices=np.array(country_confusions)
            draw_scores=[]
            for _ in range(1000):
                sampled=matrices[rng.integers(0,len(matrices),size=len(matrices))].mean(axis=0)
                support=sampled.sum(axis=1)
                recall=np.divide(np.diag(sampled),support,out=np.zeros(k),where=support>0)
                precision=np.divide(np.diag(sampled),sampled.sum(axis=0),out=np.zeros(k),where=sampled.sum(axis=0)>0)
                f1=np.divide(2*precision*recall,precision+recall,out=np.zeros(k),where=precision+recall>0)
                draw_scores.append([recall.mean(),f1.mean(),np.trace(sampled)/sampled.sum()])
            for column,metric in enumerate(['balanced_accuracy','macro_f1','accuracy']):
                values=np.array(draw_scores)[:,column]
                intervals.append({'target':target,'classifier':kind,'metric':metric,
                    'estimate':score[metric],'p025':float(np.quantile(values,.025)),
                    'p975':float(np.quantile(values,.975)),'country_draws':1000,'models_fixed':True})
    result=pd.DataFrame(all_scores)
    result.to_csv(out/'heldout_scores.csv',index=False)
    pd.concat(all_profiles).to_csv(out/'heldout_per_profile_scores.csv',index=False)
    pd.DataFrame(all_countries).to_csv(out/'heldout_country_scores.csv',index=False)
    pd.DataFrame(intervals).to_csv(out/'heldout_country_bootstrap_intervals.csv',index=False)
    json_write({'fingerprint':context['fingerprint'],'completed_at_utc':timestamp(),
        'first_access_utc':access_time,'freeze_seal_sha256':file_hash(out/'supervised_freeze_seal.json'),
        'profile_refits':False,'retuned_after_heldout':False},complete)
    return result

def make_figures(out):
    import matplotlib.pyplot as plt
    figures=out/'figures'
    figures.mkdir(exist_ok=True)
    cv=pd.read_csv(out/'development_cv_summary.csv')
    fig,axes=plt.subplots(1,len(DESIGN['profile_targets']),figsize=(7,4),constrained_layout=True)
    axes=np.atleast_1d(axes)
    for ax,(target,k) in zip(axes,DESIGN['profile_targets'].items()):
        rows=cv.loc[cv.target.eq(target)].set_index('classifier').loc[list(DESIGN['models'])]
        positions=np.arange(3)
        ax.bar(positions,rows.macro_f1_mean,color=['#a5a5a5','#39789c','#6b9b77'])
        ax.errorbar(positions,rows.macro_f1_mean,yerr=rows.macro_f1_std,fmt='none',color='black',capsize=3)
        ax.set_xticks(positions,['Majority','Logistic','Random forest'])
        ax.set_ylabel('Equal-country-weighted macro-F1')
        ax.set_ylim(0,1)
        ax.set_title(f'{target}: {k} frozen profiles')
        for i,value in enumerate(rows.macro_f1_mean):ax.text(i,value+.025,f'{value:.3f}',ha='center')
    fig.suptitle('Development-only country-grouped cross-validation\nError bars are fold SD, not confidence intervals',fontsize=11)
    fig.savefig(figures/'development_classifier_comparison.png',dpi=180)
    plt.close(fig)
    seal=json.loads((out/'supervised_freeze_seal.json').read_text())
    for target,k in DESIGN['profile_targets'].items():
        kind=seal['selection'][target]['classifier']
        cm=pd.read_csv(out/f'{target}_{kind}_heldout_confusion_recall.csv',index_col=0)
        fig,ax=plt.subplots(figsize=(max(5,k*.75),max(4,k*.65)),constrained_layout=True)
        image=ax.imshow(cm,cmap='Blues',vmin=0,vmax=1)
        ax.set_xticks(range(k),cm.columns,rotation=45,ha='right')
        ax.set_yticks(range(k),cm.index)
        ax.set_xlabel('Predicted frozen profile')
        ax.set_ylabel('True frozen profile')
        ax.set_title(f'{target}: held-out recall pattern ({kind})')
        for i in range(k):
            for j in range(k):
                value=cm.iloc[i,j]
                ax.text(j,i,f'{value:.2f}',ha='center',va='center',color='white' if value>.5 else 'black',fontsize=9)
        fig.colorbar(image,ax=ax,label='Within-true-profile weighted fraction')
        fig.savefig(figures/f'{target}_heldout_confusion.png',dpi=180)
        plt.close(fig)
    importance_path=out/'development_block_permutation_summary.csv'
    if importance_path.exists():
        importance=pd.read_csv(importance_path)
        fig,axes=plt.subplots(1,len(DESIGN['profile_targets']),figsize=(8,4),constrained_layout=True)
        axes=np.atleast_1d(axes)
        for ax,target in zip(axes,DESIGN['profile_targets']):
            rows=importance.loc[importance.target.eq(target)].sort_values('mean')
            ax.barh(rows.block,rows['mean'],color='#39789c')
            ax.axvline(0,color='black',linewidth=.7)
            ax.set_xlabel('Development macro-F1 drop after block permutation')
            ax.set_title(target)
        fig.savefig(figures/'development_predictor_block_importance.png',dpi=180)
        plt.close(fig)
    return figures

