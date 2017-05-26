import pandas as pd
import numpy as np

from scipy.stats import ttest_ind, bartlett

prod = pd.read_csv('PROD2009_V2.CSV')
test = pd.read_csv('cps-matched-puf.csv')

print ('Prod')
print ('N:',len(prod))
print ('N filed:',len(prod[prod['filer'] == 1]))

print ('Test')
print ('N:',len(test))
print ('N filed:',len(test[test['filer'] == 1]))

columns = list(set(list(test.columns)).intersection(list(prod.columns)))

results = {'variable':[], 'mean_production':[], 'mean_test' : [], 'mean_diff': [], \
	'studentt_pvalue':[], 'stddev_production': [], 'stddev_test': [], 'stddev_diff': [],\
	'bartlett_pvalue': []}

for c in columns:	
	results['variable'].append(c)
	
	results['mean_production'].append(np.mean(prod[c]))
	results['mean_test'].append(np.mean(test[c]))
	results['mean_diff'].append( abs(np.mean(prod[c]) - np.mean(test[c])) )
	results['studentt_pvalue'].append(ttest_ind(prod[c],test[c]).pvalue)
	
	results['stddev_production'].append(np.std(prod[c]))
	results['stddev_test'].append(np.std(test[c]))
	results['stddev_diff'].append( abs(np.std(prod[c]) - np.std(test[c])) )
	results['bartlett_pvalue'].append(bartlett(prod[c],test[c]).pvalue)
	
	
results = pd.DataFrame.from_dict(results)

results.to_csv('results.csv')

