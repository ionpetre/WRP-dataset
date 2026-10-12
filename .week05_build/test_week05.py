import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd

path = Path(__file__).with_name('week05_core.py')
import sys
module_spec = importlib.util.spec_from_file_location('week05_core', path)
w = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = w
module_spec.loader.exec_module(w)

def frame(countries=6, per_country=25):
    rng = np.random.default_rng(123)
    n = countries * per_country
    result = pd.DataFrame({'WPID_RANDOM': np.arange(n),
        'COUNTRY_ISO3': np.repeat([f'C{i:02d}' for i in range(countries)], per_country),
        'WGT': rng.uniform(.5, 2, n)})
    for col in w.WORRY:
        result[col] = rng.integers(0, 3, n)
    for col in w.PERSONAL + w.KNOWN:
        result[col] = rng.integers(0, 2, n)
    return result

class ValidationTests(unittest.TestCase):
    def test_weights(self):
        df = frame()
        weights = w.country_weights(df)
        self.assertAlmostEqual(weights.sum(), 1)
        for country in df.COUNTRY_ISO3.unique():
            self.assertAlmostEqual(weights[df.COUNTRY_ISO3.eq(country)].sum(), 1/6)

    def test_geometry_matches_week04(self):
        df = frame()
        for spec in w.SPECIFICATIONS.values():
            transformed = w.transform(df, spec)
            worry = np.where(df[w.WORRY].to_numpy() == 2, spec.top, df[w.WORRY]) / spec.top
            mean = worry.mean(axis=1, keepdims=True)
            expected = np.column_stack([(worry-mean)*np.sqrt(spec.alpha)/np.sqrt(6),
                mean*np.sqrt(spec.alpha)/np.sqrt(6),
                df[w.PERSONAL+w.KNOWN].to_numpy()*np.sqrt((1-spec.alpha)/2)/np.sqrt(7)])
            np.testing.assert_allclose(transformed, expected, atol=1e-15)
            np.testing.assert_allclose(transformed[:, :6].sum(axis=1), 0, atol=1e-15)
        df.loc[0, w.WORRY[0]] = np.nan
        with self.assertRaises(ValueError):
            w.transform(df, w.SPECIFICATIONS['B'])

    def test_overlap_permutation_and_many_to_one(self):
        weights = np.ones(6)/6
        a = np.array([0,0,1,1,2,2])
        b = np.array([2,2,0,0,1,1])
        stats, table = w.compare_partitions(a,b,weights)
        self.assertAlmostEqual(stats['ari_unweighted'], 1)
        self.assertAlmostEqual(stats['one_to_one_matched_share'], 1)
        self.assertAlmostEqual(table.joint_share.sum(), 1)
        merged = np.array([0,0,0,0,1,1])
        stats, _ = w.compare_partitions(a,merged,weights)
        self.assertAlmostEqual(stats['local_to_global_purity'], 1)
        self.assertLess(stats['global_to_local_purity'], 1)

    def test_small_region_plans(self):
        plans, audit, info = w.make_regional_plans(frame(1), 6, w.REGIONAL_DESIGN)
        self.assertEqual(plans['countries'], [])
        self.assertFalse(info['country_stability_claim_available'])
        plans, audit, info = w.make_regional_plans(frame(3), 4, w.REGIONAL_DESIGN)
        self.assertEqual(len(plans['countries']), 3)
        self.assertTrue(audit.omitted_count.eq(1).all())
        self.assertEqual(info['country_diagnostic'], 'leave_one_country_out')
        plans, audit, info = w.make_regional_plans(frame(15), 5, w.REGIONAL_DESIGN)
        keys = [tuple(idx) for idx in plans['countries']]
        self.assertEqual(len(keys), 50)
        self.assertEqual(info['distinct_country_fits'],len(set(keys)))
        for rows in plans['countries']:
            self.assertEqual(frame(15).iloc[rows].COUNTRY_ISO3.nunique(), 12)
        again, _, _ = w.make_regional_plans(frame(15), 5, w.REGIONAL_DESIGN)
        for a, b in zip(plans['respondents'], again['respondents']):
            np.testing.assert_array_equal(a,b)
        plans,audit,info=w.make_regional_plans(frame(6),10,w.REGIONAL_DESIGN)
        self.assertEqual(len(plans['countries']),50)
        self.assertEqual(info['possible_80pct_subsets'],15)
        for rows in plans['countries']:
            self.assertEqual(frame(6).iloc[rows].COUNTRY_ISO3.nunique(),4)

    def test_structure_local_two_groups(self):
        result = w.structure(np.array([0,0,1,1]), np.ones(4)/4)
        self.assertFalse(result['global_benchmark_pass'])
        self.assertEqual(result['coverage'], 1)

    def test_fitting_cache_and_failures(self):
        df = frame()
        with tempfile.TemporaryDirectory() as folder:
            a = w.cached_kmeans(df,w.SPECIFICATIONS['B'],4,np.arange(len(df)),12,folder,'test','first')
            self.assertEqual(a['status'],'ok')
            b = w.cached_kmeans(df,w.SPECIFICATIONS['B'],4,np.arange(len(df)),12,folder,'test','first')
            np.testing.assert_array_equal(a['labels'],b['labels'])
            self.assertEqual(len(list(Path(folder).glob('*.joblib'))),1)
            c = w.cached_kmeans(df,w.SPECIFICATIONS['B'],200,np.arange(len(df)),12,folder,'test','fail')
            self.assertEqual(c['status'],'failed')
            summary, _, _ = w.pairwise_stability([a,b,c], a['labels'])
            self.assertEqual(summary['failed_fits'],1)
            self.assertEqual(summary['pairwise_count'],1)

    def test_original_units(self):
        df = frame(2)
        labels = np.arange(len(df))%2
        profile = w.original_profiles(df,labels,w.country_weights(df))
        np.testing.assert_allclose(profile.groupby(['cluster','feature']).proportion.sum(),1)

    def test_weighted_quantile(self):
        self.assertEqual(w.weighted_quantile(np.array([2,1,3]),np.array([1,8,1]),.5),1)
        self.assertEqual(w.weighted_quantile(np.array([2,1,3]),np.array([1,8,1]),.95),3)

if __name__ == '__main__':
    unittest.main(verbosity=2)
