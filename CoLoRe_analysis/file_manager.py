import os
import shutil 
from lib.time_analysis_LSST import Sim0404
import configparser

# The class FileManager should be understood as a group of functions (a FileManager object would be totally unuseful). 
# All the file handling system relies in the existence of a info_file in each Simulation. This info_file will contain the basic information of the Simulation and it is included by default in the scripts located in Shs/CoLoRe_LSST/. 
# With the built-in function get_simulations, it searches for every info_file below the given path and therefore any Simulation. This is very useful because hierarchy in the directories is no longer needed. 
# Simulations can be deleted by using the classmethod remove_sim or the method .remove in Simulation objects (from Simulation class). 
class FileManager:
    info_file = "sim_info.INI"
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
                        
        return sorted(list(sims), key=lambda folder: int(cls.get_parameter(folder,'preparation_time')))
    
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
        config = configparser.ConfigParser()
        config.read(path + '/' + cls.info_file)

        for item in param_filter.items():
            # Translate single values into list
            if type(item[1]) != list:
                values = [item[1]]
            else:
                values = item[1]
            
            # For the item, check if our Simulation has one of the values:
            if config.get('SIM_CONFIG',item[0],fallback=None) not in map(str,values):
                return False
        return True
    
    @classmethod
    def get_parameter(cls,path,param):
        config = configparser.ConfigParser()
        config.read(path + '/' + cls.info_file)
        return config.get('SIM_CONFIG', param)
    
    @classmethod
    def change_parameter(cls, path, param, value):
        config = configparser.ConfigParser()
        config.read(path + '/' + cls.info_file )
        config.set('SIM_CONFIG',param,value)
        with open(path + '/' + cls.info_file, 'w') as configfile:
            config.write(configfile)
            
    @classmethod
    def print_sims_table(cls,path,param_filter):
        sims = {}
        print('| id | commit | Status | Nodes | Seed | Version | Template | Factor | Shear | Nside | Memory (GB) | Disk  | Time (s)| Preparation Date')
        print(' |:---:|:----:|:----:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:----:|:----:|')

        # Delete empty directories
        FileManager.remove_empty_dirs(path)

        # Find simulations
        for i,sim in enumerate(cls.get_simulations(path,param_filter)):
            simname = i
            sims[simname] = Sim0404(sim,simname)
        
        # Getting informations    
        for x in sims.keys():
            if sims[x].status == 'done': 
                sims[x].set_time_reader()
                
            sims[x].set_memory_reader()
            sims[x].set_size()
            sims[x].set_shear_reader()
            
        for sim in sims.items():
            x = sim[1]
            total_time = round(x.time_reader.times["Total"]/1000 if x.status == 'done' else 0,4)
            print('| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |'.format(x.__name__,x.commit,x.status,x.nodes,x.seed,x.version,x.template,x.factor,x.shear,x.nside,x.memory_reader.tasks['Total']['Memory']/1000, x.size,total_time, x.preparation_time))
        return sims

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