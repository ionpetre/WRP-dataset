import sys
import unittest
import numpy as np
import pandas as pd
import local_resolution as a
from test_week05 import frame

class ResolutionTests(unittest.TestCase):
    def test_selection_does_not_use_global_ari(self):
        reference=[];profiles=[]
        for name in a.SPECIFICATIONS:
            for k in range(2,11):
                reference.append({'region':1,'candidate':name,'k':k,'status':'ok',
                    'inertia':1/k,'largest_share':1/k,'dominance':1,
                    'ari_unweighted':0.99 if k==9 else 0})
                for cluster in range(k):
                    for feature in a.FEATURES:
                        cats=[0,1,2] if feature in a.WORRY else [0,1]
                        prob=np.ones(len(cats))/len(cats)
                        prob=np.roll(prob,cluster%len(cats))
                        for category,p in zip(cats,prob):
                            profiles.append({'region':1,'candidate':name,'k':k,'cluster':cluster,
                                'feature':feature,'category':category,'proportion':p,'cluster_share':1/k})
        ref=pd.DataFrame(reference);p=pd.DataFrame(profiles)
        first,_=a.select_local_resolutions(ref,p)
        ref['ari_unweighted']=np.linspace(0,1,len(ref))[::-1]
        second,_=a.select_local_resolutions(ref,p)
        pd.testing.assert_frame_equal(first,second)
        self.assertTrue(first.global_agreement_used.eq(False).all())
        self.assertTrue(first.groupby(['region','candidate']).size().le(3).all())
        self.assertTrue(set(first.k).issuperset({2,3}))

    def test_reference_matching_jaccard_formula(self):
        weights=np.ones(6)/6
        ref=np.array([0,0,0,1,1,1]);pred=1-ref
        overlap=np.bincount(ref*2+pred,weights=weights,minlength=4).reshape(2,2)
        rr,cc=a.linear_sum_assignment(-overlap)
        scores=[overlap[r,c]/(overlap[r,:].sum()+overlap[:,c].sum()-overlap[r,c]) for r,c in zip(rr,cc)]
        np.testing.assert_allclose(scores,1)

if __name__=='__main__':unittest.main(verbosity=2)
