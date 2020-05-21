from lib.data_treatment import data_treatment
import numpy as np

# The class shear reader is used to get data from data_treatment, it will always be shear information but it can also treat with cl information.
class ShearReader:
    def __init__(self,location):
        self.location = location
    
    def do_data_treatment(self,source=1, do_cls=False, do_kappa=False):
        data_treatment(self.location,source, do_cls, do_kappa)

    def get_values(self,parameter, source=1):
        try:
            return np.loadtxt(self.location + f'/data_treated/source_{ source }/'+parameter+'.dat')
        except OSError:
            if parameter == 'mp_k': 
                do_kappa = True
            else:
                do_kappa = False

            if parameter[:2] == 'cl' or parameter == 'ld' or parameter == 'lt':
                do_cls   = True
            else:
                do_cls   = False
            self.do_data_treatment(source=source, do_cls=do_cls, do_kappa=do_kappa)
            return np.loadtxt(self.location + f'/data_treated/source_{ source }/'+parameter+'.dat')
