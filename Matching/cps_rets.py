"""
Create tax units from the processed CPS data
Input file: cpsmar2014.csv
"""

from collections import OrderedDict
import pandas as pd
import numpy as np
from tqdm import tqdm


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
        self.depwages = 0
        self.depTotal = 1000
        # wage thresholds for non-dependent filers
        self.wage1 = 1000
        self.wage2 = 250
        self.wage2nk = 10000
        self.wage3 = 1

        # Set dependent exemptions
        self.depExempt = 3950

        # Lists to hold tax units in each household and over all
        self.house_units = list()
        self.tax_units = list()

        # Start the tax unit creation process
        # self.computation()

    def computation(self):
        """
        Construct tax units based on type of household:
        1. Single persons living alone
        2. Persons living in group quarters
        3. All other family structures

        Returns
        -------
        CPS Tax Units File

        """
        # Extract each household from full CPS file
        # Tax unit head flag
        self.cps['h_flag'] = False
        # Tax unit spouse flag
        self.cps['s_flag'] = False
        # Tax unit dependent flag
        self.cps['d_flag'] = False
        # flag
        self.cps['flag'] = False

        self.cps['alm_val'] = 0
        for index, row in self.cps.iterrows():
            if row['oi_off'] == 20:
                row['alm_val'] = row['oi_off']

        for num in tqdm(self.h_nums):
            try:
                self.nunits = 0
                del self.house_units[:]
                self.household = self.cps[self.cps['h_seq'] == num]
                self.household = self.household.sort_values('a_lineno')
                self.household = self.household.to_dict('records')

                # Single person living alone
                if ((self.household[0]['h_type'] == 6 or
                     self.household[0]['h_type'] == 7) and
                        (self.household[0]['h_numper'] == 1)):
                    self.house_units.append(self.create(self.household[0]))
                # Persons living in group quarters
                elif self.household[0]['h_type'] == 9:
                    for person in self.household:
                        self.house_units.append(self.create(person))
                # All other households
                else:
                    for person in self.household:
                        # Only call create method if they aren't flagged
                        if (not person['h_flag'] and not
                                person['s_flag'] and not
                                person['d_flag']):
                            self.house_units.append(self.create(person))
                        if not person['s_flag'] and person['d_flag']:
                            if self.must_file(person):
                                self.house_units.append(self.create(person))
                        # If there is more than one tax unit in a household,
                        # search for dependencies among the household
                        if self.nunits > 1:
                            self.tax_units_search()
            # for some individuals, a_spouse is not correct
            except IndexError:
                print "IndexError"
                continue

            # Check head of household status for each unit in the household
            [self.hhstatus(unit) for unit in self.house_units]
            '''
            Might be able to replace loop with map function:
            map(self.hhstatus(), self.house_units)
            '''
            # Add each unit to the combined unit list
            for unit in self.house_units:
                if not unit['t_flag']:
                    continue
                self.tax_units.append(self.output(unit))
        output = pd.DataFrame(self.tax_units)
        output.to_csv('CPSRETS2014.csv', index=False)
        return output

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
        # flag this person
        record['flag'] = True
        # income items
        was = record['wsal_val']
        wasp = was
        intst = record['int_val']
        dbe = record['div_val']

        alimony = record['alm_val']
        bil = record['semp_val']
        pensions = record['rtm_val']
        rents = record['rnt_val']
        fil = record['frse_val']
        ucomp = record['uc_val']
        socsec = record['ss_val']
        # weight & flags
        wt = record['fsup_wgt']
        ifdept = record['d_flag']  # Tax unit dependent flag
        record['h_flag'] = True   # Tax Unit Head Flag
        # CPS identifiers
        xhid = record['h_seq']
        xfid = record['ffpos']
        xpid = record['ph_seq']
        xstate = record['gestfips']
        xregion = record['gereg']
        # CPS evaluation criteria (head)
        zifdep = record['d_flag']   # Tax unit dependent flag
        zntdep = 0
        zhhinc = record['hhinc']
        zagept = record['a_age']
        zagesp = 0
        zoldes = 0
        zyoung = 0
        zworkc = record['wc_val']
        zsocse = record['ss_val']
        zssinc = record['ssi_val']
        zpubas = record['paw_val']
        zvetbe = record['vet_val']
        zchsup = 0
        zfinas = 0
        zdepin = 0
        zowner = 0
        zwaspt = record['wsal_val']
        zwassp = 0

        # home Ownership Flag
        if (self.nunits == 1) and (record['h_tenure'] == 1):
            zowner = 1

        # store dependents info
        for i in range(1, 17):
            record['dep' + str(i)] = np.nan
        for i in range(1, 17):
            record['depage' + str(i)] = np.nan

        # marital status
        ms = record['a_maritl']
        if ms == 1 or ms == 2 or ms == 3:
            ms_type = 2
        else:
            ms_type = 1
        sp_ptr = record['a_spouse']
        relcode = record['a_exprrp']
        # ftype = record['ftype']
        ageh = record['a_age']
        if ageh >= 65:
            agede = 1
        else:
            agede = 0
        depne = 0
        ages = np.nan
        wass = np.nan
        if ms_type == 1:
            js = 1
            ages = np.nan
            # Certain single & separated individuals living alone are allowed
            # to file as head of household.
            if ((record['h_type'] == 6 or
                 record['h_type'] == 7) and record['h_numper'] == 1):
                if ms == 6:
                    js = 3  # JS = 1 in SAS code
        else:
            js = 2
            if sp_ptr != 0:
                ages = self.household[sp_ptr - 1]['a_age']
                if ages >= 65:
                    agede += 1
                wass = self.household[sp_ptr - 1]['wsal_val']
                was += wass
                intst += self.household[sp_ptr - 1]['int_val']
                dbe += self.household[sp_ptr - 1]['div_val']
                alimony += self.household[sp_ptr - 1]['alm_val']
                bil += self.household[sp_ptr - 1]['semp_val']
                pensions += self.household[sp_ptr - 1]['rtm_val']
                rents += self.household[sp_ptr - 1]['rnt_val']
                fil += self.household[sp_ptr - 1]['frse_val']
                ucomp += self.household[sp_ptr - 1]['uc_val']
                socsec += self.household[sp_ptr - 1]['ss_val']
                # Tax unit spouse flag
                self.household[sp_ptr - 1]['s_flag'] = True

                # CPS Evaluation Criteria (spouse)
                zagesp = self.household[sp_ptr - 1]['a_age']
                zworkc += self.household[sp_ptr - 1]['wc_val']
                zsocse += self.household[sp_ptr - 1]['ss_val']
                zssinc += self.household[sp_ptr - 1]['ssi_val']
                zpubas += self.household[sp_ptr - 1]['paw_val']
                zvetbe += self.household[sp_ptr - 1]['vet_val']
                zchsup += 0
                zfinas += 0
                zwassp = self.household[sp_ptr - 1]['wsal_val']

        if intst > 400:
            xschb = 1
        else:
            xschb = 0
        if fil != 0:
            xschf = 1
        else:
            xschf = 0
        if rents != 0:
            xsche = 1
        else:
            xsche = 0
        if bil != 0:
            xschc = 1
        else:
            xschc = 0

        record['101'] = record['a_age']
        record['102'] = np.nan
        if sp_ptr != 0:
            record['102'] = self.household[sp_ptr - 1]['a_age']

        # health insurance coverage
        record['110'] = 0
        record['111'] = 0
        record['112'] = 0
        record['113'] = np.nan
        record['114'] = np.nan
        record['115'] = np.nan
        if sp_ptr != 0:
            record['113'] = 0
            record['114'] = 0
            record['115'] = 0

        # pension coverage
        record['116'] = 0
        record['117'] = 0
        record['118'] = np.nan
        record['119'] = np.nan
        if sp_ptr != 0:
            record['118'] = 0
            record['119'] = 0

        # health status
        record['120'] = 0
        record['121'] = np.nan
        if sp_ptr != 0:
            record['121'] = 0

        # miscellaneous income amounts
        record['122'] = record['ssi_val']  # SSI
        record['123'] = record['paw_val']  # public assistance (TANF)
        record['124'] = record['wc_val']  # workman's compensation
        record['125'] = record['vet_val']  # veteran's benefits
        record['126'] = 0  # child support
        record['127'] = record['dsab_val']  # disablility income
        record['128'] = record['ss_val']  # social security income
        record['129'] = zowner  # home ownership flag
        record['130'] = 0  # wage share
        if sp_ptr != 0:
            record['122'] += self.household[sp_ptr - 1]['ssi_val']
            record['123'] += self.household[sp_ptr - 1]['paw_val']
            record['124'] += self.household[sp_ptr - 1]['wc_val']
            record['125'] += self.household[sp_ptr - 1]['vet_val']
            record['126'] += 0
            record['127'] += self.household[sp_ptr - 1]['dsab_val']
            record['128'] += self.household[sp_ptr - 1]['ss_val']
            totalwas = (record['wsal_val'] +
                        self.household[sp_ptr - 1]['wsal_val'])
            if totalwas > 0:
                record['130'] = (min(record['wsal_val'],
                                     self.household[sp_ptr - 1]['wsal_val']) /
                                 float(totalwas))

        # energy assistance, food stamp, school lunch
        # only get put on the return of the primary taxpayer

        if self.nunits == 1:
            record['131'] = 0
            record['132'] = 0
            record['133'] = 0
        else:
            record['131'] = np.nan
            record['132'] = np.nan
            record['133'] = np.nan

        # additional health_related variables, etc:
        # medicare, medicade, champus and country of origin

        record['134'] = 0
        record['135'] = record['ljcw']
        record['136'] = record['wemind']
        record['137'] = record['penatvty']
        record['138'] = np.nan
        record['139'] = np.nan
        record['140'] = np.nan
        record['141'] = np.nan
        if sp_ptr != 0:
            record['138'] = 0
            record['139'] = self.household[sp_ptr - 1]['ljcw']
            record['140'] = self.household[sp_ptr - 1]['wemind']
            record['141'] = self.household[sp_ptr - 1]['penatvty']

        # (1)	EDUCATIONAL ATTAINMENT (HEAD AND SPOUSE)
        # (2)	GENDER (HEAD AND SPOUSE)
        record['142'] = record['a_hga']
        record['143'] = record['a_sex']
        record['144'] = np.nan
        record['145'] = np.nan
        if sp_ptr != 0:
            record['144'] = self.household[sp_ptr - 1]['a_hga']
            record['145'] = self.household[sp_ptr - 1]['a_sex']

        # self-employed industry - head and spouse
        classofworker = record['ljcw']
        majorindustry = 0
        senonfarm = 0
        sefarm = 0
        if classofworker == 6:
            senonfarm = record['semp_val']
            sefarm = record['frse_val']
            majorindustry = record['wemind']
        if sp_ptr != 0:
            classofworker = self.household[sp_ptr - 1]['ljcw']
            if classofworker == 6:
                senonfarm_sp = self.household[sp_ptr - 1]['semp_val']
                sefarm_sp = self.household[sp_ptr - 1]['frse_val']
                if abs(senonfarm_sp) > abs(senonfarm):
                    majorindustry = self.household[sp_ptr - 1]['wemind']
                    senonfarm += senonfarm_sp
                    sefarm += sefarm_sp

        record['146'] = majorindustry
        record['147'] = senonfarm
        record['148'] = sefarm

        record['151'] = record['a_age']
        record['152'] = record['care']
        record['153'] = record['caid']
        record['154'] = record['oth']
        record['155'] = record['hi']
        record['156'] = record['priv']
        record['157'] = record['paid']
        record['158'] = record['filestat']
        record['159'] = record['agi']
        record['160'] = 0  # capital gains no longer on file
        record['161'] = np.nan
        record['162'] = np.nan
        record['163'] = np.nan
        record['164'] = np.nan
        record['165'] = np.nan
        record['166'] = np.nan
        record['167'] = np.nan
        record['168'] = np.nan
        record['169'] = np.nan
        record['170'] = np.nan
        if sp_ptr != 0:
            record['161'] = self.household[sp_ptr - 1]['a_age']
            record['162'] = self.household[sp_ptr - 1]['care']
            record['163'] = self.household[sp_ptr - 1]['caid']
            record['164'] = self.household[sp_ptr - 1]['oth']
            record['165'] = self.household[sp_ptr - 1]['hi']
            record['166'] = self.household[sp_ptr - 1]['priv']
            record['167'] = self.household[sp_ptr - 1]['paid']
            record['168'] = self.household[sp_ptr - 1]['filestat']
            record['169'] = self.household[sp_ptr - 1]['agi']
            record['170'] = 0

        record['171'] = record['wsal_val']
        record['172'] = record['int_val']
        record['173'] = record['div_val']
        record['174'] = record['alm_val']
        record['175'] = record['semp_val']
        record['176'] = record['rtm_val']
        record['177'] = record['rnt_val']
        record['178'] = record['frse_val']
        record['179'] = record['uc_val']
        record['180'] = record['ss_val']  # capital gains no longer on file
        record['181'] = np.nan
        record['182'] = np.nan
        record['183'] = np.nan
        record['184'] = np.nan
        record['185'] = np.nan
        record['186'] = np.nan
        record['187'] = np.nan
        record['188'] = np.nan
        record['189'] = np.nan
        record['190'] = np.nan
        if sp_ptr != 0:
            record['181'] = self.household[sp_ptr - 1]['wsal_val']
            record['182'] = self.household[sp_ptr - 1]['int_val']
            record['183'] = self.household[sp_ptr - 1]['div_val']
            record['184'] = self.household[sp_ptr - 1]['alm_val']
            record['185'] = self.household[sp_ptr - 1]['semp_val']
            record['186'] = self.household[sp_ptr - 1]['rtm_val']
            record['187'] = self.household[sp_ptr - 1]['rnt_val']
            record['188'] = self.household[sp_ptr - 1]['frse_val']
            record['189'] = self.household[sp_ptr - 1]['uc_val']
            record['190'] = self.household[sp_ptr - 1]['ss_val']

        # retirement income
        record['191'] = record['ret_val1']
        record['192'] = record['ret_sc1']
        record['193'] = record['ret_val2']
        record['194'] = record['ret_sc2']
        record['195'] = np.nan
        record['196'] = np.nan
        record['197'] = np.nan
        record['198'] = np.nan

        if sp_ptr != 0:
            record['195'] = self.household[sp_ptr - 1]['ret_val1']
            record['196'] = self.household[sp_ptr - 1]['ret_sc1']
            record['197'] = self.household[sp_ptr - 1]['ret_val2']
            record['198'] = self.household[sp_ptr - 1]['ret_sc2']

        # disability income

        record['199'] = record['dis_val1']
        record['200'] = record['dis_sc1']
        record['201'] = record['dis_val2']
        record['202'] = record['dis_sc2']
        record['203'] = np.nan
        record['204'] = np.nan
        record['205'] = np.nan
        record['206'] = np.nan
        if sp_ptr != 0:
            record['203'] = self.household[sp_ptr - 1]['dis_val1']
            record['204'] = self.household[sp_ptr - 1]['dis_sc1']
            record['205'] = self.household[sp_ptr - 1]['dis_val2']
            record['206'] = self.household[sp_ptr - 1]['dis_sc2']

        # survivor income

        record['207'] = record['sur_val1']
        record['208'] = record['sur_sc1']
        record['209'] = record['sur_val2']
        record['210'] = record['sur_sc2']
        record['211'] = np.nan
        record['212'] = np.nan
        record['213'] = np.nan
        record['214'] = np.nan

        if sp_ptr != 0:
            record['211'] = self.household[sp_ptr - 1]['sur_val1']
            record['212'] = self.household[sp_ptr - 1]['sur_sc1']
            record['213'] = self.household[sp_ptr - 1]['sur_val2']
            record['214'] = self.household[sp_ptr - 1]['sur_sc2']

            # veterans income

        record['215'] = record['vet_typ1']
        record['216'] = record['vet_typ2']
        record['217'] = record['vet_typ3']
        record['218'] = record['vet_typ4']
        record['219'] = record['vet_typ5']
        record['220'] = record['vet_val']
        record['221'] = np.nan
        record['222'] = np.nan
        record['223'] = np.nan
        record['224'] = np.nan
        record['225'] = np.nan
        record['226'] = np.nan
        if sp_ptr != 0:
            record['221'] = self.household[sp_ptr - 1]['vet_typ1']
            record['222'] = self.household[sp_ptr - 1]['vet_typ2']
            record['223'] = self.household[sp_ptr - 1]['vet_typ3']
            record['224'] = self.household[sp_ptr - 1]['vet_typ4']
            record['225'] = self.household[sp_ptr - 1]['vet_typ5']
            record['226'] = self.household[sp_ptr - 1]['vet_val']

        record['227'] = sp_ptr

        # household

        record['228'] = record['fhip_val']
        record['229'] = record['fmoop']
        record['230'] = record['fotc_val']
        record['231'] = record['fmed_val']
        record['232'] = record['hmcaid']
        record['233'] = record['hrwicyn']
        record['234'] = record['hfdval']
        record['235'] = record['care_val']

        # taxpayer
        record['236'] = record['paw_val']
        record['237'] = record['mcaid']
        record['238'] = record['pchip']
        record['239'] = record['wicyn']
        record['240'] = record['ssi_val']
        record['241'] = record['hi_yn']
        record['242'] = record['hiown']
        record['243'] = record['hiemp']
        record['244'] = record['hipaid']
        record['245'] = record['emcontrb']
        record['246'] = record['hi']
        record['247'] = record['hityp']
        record['248'] = record['paid']
        record['249'] = record['priv']
        record['250'] = record['prityp']
        record['251'] = record['ss_val']
        record['252'] = record['uc_val']
        record['253'] = record['mcare']
        record['254'] = record['wc_val']
        record['255'] = record['vet_val']
        record['256'] = np.nan
        record['257'] = np.nan
        record['258'] = np.nan
        record['259'] = np.nan
        record['260'] = np.nan
        record['261'] = np.nan
        record['262'] = np.nan
        record['263'] = np.nan
        record['264'] = np.nan
        record['265'] = np.nan
        record['266'] = np.nan
        record['267'] = np.nan
        record['268'] = np.nan
        record['269'] = np.nan
        record['270'] = np.nan
        record['271'] = np.nan
        record['272'] = np.nan
        record['273'] = np.nan
        record['274'] = np.nan
        record['275'] = np.nan

        if sp_ptr != 0:
            record['256'] = self.household[sp_ptr - 1]['paw_val']
            record['257'] = self.household[sp_ptr - 1]['mcaid']
            record['258'] = self.household[sp_ptr - 1]['pchip']
            record['259'] = self.household[sp_ptr - 1]['wicyn']
            record['260'] = self.household[sp_ptr - 1]['ssi_val']
            record['261'] = self.household[sp_ptr - 1]['hi_yn']
            record['262'] = self.household[sp_ptr - 1]['hiown']
            record['263'] = self.household[sp_ptr - 1]['hiemp']
            record['264'] = self.household[sp_ptr - 1]['hipaid']
            record['265'] = self.household[sp_ptr - 1]['emcontrb']
            record['266'] = self.household[sp_ptr - 1]['hi']
            record['267'] = self.household[sp_ptr - 1]['hityp']
            record['268'] = self.household[sp_ptr - 1]['paid']
            record['269'] = self.household[sp_ptr - 1]['priv']
            record['270'] = self.household[sp_ptr - 1]['prityp']
            record['271'] = self.household[sp_ptr - 1]['ss_val']
            record['272'] = self.household[sp_ptr - 1]['uc_val']
            record['273'] = self.household[sp_ptr - 1]['mcare']
            record['274'] = self.household[sp_ptr - 1]['wc_val']
            record['275'] = self.household[sp_ptr - 1]['vet_val']

        totincx = (was + intst + dbe + alimony + bil + pensions + rents + fil +
                   ucomp + socsec)

        if not ifdept:
            # Search for dependents among other members of the household who
            # are not already claimed on another return.
            for individual in self.household:
                idxfid = individual['ffpos']
                idxhea = individual['h_flag']
                idxspo = individual['s_flag']
                idxdep = individual['d_flag']
                dflag = False
                if ((self.household.index(individual) !=
                     self.household.index(record)) and
                        idxfid == xfid and not idxdep and not idxspo and
                        not idxhea):
                    # Determine if Individual is a dependent of the reference
                    # person
                    test1 = 1
                    test2 = 1
                    test3 = 1
                    test4 = 0
                    test5 = 0
                    dflag = False
                    age = individual['a_age']
                    income = (individual['wsal_val'] + individual['semp_val'] +
                              individual['frse_val'] + individual['uc_val'] +
                              individual['ss_val'] + individual['rtm_val'] +
                              individual['int_val'] + individual['div_val'] +
                              individual['rnt_val'] + individual['alm_val'])
                    # set up child flag (related == -1)
                    reference_person = record['a_exprrp']
                    index_person = individual['a_exprrp']
                    if reference_person == 5:
                        genref = -1
                    elif reference_person == 7:
                        genref = -2
                    elif reference_person == 8:
                        genref = 1
                    elif reference_person == 9:
                        genref = 0
                    elif reference_person == 11:
                        genref = -1
                    else:
                        genref = 99
                    if index_person == 5:
                        genind = -1
                    elif index_person == 7:
                        genind = -2
                    elif index_person == 8:
                        genind = 1
                    elif index_person == 9:
                        genind = 0
                    elif index_person == 11:
                        genind = -1
                    else:
                        genind = 99
                    if genref != 99 and genind != 99:
                        related = genind - genref
                    else:
                        related = 99
                    # In general, a person's income must be less than $2,500 to
                    # be eligible to be a dependent.
                    # But there are exceptions for children.
                    if income <= 2500:
                        test4 = 1
                    if (relcode == 5) or (related == -1):
                        if age <= 18 or (age <= 23 and record['a_enrlw'] > 0):
                            test4 = 1
                    if totincx + income > 0:
                        if income / float(totincx + income) < 0.5:
                            test5 = 1
                    else:
                        test5 = 1
                    dtest = test1 + test2 + test3 + test4 + test5
                    if dtest == 5:
                        dflag = True
                if dflag:
                    individual['d_flag'] = True
                    depne += 1
                    dage = individual['a_age']
                    record[('dep' +
                            str(depne))] = self.household.index(individual)
                    record['depage' + str(depne)] = dage

        cahe = np.nan

        record['t_flag'] = True  # tax unit flag
        returns = record['t_flag']

        namelist = ['js', 'ifdept', 'agede', 'cahe', 'ageh', 'ages', 'was',
                    'intst', 'dbe', 'alimony', 'bil', 'pensions', 'rents',
                    'fil', 'ucomp', 'socsec', 'returns', 'wt', 'zifdep',
                    'zntdep', 'zhhinc', 'zagept', 'zagesp', 'zoldes', 'zyoung',
                    'zworkc', 'zsocse', 'zssinc', 'zpubas', 'zvetbe', 'zchsup',
                    'zfinas', 'zdepin', 'zowner', 'zwaspt', 'zwassp', 'wasp',
                    'wass', 'xregion', 'xschb', 'xschf', 'xsche', 'xschc',
                    'xhid', 'xfid', 'xpid', 'depne', 'totincx', 'xstate']

        varlist = [js, ifdept, agede, cahe, ageh, ages, was, intst, dbe,
                   alimony, bil, pensions, rents, fil, ucomp, socsec, returns,
                   wt, zifdep, zntdep, zhhinc, zagept, zagesp, zoldes, zyoung,
                   zworkc, zsocse, zssinc, zpubas, zvetbe, zchsup, zfinas,
                   zdepin, zowner, zwaspt, zwassp, wasp, wass, xregion, xschb,
                   xschf, xsche, xschc, xhid, xfid, xpid, depne, totincx,
                   xstate]

        for name, var in zip(namelist, varlist):
            record[name] = var
        return record

    def hhstatus(self, unit):

        """
        Determine head of household status
        Parameters
        ----------
        unit: Tax unit

        Returns
        -------


        """
        income = 0
        for inuit in self.house_units:
            totincx = (inuit['was'] + inuit['intst'] + inuit['dbe'] +
                       inuit['alimony'] + inuit['bil'] + inuit['pensions'] +
                       inuit['rents'] + inuit['fil'] + inuit['ucomp'] +
                       inuit['socsec'])
            income += totincx
        if income > 0:
            totincx = (unit['was'] + unit['intst'] + unit['dbe'] +
                       unit['alimony'] + unit['bil'] + unit['pensions'] +
                       unit['rents'] + unit['fil'] + unit['ucomp'] +
                       unit['socsec'])
            indjs = unit['js']
            indif = unit['ifdept']
            inddx = unit['depne']
            if indjs == 1 and float(totincx)/income > 0.99:
                if indif != 1 and inddx > 0:
                    unit['js'] = 3

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
        wages = record['wsal_val']
        income = (wages + record['semp_val'] + record['frse_val'] +
                  record['uc_val'] + record['ss_val'] + record['rtm_val'] +
                  record['int_val'] + record['div_val'] + record['rnt_val'] +
                  record['alm_val'])
        if (wages > self.depwages) or (income > self.depTotal):
            depfile = 1
        else:
            depfile = False
        return depfile

    def convert(self, ix, iy):
        """
        Convert an existing tax unit (IX)
        to a dependent filer and add the dependent
        information to the target return (IY)
        Parameters
        ----------
        IX, IY : tax units

        Returns
        -------

        """
        self.house_units[ix]['ifdept'] = True
        ixdeps = self.house_units[ix]['depne']
        iydeps = self.house_units[iy]['depne']
        self.house_units[ix]['depne'] = 0
        ixjs = self.house_units[ix]['js']
        if ixjs == 2:
            self.house_units[iy]['depne'] += (ixdeps + 2)
            self.house_units[iy]['dep' + str(iydeps + 1)] = ix
            self.house_units[iy][('dep' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['sp_ptr']
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      1))] = self.house_units[ix]['a_age']
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['ages']
            iybgin = iydeps + 2
        else:
            self.house_units[iy]['depne'] += (ixdeps + 1)
            self.house_units[iy]['dep' + str(iydeps + 1)] = ix
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      1))] = self.house_units[ix]['a_age']
            iybgin = iydeps + 1
        if ixdeps > 0:
            for ndeps in range(1, ixdeps + 1):
                self.house_units[iy][('dep' + str(iybgin + ndeps))] = self.house_units[ix]['dep' + str(ndeps)]
                self.house_units[ix]['dep' + str(iybgin + ndeps)] = 0
                self.house_units[iy]['depage' + str(iybgin + ndeps)] = self.house_units[ix]['depage' + str(ndeps)]

    def tax_units_search(self):
        """
        Analogous to SEARCH2 macro in SAS files.
        Searches among the tax units in a household to see if there are any
        dependencies
        Parameters
        ----------

        Returns
        -------

        """
        highest = -9.9E32
        idxhigh = 0
        for ix in range(0, self.nunits):
            totincx = self.house_units[ix]['totincx']
            if totincx > highest:
                highest = totincx
                idxhigh = ix
        if not self.house_units[idxhigh]['ifdept']:
            for ix in range(0, self.nunits):
                idxjs = self.house_units[ix]['js']
                idxdepf = self.house_units[ix]['ifdept']
                idxrelc = self.house_units[ix]['a_exprrp']
                idxfamt = self.house_units[ix]['ftype']
                if ((ix != idxhigh) and (idxdepf != 1) and (highest >= 0) and
                        (idxjs != 2)):
                    if (idxfamt == 1) or (idxfamt == 3) or (idxfamt == 5):
                        totincx = self.house_units[ix]['totincx']
                        if totincx <= 0:
                            self.house_units[ix]['t_flag'] = False
                            self.convert(ix, idxhigh)
                        if 3000 >= totincx > 0:
                            self.convert(ix, idxhigh)
                    if idxrelc == 11:
                        self.house_units[ix]['t_flag'] = False
                        self.convert(ix, idxhigh)

    def filst(self, output):
        """
        Determines whether or not a CPS Tax Unit
        actually files a return.
        Parameters
        ----------
        output

        Returns
        -------

        """

        # test1: wage test
        output['filst'] = 0
        if output['js'] == 1:
            if output['was'] >= self.wage1:
                output['filst'] = 1
        if output['js'] == 2:
            if output['depne'] > 0:
                if output['was'] >= self.wage2:
                    output['filst'] = 1
                if output['was'] >= self.wage2nk:
                    output['filst'] = 1
        if output['js'] == 3:
            if output['was'] >= self.wage3:
                output['filst'] = 1

        # test2: wage test
        if output['js'] == 1:
            amount = self.single - self.depExempt * output['depne']
            if output['agede'] != 0:
                amount = self.single65 - self.depExempt * output['depne']
            if output['income'] >= amount:
                output['filst'] = 1
        if output['js'] == 2:
            amount = self.joint - self.depExempt * output['depne']
            if output['agede'] == 1:
                amount = self.joint65one - self.depExempt * output['depne']
                amount = self.joint65both - self.depExempt * output['depne']
            if output['income'] >= amount:
                output['filst'] = 1
        if output['js'] == 3:
            amount = self.hoh
            if output['agede'] != 0:
                amount = self.hoh65 - self.depExempt * output['depne']
            if output['income'] >= amount:
                output['filst'] = 1

        # test3: dependent filers
        if output['ifdept']:
            output['filst'] = 1
        # test4: random selection
        if (output['js'] == 3 and output['agede'] > 0 and
                output['income'] < 6500 and output['depne'] > 0):
            output['filst'] = 0
        # test5 : negative income
        if (output['bil'] < 0) or (output['fil'] < 0) or (output['rents'] < 0):
            output['filst'] = 1

    def output(self, unit):
        """
        After all CPS Tax Units have been created,
        output all records.
        Parameters
        ----------
        unit

        Returns
        -------
        output
        """

        output = {}
        depne = unit['depne']
        if unit['js'] == 2:
            txpye = 2
        else:
            txpye = 1
        xxtot = txpye + depne
        # Check relationship codes among dependents
        xxoodep = 0
        xxopar = 0
        xxocah = 0
        xxocawh = 0
        if depne > 0:
            for i in range(1, depne+1):
                pptr = i
                dindex = unit['dep' + str(i)]
                drel = self.household[dindex]['a_exprrp']
                dage = self.household[dindex]['a_age']
                if drel == 8:
                    xxopar += 1
                if (drel >= 9) and (dage >= 18):
                    xxoodep += 1
                if dage < 18:
                    xxocah += 1

        output['xagex'] = unit['agede']
        output['xstate'] = unit['xstate']
        output['xregion'] = unit['xregion']
        output['xschb'] = unit['xschb']
        output['xschf'] = unit['xschf']
        output['xsche'] = unit['xsche']
        output['xschc'] = unit['xschc']
        output['xhid'] = unit['xhid']
        output['xfid'] = unit['xfid']
        output['xpid'] = unit['xpid']

        oldest = 0
        youngest = 0
        if depne > 0:
            oldest = -9.9E16
            youngest = 9.9E16
            for i in range(1, depne + 1):
                dindex = i
                dage = unit['depage' + str(dindex)]
                if dage > oldest:
                    oldest = dage
                if dage < youngest:
                    youngest = dage
                unit['zoldes'] = oldest
                unit['zyoung'] = youngest

        output['oldest'] = oldest
        output['youngest'] = youngest
        output['xxocah'] = xxocah
        output['xxocawh'] = xxocawh
        output['xxoodep'] = xxoodep
        output['xxopar'] = xxopar
        output['xxtot'] = xxtot

        icps1 = unit['101']
        icps2 = unit['102']
        icps3 = np.nan
        icps4 = np.nan
        icps5 = np.nan
        icps6 = np.nan
        icps7 = np.nan
        icps8 = youngest
        icps9 = oldest
        icps10 = unit['110']
        icps11 = unit['111']
        icps12 = unit['112']
        icps13 = unit['113']
        icps14 = unit['114']
        icps15 = unit['115']
        icps16 = unit['116']
        icps17 = unit['117']
        icps18 = unit['118']
        icps19 = unit['119']
        icps20 = unit['120']
        icps21 = unit['121']
        icps22 = unit['122']
        icps23 = unit['123']
        icps24 = unit['124']
        icps25 = unit['125']
        icps26 = unit['126']
        icps27 = unit['127']
        icps28 = unit['128']
        icps29 = unit['129']
        icps30 = unit['130']
        icps31 = unit['131']
        icps32 = unit['132']
        icps33 = unit['133']
        icps34 = unit['134']
        icps35 = unit['135']
        icps36 = unit['136']
        icps37 = unit['137']
        icps38 = unit['138']
        icps39 = unit['139']
        icps40 = unit['140']
        icps41 = unit['141']
        icps42 = unit['142']
        icps43 = unit['143']
        icps44 = unit['144']
        icps45 = unit['145']
        icps46 = unit['146']
        icps47 = unit['147']
        icps48 = unit['148']

        jcps1 = unit['151']
        jcps2 = unit['152']
        jcps3 = unit['153']
        jcps4 = unit['154']
        jcps5 = unit['155']
        jcps6 = unit['156']
        jcps7 = unit['157']
        jcps8 = unit['158']
        jcps9 = unit['159']
        jcps10 = unit['160']
        jcps11 = unit['161']
        jcps12 = unit['162']
        jcps13 = unit['163']
        jcps14 = unit['164']
        jcps15 = unit['165']
        jcps16 = unit['166']
        jcps17 = unit['167']
        jcps18 = unit['168']
        jcps19 = unit['169']
        jcps20 = unit['170']
        jcps21 = unit['171']
        jcps22 = unit['172']
        jcps23 = unit['173']
        jcps24 = unit['174']
        jcps25 = unit['175']
        jcps26 = unit['176']
        jcps27 = unit['177']
        jcps28 = unit['178']
        jcps29 = unit['179']
        jcps30 = unit['180']
        jcps31 = unit['181']
        jcps32 = unit['182']
        jcps33 = unit['183']
        jcps34 = unit['184']
        jcps35 = unit['185']
        jcps36 = unit['186']
        jcps37 = unit['187']
        jcps38 = unit['188']
        jcps39 = unit['189']
        jcps40 = unit['190']
        jcps41 = unit['191']
        jcps42 = unit['192']
        jcps43 = unit['193']
        jcps44 = unit['194']
        jcps45 = unit['195']
        jcps46 = unit['196']
        jcps47 = unit['197']
        jcps48 = unit['198']
        jcps49 = unit['199']
        jcps50 = unit['200']
        jcps51 = unit['201']
        jcps52 = unit['202']
        jcps53 = unit['203']
        jcps54 = unit['204']
        jcps55 = unit['205']
        jcps56 = unit['206']
        jcps57 = unit['207']
        jcps58 = unit['208']
        jcps59 = unit['209']
        jcps60 = unit['210']
        jcps61 = unit['211']
        jcps62 = unit['212']
        jcps63 = unit['213']
        jcps64 = unit['214']
        jcps65 = unit['215']
        jcps66 = unit['216']
        jcps67 = unit['217']
        jcps68 = unit['218']
        jcps69 = unit['219']
        jcps70 = unit['220']
        jcps71 = unit['221']
        jcps72 = unit['222']
        jcps73 = unit['223']
        jcps74 = unit['224']
        jcps75 = unit['225']
        jcps76 = unit['226']
        jcps77 = np.nan
        jcps78 = np.nan
        jcps79 = np.nan
        jcps80 = np.nan
        jcps81 = np.nan
        jcps82 = np.nan
        jcps83 = np.nan
        jcps84 = np.nan

        if not unit['ifdept']:
            jcps77 = unit['228']
            jcps78 = unit['229']
            jcps79 = unit['230']
            jcps80 = unit['231']
            jcps81 = unit['232']
            jcps82 = unit['233']
            jcps83 = unit['234']
            jcps84 = unit['235']

        jcps85 = unit['236']
        jcps86 = unit['237']
        jcps87 = unit['238']
        jcps88 = unit['239']
        jcps89 = unit['240']
        jcps90 = unit['241']
        jcps91 = unit['242']
        jcps92 = unit['243']
        jcps93 = unit['244']
        jcps94 = unit['245']
        jcps95 = unit['246']
        jcps96 = unit['247']
        jcps97 = unit['248']
        jcps98 = unit['249']
        jcps99 = unit['250']
        jcps100 = unit['251']
        jcps101 = unit['252']
        jcps102 = unit['253']
        jcps103 = unit['254']
        jcps104 = unit['255']
        jcps105 = unit['256']
        jcps106 = unit['257']
        jcps107 = unit['258']
        jcps108 = unit['259']
        jcps109 = unit['260']
        jcps110 = unit['261']
        jcps111 = unit['262']
        jcps112 = unit['263']
        jcps113 = unit['264']
        jcps114 = unit['265']
        jcps115 = unit['266']
        jcps116 = unit['267']
        jcps117 = unit['268']
        jcps118 = unit['269']
        jcps119 = unit['270']
        jcps120 = unit['271']
        jcps121 = unit['272']
        jcps122 = unit['273']
        jcps123 = unit['274']
        jcps124 = unit['275']

        for i in range(1, 49):
            var = 'icps' + str(i)
            output[str(var)] = eval(var)
        for i in range(1, 125):
            var = 'jcps' + str(i)
            output[str(var)] = eval(var)

        d5 = min(depne, 5)
        if d5 > 0:
            for i in range(1, d5 + 1):
                var = 'icps' + str(2+i)
                output[str(var)] = unit['depage' + str(i)]

        zdepin = 0
        if depne > 0:
            for i in range(1, depne+1):
                dindex = unit['dep' + str(i)]
                if not self.household[dindex]['flag']:
                    zdepin = (zdepin + self.household[dindex]['wsal_val'] +
                              self.household[dindex]['semp_val'] +
                              self.household[dindex]['frse_val'] +
                              self.household[dindex]['uc_val'] +
                              self.household[dindex]['ss_val'] +
                              self.household[dindex]['rtm_val'] +
                              self.household[dindex]['int_val'] +
                              self.household[dindex]['div_val'] +
                              self.household[dindex]['alm_val'])
        output['h_seq'] = unit['h_seq']
        output['hhid'] = unit['h_seq']
        output['peridnum'] = unit['peridnum']
        output['js'] = unit['js']
        output['ifdept'] = unit['ifdept']
        output['agede'] = unit['agede']
        output['depne'] = unit['depne']
        output['cahe'] = unit['cahe']
        output['ageh'] = unit['ageh']
        output['ages'] = unit['ages']
        output['was'] = unit['was']
        output['intst'] = unit['intst']
        output['dbe'] = unit['dbe']
        output['alimony'] = unit['alimony']
        output['bil'] = unit['bil']
        output['pensions'] = unit['pensions']
        output['rents'] = unit['rents']
        output['fil'] = unit['fil']
        output['ucomp'] = unit['ucomp']
        output['socsec'] = unit['socsec']

        output['income'] = (unit['was'] + unit['intst'] + unit['dbe'] +
                            unit['alimony'] + unit['bil'] + unit['pensions'] +
                            unit['rents'] + unit['fil'] + unit['ucomp'] +
                            unit['socsec'])

        output['returns'] = unit['returns']
        output['wt'] = unit['wt']
        output['zifdep'] = unit['zifdep']
        output['zntdep'] = unit['zntdep']
        output['zhhinc'] = unit['zhhinc']
        output['zagesp'] = unit['zagesp']
        output['zoldes'] = unit['zoldes']
        output['zyoung'] = unit['zyoung']
        output['zworkc'] = unit['zworkc']
        output['zsocse'] = unit['zsocse']
        output['zssinc'] = unit['zssinc']
        output['zpubas'] = unit['zpubas']
        output['zvetbe'] = unit['zvetbe']
        output['zchsup'] = unit['zchsup']
        output['zfinas'] = unit['zfinas']
        output['zdepin'] = zdepin
        output['zowner'] = unit['zowner']
        output['zwaspt'] = unit['zwaspt']
        output['zwassp'] = unit['zwassp']
        output['wasp'] = unit['wasp']
        output['wass'] = unit['wass']

        self.filst(output)

        return output

# Temporary. In future, class will be initiated in earlier script.
# Read in data


cps_recs = pd.read_csv('cpsmar2014.csv')
# Obtain the household sequence numbers
test = Returns(cps_recs)
