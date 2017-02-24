"""
Create tax units from the processed CPS data
Input file: cpsmar2014.csv
"""

from collections import OrderedDict
import pandas as pd
import numpy as np


class Returns(object):
    """
    Class used to create tax units from the CPS file
    """
    def __init__(self, cps):
        """

        Parameters
        ----------
        cps: CPS file used
        """
        # Set CPS file and the household numbers in that file
        self.cps = cps
        self.h_nums = np.unique(self.cps['h_seq'].values)
        self.nunits = 0

        # Set filing thresholds. Currently for 2014
        self.single = 10150
        self.single65 = 11700
        self.hoh = 13050
        self.hoh65 = 14600
        self.joint = 20300
        self.joint65one = 21500
        self.joint65both = 22700
        self.widow = 16350
        self.widow65 = 17550
        self.depTotal = 1000
        # TODO: check and make sure all filing thresholds are correct

        # Set dependent exemptions
        self.depExempt = 3950

        # Lists to hold tax units in each household and over all
        self.house_units = list()
        self.tax_units = list()

        # Start the tax unit creation process
        self.computation()
        for num in self.h_nums:
            # Extract the household
            household = cps[cps['h_seq'] == num]
            f_nums = np.unique(household['a_famnum'])
            for fam in f_nums:
                # Extract each family in the household
                self.family = household[household['a_famnum'] == fam]
                self.family = self.family.to_dict('records')
                # If it is a single person household

    def computation(self):
        """
        Construct tax units based on type of household:
        1. Single persons living alone
        2. Persons living in group quarters
        3. All other family structures

        Returns
        -------
        None

        """
        # Extract each household from full CPS file
        for num in self.h_nums:
            self.nunits = 0
            del self.house_units[:]
            household = self.cps[self.cps['h_seq'] == num]
            f_nums = np.unique(household['a_famnum'].values)
            # Extract each family from the household
            for fam in f_nums:
                self.family = household[household['a_famnum'] == fam]
                self.family = self.family.to_dict('records')
                # Single person living alone
                if (self.family[0]['h_type'] == 6 or
                        self.family[0]['h_type'] == 7 and
                        self.family[0]['h_numper'] == 1):
                    self.house_units.append(self.create(self.family[0]))
                # Persons living in group quarters
                elif self.family[0]['h_type'] == 9:
                    for person in self.family:
                        self.house_units.append(self.create(person))
                # All other households
                else:
                    # First set relation flags
                    for person in self.family:
                        # Tax unit head flag
                        person['h_flag'] = False
                        # Tax unit spouse flag
                        person['s_flag'] = False
                        # Tan unit dependent flag
                        person['d_flag'] = False
                    # Loop through family again to process
                    for person in self.family:
                        # Only call create method if they aren't flagged
                        if (not person['h_flag'] and not person['s_flag'] and
                                not person['d_flag']):
                            self.house_units.append(self.create(person))
                        if not person['s_flag'] and person['d_flag']:
                            if self.must_file(person):
                                self.house_units.append(self.create(person))
                        # If there is more than one tax unit in a household,
                        # search for dependencies among the household
                        if self.nunits > 1:
                            self.tax_units_search()
            # Check head of household status for each unit in the household
            [self.hhstatus(unit) for unit in self.house_units]
            '''
            Might be able to replace loop with map function:
            map(self.hhstatus(), self.house_units)
            '''
            # Add each unit to the combined unit list
            for unit in self.house_units:
                self.tax_units.append(unit)

    def create(self, record):
        """
        Create a CPS tax unit
        Parameters
        ----------
        record: Records for person in the household

        Returns
        -------
        A tax unit

        """
        unit = OrderedDict()
        self.nunits += 1

    def hhstatus(self, unit):
        """
        Determine head of household status
        Returns
        -------
        unit: Tax unit

        """

    def must_file(self, record):
        """
        Check if a dependent must file
        Parameters
        ----------
        record

        Returns
        -------
        True if person must file, False otherwise

        """

    def tax_units_search(self):
        """
        Analogous to SEARCH2 macro in SAS files.
        Searches among the tax units in a household to see if there are any
        dependencies
        Returns
        -------

        """



# Read in data
cps_recs = pd.read_csv('cpsmar2014.csv')
# Obtain the household sequence numbers
test = Returns(cps_recs)
