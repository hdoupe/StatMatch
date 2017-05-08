"""
Script to run each phase of the matching process
"""

from adj_filst import adjfilst
import cpsmar
from cps_rets import Returns
from soi_rets import create_soi
import pandas as pd

# Create original CPS file
mar_cps = cpsmar.create_cps()
print 'CPS Created'
rets = Returns(mar_cps)
cps = rets.computation()
print 'CPS Tax Units Created'
filers, nonfilers = adjfilst(cps)
print 'Adjustment Complete'
puf = pd.read_csv('puf2009.csv')
soi = create_soi(puf)
print 'PUF Created'
