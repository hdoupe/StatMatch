"""
Script to run each phase of the matching process
"""

from adj_filst import adjfilst
import cpsmar
from cps_rets import Returns
from soi_rets import create_soi
from phase1 import phaseone
from phase2 import phasetwo
from add_cps_vars import add_cps
from add_nonfilers import add_nonfiler
import pandas as pd

# Create original CPS file
mar_cps = cpsmar.create_cps('asec2014_pubuse_tax_fix_5x8_2017.dat')
print ('CPS Created')
rets = Returns(mar_cps)
cps = rets.computation() #pd.read_csv('CPSRETS2014.csv')
print ('CPS Tax Units Created')
filers, nonfilers = adjfilst(cps) #pd.read_csv('cpsrets14.csv'), pd.read_csv('cpsnonf2014.csv') 
print ('Adjustment Complete')
puf = pd.read_csv('puf2009.csv')
soi = create_soi(puf)
print ('PUF Created')
soi_final, cps_final, counts = phaseone(filers, soi)
print ('Start Phase Two')
match = phasetwo(soi_final, cps_final)
print ('Creating final file')
cpsrets = add_cps(filers, match, puf)

# nonfilers = pd.read_csv('cpsnonf2014.csv')
# cpsrets = pd.read_csv('cpsrets.csv')

cps_matched = add_nonfiler(cpsrets, nonfilers)
cps_matched.to_csv('cps-matched-puf.csv')
