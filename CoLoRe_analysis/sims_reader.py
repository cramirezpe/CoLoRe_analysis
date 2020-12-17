import glob
import json
import logging
import os
import re
import shutil
import subprocess

import numpy as np

from CoLoRe_analysis import ccl_reader, shear_reader

log = logging.getLogger(__name__)


# Simulation class is the responsible of handling Simulations within the LSST framework. 
# Each Simulation object will contain information of an individual Simulation and the methods to obtain it.
class Simulation:
    def __init__(self, analysis_location, name=None):
        self.analysis_location = analysis_location
        self.__name__ = name
        
        with open(f'{self.analysis_location}/sim_info.json') as json_file:
            self.info = json.load(json_file)                
        
        self.location= self.info['path']
        
        if '_param_cfg' not in self.info:
            param_file = self.location + '/param.cfg'
            while True:
                try:
                    self.get_config_file(param_file)
                    print('Configuration file found in '+param_file)
                    break
                except FileNotFoundError:
                    param_file = input(f'Configuration file for simulation {self.location} not found. Please provide the param.cfg path/s to skip\n')
                    

        try: 
            self.seed               = self.info['_param_cfg']['global']['seed']
        except KeyError:
            self.seed  = None
        try:
            self.shear_nshear       = self.info['_param_cfg']['shear']['n_shear']
            self.shear_nside        = self.info['_param_cfg']['shear']['nside']
        except KeyError:
            self.shear_nshear = None
            self.shear_nside  = None
        
        self.version            = self.info['version']
        self.factor             = self.info['factor']
        self.template           = self.info['template']
        self.status             = self.info['status']
        self.nodes              = self.info['nodes']
        self.preparation_time   = self.info['preparation_time']
        self.commit             = self.info['commit']

        if self.status != 'prepared': 
            try:
                self.terminal_file =glob.glob(self.location + '/script/terminal*')[-1]
            except: #pragma: no cover
                self.terminal_file =None
            try:
                self.error_file =   glob.glob(self.location + '/script/*.error')[-1]
            except: #pragma: no cover
                self.error_file =   None
            try:
                self.output_file =  glob.glob(self.location + '/script/*.out')[-1]
            except: #pragma: no cover
                self.output_file =  None

    def get_config_file(self, param_filename):
        '''
        Load the C libconfig file into a python dictionary.
        
        Args:
            param_filename (str): Name of the param.cfg file inside the simulation path. 
        
        Returns:
            config dictionary
        '''
        import libconf
        with open(param_filename) as f:
            config = libconf.load(f)

        self.write_to_json_file('_param_cfg', config)
        return config

       
    def __str__(self): # pragma: no cover
        if self.__name__:
            return str(self.__name__)
        else:
            return str(self.location)
        
    def write_to_json_file(self, key, value):
        self.info[key] = value

        with open(f'{self.analysis_location}/sim_info.json', 'w') as json_file:
            json.dump(self.info, json_file, indent=4, sort_keys=True)
        
    def overwrite_ini_file(self): # pragma: no cover
        try:
            madeby = self.info['made_by']
        except Exception:
            madeby = None

        info = {
            'version'           : self.version,
            'seed'              : self.seed,
            'factor'            : self.factor,
            'template'          : self.template,
            'status'            : self.status,
            'nodes'             : self.nodes,
            'preparation_time'  : self.preparation_time, 
            'shear_nshear'      : self.shear_nshear,
            'shear_nside'       : self.shear_nside, 
            'commit'            : self.commit,
            'path'              : self.location,
            'made_by'           : madeby
        }

        with open(f'{self.analysis_location}/sim_info.json', 'w') as json_file:
            json.dump(info, json_file, indent=4, sort_keys=True)
     
        with open(f'{self.analysis_location}/sim_info.json') as json_file:
            self.info = json.load(json_file)
        
    def set_time_reader(self): 
        #pylint: disable=no-member    
        self.time_reader = TimeReader(self.version,self.commit,self.terminal_file,self.positions_time_def, self.nodes)
        self.time_reader.get_times()
        
    def set_memory_reader(self): 
        #pylint: disable=no-member    
        self.memory_reader = MemoryReader(self.terminal_file,self.positions_memory_def,self.memory_line_key)
        self.memory_reader.get_memory_values_from_file()
        self.used_nodes = len(self.memory_reader.tasks) - 1

    def set_shear_reader(self):
        self.shear_reader = shear_reader.ShearReader(self.location, self.analysis_location)

    def set_ccl_reader(self, skip_lensing=False, skip_theory=False, skip_data=False):
        self.ccl_reader = ccl_reader.CCLReader(self.location, self.analysis_location, skip_lensing, skip_theory, skip_data)
        
    def set_size(self):
        # in Mb
        self.size = subprocess.check_output(['du','-sh', self.location]).split()[0].decode('utf-8')
 
    def remove(self): # pragma: no cover
        # After run this, remember to remove it from any array that contains it.
        while True:
            confirmation = input(f'Remove full simulation from {self.location}? (y/n)')
            if confirmation == 'y':
                print('Removing simulation')
                shutil.rmtree(self.location)
                break
            elif confirmation == 'n':
                print('Cancelling')
                return
           
    @property
    def version(self):
        return self._version
    
    @version.setter
    def version(self, value):
        if value not in ['New','Old','master','master_bias3',None]:
            raise TypeError('Version should be New/Old/master',value)
        self._version = value
        
