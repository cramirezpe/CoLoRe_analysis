from CoLoRe_analysis.shear_reader import ShearReader, redshift_to_str_for_path
from CoLoRe_analysis.functions import check_iterable
import numpy as np
from sklearn.linear_model import LinearRegression
from shutil import copy2
import os


import logging
log = logging.getLogger(__name__)


# It takes two lists of sim classes. It will average and compute the correlation (or maybe the other way around...)
class CorrelateTwoShears:
    def __init__(self, listA, listB):
        # Check iterables
        listA = list(listA) if isinstance(listA, tuple) else listA
        listB = list(listB) if isinstance(listB, tuple) else listB
        if not isinstance(listA, list) or not isinstance(listB, list):
            raise ValueError(f'One of the objects provided is not list or tuple')

        # Check elements with same seed and remove them
        seeds_A = set()
        seeds_B = set()
        
        for list_,seeds in zip( (listA, listB), (seeds_A, seeds_B)):
            for sim in reversed(list_): # Reversed to not break when removing
                if sim.seed in seeds:
                    list_.remove(sim)
                else:
                    seeds.add(sim.seed)
                    
        # Remove unmatched elements
        for list_,seeds in zip( (listA, listB), (seeds_B, seeds_A) ):
            for sim in reversed(list_):
                if sim.seed not in seeds:
                    list_.remove(sim)

        self.seeds = seeds_A.intersection(seeds_B)

        self.listA  = listA
        self.listB  = listB

        # Converting into dict of seeds
        self.sims = {}
        for seed in self.seeds:
            matched_sims = []
            for list_ in (listA, listB):
                for sim in list_:
                    if sim.seed == seed:
                        sim.set_shear_reader()
                        matched_sims.append(sim)
                        break
            self.sims[seed] = matched_sims
    
    def correlation_in_bin(self, parameter='mp_e1', source=1, minz=None, maxz=None):
        correlations = []
        for seed in self.sims.keys():
            Avals = self.sims[seed][0].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)
            Bvals = self.sims[seed][1].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)

            correlations.append( np.corrcoef(Avals,Bvals)[0][1] )
        return np.mean(correlations)

    def regression_in_bin(self, parameter='mp_e1', source=1, minz=None, maxz=None):
        reg_coef    = []
        reg_intercept = []
        for seed in self.sims.keys():
            Avals = self.sims[seed][0].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)
            Bvals = self.sims[seed][1].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)

            model = LinearRegression().fit(Avals.reshape((-1,1)),Bvals)
            reg_coef.append( model.coef_[0])
            reg_intercept.append( model.intercept_)
        return np.mean(reg_coef), np.mean(reg_intercept)
      
    def store_correlation(self, parameter='mp_e1', source=1, minz=None, maxz=None, out=None):
        if out == None and len(self.sims) > 1:
            raise ValueError('Multiple simulations provided. Output path is needed')
        
        if out == None:
            out = self.path_to_correlation(parameter=parameter, source=source, minz=minz, maxz=maxz)
            if not os.path.exists(out):
                os.makedirs(out)
            seed = list(self.seeds)[0]
            copy2(self.sims[seed][1].analysis_location+'/sim_info.json',out+'/compared_to_info.json')         

        correlation = self.correlation_in_bin(parameter=parameter, source=source, minz=minz, maxz=maxz)

        with open(out+ '/' + parameter +'.dat', "w") as f:
            f.write(str(correlation))

    def store_regression(self, parameter='mp_e1', source=1, minz=None, maxz=None, out=None):
        if out == None and len(self.sims) > 1:
            raise ValueError('Multiple simulations provided. Output path is needed')
        
        if out == None:
            out = self.path_to_regression(parameter=parameter, source=source, minz=minz, maxz=maxz)
            if not os.path.exists(out):
                os.makedirs(out)
            seed = list(self.seeds)[0]
            copy2(self.sims[seed][1].analysis_location+'/sim_info.json',out+'/compared_to_info.json')         

        coef, intercept = self.regression_in_bin(parameter=parameter, source=source, minz=minz, maxz=maxz)

        with open(out+ '/coef_' + parameter +'.dat', "w") as f:
            f.write(str(coef))

        with open(out+ '/intercept_' + parameter +'.dat', "w") as f:
            f.write(str(intercept))


    def get_correlation(self, parameter='mp_e1', source=1, minz=None, maxz=None):
        file_path = self.path_to_correlation(parameter=parameter, source=source, minz=minz, maxz=maxz)

        with open(file_path + parameter + '.dat',"r") as f:
            correlation = f.read()
        return float(correlation)

    def get_regression(self, reg_parameter, parameter='mp_e1', source=1, minz=None, maxz=None):
        if reg_parameter not in ('coef','intercept'):
            raise ValueError(f'Unvalid regression parameter: { reg_parameter } not in ("coef","intercept")')

        file_path = self.path_to_regression(parameter=parameter, source=source, minz=minz, maxz=maxz)

        with open(file_path + reg_parameter + '_' + parameter + '.dat',"r") as f:
            regression_value = f.read()
        return float(regression_value)        

    def path_to_correlation(self, parameter='mp_e1', source=1, minz=None, maxz=None):
        seed = list(self.seeds)[0]
        if minz != None and maxz != None:
            minz_str = redshift_to_str_for_path(minz)
            maxz_str = redshift_to_str_for_path(maxz)
            out = self.sims[seed][0].analysis_location + f'/shear_data/correlations/' + self.sims[seed][1].preparation_time +f'/binned/{ minz_str }_{ maxz_str }/source_{ source }/'
        else:
            out = self.sims[seed][0].analysis_location + f'/shear_data/correlations/source_{ source }/' + self.sims[seed][1].preparation_time +'/'
        return out

    def path_to_regression(self, parameter='mp_e1', source=1, minz=None, maxz=None):
        return self.path_to_correlation(parameter=parameter, source=source, minz=minz, maxz=maxz).replace('correlations','regressions')