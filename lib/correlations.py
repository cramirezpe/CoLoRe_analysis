from lib.shear_reader import ShearReader
from lib.functions import check_iterable
import numpy as np

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
    
    def correlation_in_bin(self,parameter='mp_e1',source=1, minz=None, maxz=None):
        correlations = []
        for seed in self.sims.keys():
            Avals = self.sims[seed][0].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)
            Bvals = self.sims[seed][0].shear_reader.get_values(parameter=parameter, source=source, minz=minz, maxz=maxz)

            correlations.append( np.corrcoef(Avals,Bvals)[0][1])
        
        return np.mean(correlations)
            