class Sim0404(Simulation):
    # The nomenclature is: Title: [Search string (if none: title), find time in the (1st/2nd/3rd) ocurrence of > below]
    positions_time_def = {
        "Creating Fourier-space density and Newtonian potential" : [None,1],
        "Transforming density and Newtonian potential" : [None,1],
        "Normalizing density and Newtonian potential" : [None,1],
        "Creating physical matter density" : [None,1],
        "Computing normalization of density field" : [None,1],
        "Getting point sources 0-th galaxy population": ["0-th galaxy population",1],
        "Getting point sources 1-th galaxy population": ["1-th galaxy population",1],
        "Re-distributing sources across nodes": [None,1],
        "Getting LOS information": [None,1],
        "Writing source catalogs 0-th": ["0-th population (FITS)",1],
        "Writing source catalogs 1-th": ["1-th population (FITS)",1],
        "Writing kappa source maps": [None,1],        
        "Total": ["Total time ellapsed",1]
    }
        
    positions_memory_def = {
        "Node" : ["will",-1],
        "Memory" : ["allocate",1],
        "Gaussian Memory": ["(Gaussian),",-2],
        "srcs Memory": ["(srcs),",-2],
        "kappa Memory": ["(kappa),",-2]
    }

    memory_line_key = "will allocate"

# The class TimeReader is devoted to obtain computation time for a given Simulation. 
# The process relies in the terminal output of CoLoRe and therefore it requires tricky methods (searching for strings in files). This is likely to change in the future and hence the convenience of having it separatedly.
class TimeReader:
    def __init__(self,version,commit,terminal_file,positions_def,nodes):
        self.version        = version
        self.commit         = commit
        self.file           = terminal_file
        self.positions_def  = positions_def
        self.nodes          = nodes
        
    def get_times(self):
        times = {}
        for key in self.positions_def.keys():
            search_string = self.positions_def[key][0]
            if not search_string:
                search_string = key
            line_string = search_1st_string_in_file(self.file, search_string)[0]
            line_time = search_1st_string_in_file(self.file, 'time ellapsed' ,ocurrence=self.positions_def[key][1], startline=line_string-1 if line_string else None)
            # Search the next ocurrence of time ellapsed
            times[key] = get_time_from_string(line_time[1])
        self.times = times      

        self.raw_hours = times['Total']*self.nodes/(1000*60*60)

# The class MemoryReader is devoted to obtain memory usage for a given Simulation. 
# The process relies in the terminal output of CoLoRe and therefore it requires tricky methods (searching for strings in files). This is likely to change in the future and hence the convenience of having it separatedly.
class MemoryReader:
    def __init__(self,file,positions_def,line_key):
        self.file = file
        self.positions_def = positions_def
        self.line_key = line_key
        
    def get_memory_values_from_file(self):
        lines = search_string_in_file(self.file, self.line_key)[:,1]
        
        self.set_positions(lines[0].split())
        tasks = {}
        for line in lines: 
            split_line = line.split()
            node = int(split_line[self.positions["Node"]])
            tasks[node] = {}
            
            # Now for each key I get the value (if the key is node It's already defined)
            for key in self.positions.keys():
                if key == "Node": continue
                if self.positions[key]:
                    value = self.remove_non_digits( split_line[self.positions[key]] )
                    unit  = split_line[self.positions[key]+1]
                    tasks[node][key] = translate_into_MB(value,unit)
                # if position is none is because it was not found, hence set to 0
                else:
                    tasks[node][key] = 0
                          

        # Let's compute the totals
        Totals = {}
        for x in tasks[0].keys():
            Totals[x] = sum( [ tasks[task][x] for task in tasks.keys() ] )
        
        # And add the totals as a new element in dict
        tasks["Total"] = Totals
                
        self.tasks = tasks
    
    def set_positions(self, splitted_line):
        positions = {}
        for key in self.positions_def.keys():
            try:
                positions[key] = splitted_line.index( self.positions_def[key][0] ) + self.positions_def[key][1]
            except ValueError:
                positions[key] = None
        self.positions = positions
        
    @staticmethod
    def remove_non_digits(x):
        non_decimal = re.compile(r'[^\d.]+')
        return non_decimal.sub('', x)
   
def translate_into_MB(number,unit): #pragma: no cover
    ''' This function will transalte expressions of type 79.729 GB, TB into MB '''
   
    if unit == "GB":
        factor = 10**3
    elif unit == "TB":
        factor = 10**6
    elif unit =="MB":
        factor = 1
    else:
        raise ValueError('Invalid unit', unit)
        
    return float(number)*factor

def get_time_from_string(line):
    '''This function will get the number prior to "ms" string for the string "line"'''
    # If line is None I return 0
    if not line:
        return 0
    
    if "ms" not in line:
        print('"ms" string not found in string: {}'.format(line))
        return 0
    else:
        output = re.findall(r"[-+]?\d*\.\d+|\d+", line)
        if len(output) > 1:
            raise ValueError('Two floats where found', line)
        return float(output[0])
    
    
def search_1st_string_in_file(filepath,string,ocurrence=1,startline=0):
    '''This function searchs a string in a text file and returns the line in which it appears. Use case: finding Total time ellapsed line'''
    if not startline: startline=0
    line_number = 0 
    found = 0
    with open(filepath, 'r') as f:
        for i in range(startline): #pylint: disable=unused-variable
            line_number += 1
            next(f)
        for line in f:
            line_number += 1
            if string in line:
                found += 1
                if found == ocurrence:
                    return (line_number,line)
    return (None,None)

def search_string_in_file(filepath,string):
    '''This function searchs a string in a text file and returns the line in which it appears. Use case: finding Total time ellapsed line'''
    line_number = 0 
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            line_number += 1
            if string in line:
                results.append([line_number,line])
    return np.asarray(results)

def replace_in_file(from_string, to_string,filein):
    f = open(filein,'r')
    filedata = f.read()
    f.close()

    newdata = filedata.replace(from_string,to_string)

    f = open(filein,'w')
    f.write(newdata)
    f.close()
