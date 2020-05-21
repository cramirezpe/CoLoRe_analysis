from lib.data_treatment import data_treatment
import numpy as np

# The class shear reader is used to get data from data_treatment, it will always be shear information but it can also treat with cl information.
class ShearReader:
    def __init__(self,location):
        self.location = location
    
    def do_data_treatment(self,source=1, do_cls=False, do_kappa=False, minz=None, maxz=None, output_path=None):
        data_treatment(self.location,source, do_cls, do_kappa, minz, maxz, output_path)

    def get_values(self, parameter, source=1, minz=None, maxz=None):
        if minz and maxz:
            minz    = round(float(minz)*100)
            maxz    = round(float(maxz)*100)
            path    = self.location + f'/data_treated/binned/{ str(minz) }_{ str(maxz) }/source_{ source }'
        else:
            path    = self.location + f'/data_treated/source_{ source }'

        try:
            return np.loadtxt( path + '/'+parameter+'.dat')
        except OSError:
            if parameter == 'mp_k': 
                do_kappa = True
            else:
                do_kappa = False

            if parameter[:2] == 'cl' or parameter == 'ld' or parameter == 'lt':
                do_cls   = True
            else:
                do_cls   = False

            self.do_data_treatment(source=source, do_cls=do_cls, do_kappa=do_kappa, minz=minz, maxz=maxz, output_path=path)
            return np.loadtxt( path + '/'+parameter+'.dat')

    def compute_binned_statistics(self, minz, maxz, bins, source=1):
        # I use mp_e1 to not compute if values already exist
        step = (maxz-minz)/bins
        for b in range(bins):
            _ = self.get_values('mp_e1', minz=minz+b*step, maxz= minz + (1+b)*step)