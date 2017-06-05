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
mar_cps = cpsmar.create_cps('asec2014_pubuse_tax_fix_5x8.dat')

# If you already have the CPS in CSV format, comment out the line above and
# uncomment the line bellow to skip creation from the DAT file and use the CSV

# mar_cps = pd.read_csv('cpsmar2014.csv')
print ('CPS Created')
rets = Returns(mar_cps)
cps = rets.computation()
print ('CPS Tax Units Created')
filers, nonfilers = adjfilst(cps)
print ('Adjustment Complete')
puf = pd.read_csv('puf2009.csv')
soi = create_soi(puf)
print ('PUF Created')
soi_final, cps_final, counts = phaseone(filers, soi)
print ('Start Phase Two')
match = phasetwo(soi_final[['cellid', 'soiseq', 'wt', 'factor', 'yhat']],
                 cps_final[['cellid', 'cpsseq', 'wt', 'factor', 'yhat']])
print ('Creating final file')
cpsrets = add_cps(filers, match, puf)
cps_matched = add_nonfiler(cpsrets, nonfilers)
# Rename variables for use in PUF data prep
renames = {'icps1': 'age_head',
           'icps2': 'age_spouse',
           'wasp': 'wage_head',
           'wass': 'wage_spouse'}
cps_matched = cps_matched.rename(columns=renames)
cps_matched.to_csv('cps-matched-puf.csv')
