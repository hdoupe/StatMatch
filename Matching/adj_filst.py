"""
Create tax units from the processed CPS data
Input file: CPSRETS2014.csv
"""

import pandas as pd
import numpy as np


cps_recs = pd.read_csv('CPSRETS2014.csv')
case1 = (cps_recs['filst'] == 0) & (cps_recs['was'] > 0)
case2 = (cps_recs['filst'] == 0) & (cps_recs['was'] <= 0)
cps_recs['case1'] = np.nan
cps_recs['case1'][case1] = 1
cps_recs['case2'] = np.nan
cps_recs['case2'][case2] = 1
np.random.seed(142)
cps_recs['z1'] = cps_recs['case1'].apply(lambda x: np.random.uniform(0, 1)
                                         if x == 1 else x)
np.random.seed(1)
cps_recs['z2'] = cps_recs['case2'].apply(lambda x: np.random.uniform(0, 1)
                                         if x == 1 else x)
# TODO: check the probability
selected = (cps_recs['z1'] <= 0.84) | (cps_recs['z2'] <= 0.54)
cps_recs['filst'][selected] = 1
cps_recs.drop(['case1', 'case2'], axis=1, inplace=True)

filers = cps_recs.copy()[(cps_recs['filst'] == 1)]
nonfilers = cps_recs.copy()[(cps_recs['filst'] == 0)]

filers.to_csv('cpsrets14.csv', index=False)
nonfilers.to_csv('cpsnonf2014.csv', index=False)
