"""
Create a composite extract from the SOI 2009 Public Use File
Input file: puf2009.sas7bdat
Output file: SOIRETS2009.csv
"""
# import pandas as pd
import numpy as np


def create_soi(SOI):
    # SOI = pd.read_sas('puf2009.sas7bdat')
    SOI = SOI[SOI['recid'] != 999999]

    SOI['filer'] = 1
    SOI['dmfs'] = 1
    SOI.loc[((SOI['mars'] == 3) | (SOI['mars'] == 6), 'dmfs')] = 0.5
    SOI['js'] = 2
    SOI.loc[(SOI['mars'] == 1, 'js')] = 1
    SOI.loc[(SOI['mars'] == 4, 'js')] = 3
    SOI['depne'] = SOI['xocah'] + SOI['xocawh'] + SOI['xoodep'] + SOI['xopar']
    SOI['agep'] = np.nan
    SOI['ages'] = np.nan
    SOI['agede'] = 0
    SOI.loc[(SOI['e02400'] > 0, 'agede')] = 1
    SOI['wasp'] = np.nan
    SOI['wass'] = np.nan
    SOI['ssincp'] = np.nan
    SOI['ssincs'] = np.nan
    SOI['returns'] = 1
    SOI['oldest'] = np.nan
    SOI['youngest'] = np.nan
    SOI['agepsqr'] = np.nan

    adjust = (SOI['e03150'] + SOI['e03210'] + SOI['e03220'] + SOI['e03230'] +
              SOI['e03260'] + SOI['e03270'] + SOI['e03240'] + SOI['e03290'] +
              SOI['e03300'] + SOI['e03400'] + SOI['e03500'])
    SOI['totincx'] = SOI['e00100'] + adjust

    SOI.rename(columns={'recid': 'retid', 'xocah': 'cahe', 'xocawh': 'cafhe',
                        'xoodep': 'othdep', 'dsi': 'ifdept',
                        'agedp1': 'agedep1', 'agedp2': 'agedep2',
                        'agedp3': 'agedep3', 'xopar': 'parents',
                        'e00200': 'was', 'e00300': 'intst', 'e00400': 'texint',
                        'e00600': 'dbe', 'e00800': 'alimony', 'e00900': 'bil',
                        'e01500': 'pensions', 'e01700': 'ptpen',
                        'e02100': 'fil', 'e02300': 'ucagix', 'e02400': 'ssinc',
                        'e02500': 'ssagix', 'e00100': 'agix',
                        'e04800': 'tincx'},
               inplace=True)

    # I wanted to include 'e02000' in SOI.rename list. But somehow the column
    # is series before renaming, and DataFrame afterwards.
    SOI['sche'] = SOI['e02000']

    SOI['xifdept'] = SOI['ifdept']
    SOI['xdepne'] = SOI['depne']
    SOI['xagede'] = SOI['agede']
    SOI['income'] = SOI['totincx']

    wt = SOI['s006'] / 100
    SOI['wt'] = wt * 1.03  # TODO: check the number

    SOI['sequence'] = SOI.index + 1
    SOI['soiseq'] = SOI.index + 1

    columns_to_keep = ['js', 'agedep1', 'agedep2', 'agedep3', 'parents',
                       'ifdept', 'cahe', 'cafhe', 'othdep', 'depne', 'agep',
                       'ages', 'agede', 'was', 'wasp', 'wass', 'intst',
                       'texint', 'dbe', 'alimony', 'bil', 'pensions', 'ptpen',
                       'sche', 'fil', 'ucagix', 'ssinc', 'ssincp', 'ssincs',
                       'ssagix', 'totincx', 'agix', 'tincx', 'returns',
                       'oldest', 'youngest', 'agepsqr', 'xagede', 'xifdept',
                       'xdepne', 'income', 'retid', 'sequence', 'soiseq',
                       'wt', 'filer']

    SOI = SOI[columns_to_keep]
    # SOI.to_csv('soirets2009.csv', index=False)
    return SOI
