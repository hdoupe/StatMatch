"""
Read in raw CPS data file and structure to be used in future scripts
"""
import pandas as pd
import numpy as np


def h_recs(rec):
    """
    Process each household record in the raw CPS file and

    Parameters
    ----------
    rec: Record from CPS file

    Returns
    -------
    DataFrame with the variables

    """
    record = pd.DataFrame()
    record['hrecord'] = [int(rec[0])]
    record['h_seq'] = [int(rec[1:6])]
    record['hhpos'] = [int(rec[6:8])]
    record['hunits'] = [int(rec[8])]
    record['hefaminc'] = [int(rec[9:11])]
    record['h_respnm'] = [int(rec[12:13])]
    record['h_year'] = [int(rec[13:17])]
    record['h_hhtype'] = [int(rec[19])]
    record['h_numper'] = [int(rec[20:22])]
    record['hnumfam'] = [int(rec[22:24])]
    record['h_type'] = [int(rec[24])]
    record['h_month'] = [int(rec[25:27])]
    record['h_mis'] = [int(rec[28])]
    record['h_hhnum'] = [int(rec[29])]

    return record
cps = [line.strip().split() for line in
       open('asec2014_pubuse_tax_fix_5x8.dat').readlines()]
print h_recs(cps[0][0])
recs_dict = {}
