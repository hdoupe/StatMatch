"""
Script to run each phase of the matching process
"""

from adj_filst import adjfilst
import cpsmar
from cps_rets import Returns
from soi_rets import create_soi
from phase1 import phaseone
from phase2 import phasetwo
import pandas as pd

# Create original CPS file
mar_cps = cpsmar.create_cps('asec2014_pubuse_tax_fix_5x8.dat')
print 'CPS Created'
rets = Returns(mar_cps)
cps = rets.computation()
print 'CPS Tax Units Created'
filers, nonfilers = adjfilst(cps)
print 'Adjustment Complete'
puf = pd.read_csv('puf2009.csv')
soi = create_soi(puf)
print 'PUF Created'
soi_final, cps_final, counts = phaseone(cps, soi)
print 'Start Phase Two'
match = phasetwo(soi_final, cps_final)
