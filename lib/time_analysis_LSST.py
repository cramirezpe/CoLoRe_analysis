import sys, os
from astropy.io import fits
from contextlib import contextmanager
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,AutoMinorLocator)
import datetime
import glob
import healpy as hp
import imp
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import os.path
import re
import shutil
import subprocess
from lib.shear_reader import ShearReader

class FilterList:
    def prepared():
        prepared = {
            "status" : "prepared"
        }
        return ["Prepared",prepared]
    
    def crashed():
        crashed = {
            "status" : ["crashed","crashed on data treatment"]
        }
        return ["Crashed",crashed]

    def running():
        running = {
            "status" : ["running","running data treatment"]
        }
        return ["Running",running]
    
    def done():
        done = {
            "status" : "done"
        }
        return ["Done", done]

    @classmethod
    def filters(cls):
        return [cls.prepared(),cls.crashed(),cls.running(),cls.done()]

# The class FileManager should be understood as a group of functions (a FileManager object would be totally unuseful). 
# All the file handling system relies in the existence of a info_file in each Simulation. This info_file will contain the basic information of the Simulation and it is included by default in the scripts located in Shs/CoLoRe_LSST/. 
# With the built-in function get_simulations, it searches for every info_file below the given path and therefore any Simulation. This is very useful because hierarchy in the directories is no longer needed. 
# Simulations can be deleted by using the classmethod remove_sim or the method .remove in Simulation objects (from Simulation class). 
class FileManager:
    info_file = "sim_info.dat"
    # This will remove empty folders below path
    @staticmethod
    def remove_empty_dirs(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                try:
                    if len(os.listdir( os.path.join(root, name) )) == 0: #check whether the directory is empty
                        print( "Deleting", os.path.join(root, name) )
                        try:
                            os.rmdir( os.path.join(root, name) )
                        except:
                            print( "FAILED :", os.path.join(root, name) )
                            pass
                except:
                    pass
    
    # This will find Simulations searching for info_file which must be included in any Simulation
    @classmethod
    def get_simulations(cls,path,param_filter=None):
        sims = []
        for folder, subfolder, files in os.walk(path):
            for file in files:
                # If an info_file exist, 
                if file == cls.info_file:
                    if param_filter:
                        # If the Simulation pass the filter I append it
                        if FileManager.filter_parameters(folder,param_filter):
                            sims.append(folder)   
                    # if there is no need for filter, I append directly
                    else:
                        sims.append(folder)
        return sims
    
    @classmethod
    def remove_sim(cls,path):
        if os.path.isfile(path+'/'+cls.info_file):
            shutil.rmtree(path)
            print("Simulation in path {} removed".format(path))
        else:
            raise ValueError("The path {} does not contain an info file".format(path))
        return
    
    @classmethod
    def filter_parameters(cls,path,param_filter):
        # Get the information file content into f
        with open(file = path + '/' + cls.info_file) as file:
            f = file.read()
            
        for item in param_filter.items():
            item_ok = False
            # Translate single values into list
            if type(item[1]) != list:
                values = [item[1]]
            else:
                values = item[1]
                
            # For the item, check if our Simulation has one of the values
            for value in values:
                if (str(item[0]) + '= ' + str(value)) in f:
                    # If there is one value, we can go into next item
                    item_ok = True
                    break
            
            # If we didn't found any compatible value, is uncompatible
            if not item_ok: 
                return False
        return True
    
    @classmethod
    def get_parameter(cls,path,param):
        with open(path+'/'+cls.info_file) as file:
            f = file.readlines()
        for line in f:
            if param in line:
                return line.split()[1]
        raise ValueError('Parameter {} not found in file {}'.format(param,path+'/'+cls.info_file))
    
    @classmethod
    def change_parameter(cls, path, param, from_value, to_value):
        param_filter = {
            param : from_value
        }
        
        paths = cls.get_simulations(path,param_filter)
        
        for path in paths:
            file = path + '/' + cls.info_file
            replace_in_file(param+'= '+from_value,param+'= '+to_value, file)
            
    @classmethod
    def running_to_crash(cls,path):
        cls.change_parameters(path,'status','running','crashed')
    
   
# The class TimeReader is devoted to obtain computation time for a given Simulation. 
# The process relies in the terminal output of CoLoRe and therefore it requires tricky methods (searching for strings in files). This is likely to change in the future and hence the convenience of having it separatedly.
class TimeReader:
    def __init__(self,version,commit,terminal_file,positions_def):
        self.version = version
        self.commit = commit
        self.file = terminal_file
        self.positions_def = positions_def
        
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
   
def translate_into_MB(number,unit):
    ''' This function will transalte expressions of type 79.729 GB, TB into MB '''
   
    if unit == "GB":
        factor = 10**3
    elif unit == "TB":
        factor = 10**6
    elif unit =="MB":
        factor = 1
    else:
        raise ValueError('Invalid unit', unit)
        factor = 0
        
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
        for i in range(startline):
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
    
    
#####################################################################
#####################################################################
###            SIMULATION CLASSES  ##################################
#####################################################################
#####################################################################

# Simulation class is the responsible of handling Simulations within the LSST framework. 
# Each Simulation object will contain information of an individual Simulation and the methods to obtain it.
class Simulation:
    def __init__(self, location, name=None):
        self.location = location
        self.__name__ = name
        self.version = FileManager.get_parameter(self.location,'version') 
        self.seed = FileManager.get_parameter(self.location,'seed')
        
        self.factor = FileManager.get_parameter(self.location,'factor')
        #self.factor = round(np.loadtxt(self.location + '/new_NzRed.txt')[0,1] / np.loadtxt(self.location + '/NzRed.txt')[0,1],5)
        self.template = FileManager.get_parameter(self.location, 'template')
        self.status = FileManager.get_parameter(self.location, 'status')
        self.preparation_time = FileManager.get_parameter(self.location, 'preparation_time')
        
        if self.status != 'prepared':
            self.terminal_file = glob.glob(location + '/script/terminal*')[-1]
            self.error_file =    glob.glob(location + '/script/*.error')[-1]
            self.output_file =   glob.glob(location + '/script/*.out')[-1]
        if self.version != 'master':
            self.shear = FileManager.get_parameter(self.location, 'shear')
            self.commit = FileManager.get_parameter(self.location, 'commit')
        else:
            self.shear = None
            self.commit = None
        
    def __str__(self):
        if self.__name__:
            return str(self.__name__)
        else:
            return str(self.location)
     
    def set_time_reader(self):
        self.time_reader = TimeReader(self.version,self.commit,self.terminal_file,self.positions_time_def)
        self.time_reader.get_times()
        
    def set_memory_reader(self):      
        self.memory_reader = MemoryReader(self.terminal_file,self.positions_memory_def,self.memory_line_key)
        self.memory_reader.get_memory_values_from_file()
        self.nodes = len(self.memory_reader.tasks) - 1

    def set_shear_reader(self):
        self.shear_reader = ShearReader(self.location)
        
    def set_size(self):
        # in Mb
        self.size = subprocess.check_output(['du','-sh', self.location]).split()[0].decode('utf-8')      
  
    def remove(self):
        # After run this, remember to remove it from any array that contains it.
        shutil.rmtree(self.location)
           
    @property
    def version(self):
        return self._version
    
    @version.setter
    def version(self, value):
        if value not in ['New','Old','master']:
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