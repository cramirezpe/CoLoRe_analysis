import os
import shutil 
from CoLoRe_analysis.sims_reader import Sim0404
import json
from pathlib import Path
import shutil

# The class FileManager should be understood as a group of functions (a FileManager object would be totally unuseful). 
# All the file handling system relies in the existence of a info_file in each Simulation. This info_file will contain the basic information of the Simulation and it is included by default in the scripts located in Shs/CoLoRe_LSST/. 
# With the built-in function get_simulations, it searches for every info_file below the given path and therefore any Simulation. This is very useful because hierarchy in the directories is no longer needed. 
# Simulations can be deleted by using the classmethod remove_sim or the method .remove in Simulation objects (from Simulation class). 
class FileManager:
    info_file = "sim_info.json"
    # This will remove empty folders below path

    @staticmethod
    def remove_empty_dirs(path):
        for root, dirs, files in os.walk(path, topdown=False): #pylint: disable=unused-variable
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

    @classmethod
    def import_simulations(cls, path, analysis_path, extra_sim_info=dict()):
        '''
        This method will import simulations that are located outside the analysis path into the analysis path.

        Args:
            path (str): Path where to search for simulations (it will search for sim_info.json files).
            analysis_path (str): Path for the analysis.
            extra_sim_info (dict): Extra information to add to the sim_info.json file (in dict format).
        '''
        out_path = Path(analysis_path)
        for path_object in Path(path).glob('**/'+ cls.info_file):
            datetime = path_object.parent.name
            path = str(path_object.parent)
            (out_path / datetime).mkdir(parents=True, exist_ok=True)

            if (path_object.parent / 'ccl_data').is_dir():
                shutil.copytree(path_object.parent /'ccl_data', out_path / datetime / 'ccl_data')
            if (path_object.parent / 'shear_data').is_dir():
                shutil.copytree(path_object.parent / 'shear_data', out_path / datetime / 'shear_data' )
            
            shutil.copy2( path_object, out_path / datetime)
            json_path = out_path / datetime / cls.info_file
            with open(json_path) as json_file:
                info = json.load(json_file)

            info['path'] = path
            for key, value in extra_sim_info.items():
                info[key] = value

            with open(json_path, 'w') as json_file:
                json.dump(info, json_file)
        
        return
        
    # This will find Simulations searching for info_file which must be included in any Simulation
    @classmethod
    def get_simulations(cls,path,param_filter=None):
        sims = []
        for folder, subfolder, files in os.walk(path): #pylint: disable=unused-variable
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
            while True:
                confirmation = input(f'Remove full simulation from {path}? (y/n)')
                if confirmation == 'y':
                    shutil.rmtree(path)
                    print("Simulation in path {} removed".format(path)) 
                elif confirmation == 'n':
                    print('Cancelling')
                    return
        else:
            raise ValueError("The path {} does not contain an info file".format(path))
        return
    
    @classmethod
    def filter_parameters(cls,path,param_filter):
        with open(f'{path}/sim_info.json') as json_file:
            info = json.load(json_file)
        
        for key in param_filter.keys():
            if info[key] not in param_filter[key]:
                break
        else:
            return True

        return False
        
    @classmethod
    def get_parameter(cls,path,param):
        with open(f'{path}/sim_info.json') as json_file:
            info = json.load(json_file)
        return info[param]
    
    @classmethod
    def change_parameter(cls, path, param, value):
        with open(f'{path}/sim_info.json') as json_file:
            info = json.load(json_file)

        info[param] = value

        with open(f'{path}/sim_info.json','w') as json_file:
            json.dump(info, json_file)
           
    @classmethod
    def convert_ini_into_json(cls, path): #pragma: no cover
        import configparser
        config = configparser.ConfigParser()
        config.read(path + '/sim_info.INI')
        version = config.get('SIM_CONFIG','version')
        seed    = config.getint('SIM_CONFIG','seed')
        factor  = config.getfloat('SIM_CONFIG','factor')
        template= config.get('SIM_CONFIG','template')
        status  = config.get('SIM_CONFIG','status')
        nodes   = config.getint('SIM_CONFIG','nodes', fallback=1)
        preparation_time = config.get('SIM_CONFIG','preparation_time')
        shear   = config.getint('SIM_CONFIG', 'shear', fallback=None)
        nside   = config.getint('SIM_CONFIG', 'nside', fallback=None)
        commit  = config.get('SIM_CONFIG', 'commit', fallback=None)

        info = {
            'version' : version,
            'seed'    : seed,
            'factor'  : factor,
            'template': template,
            'status'  : status,
            'nodes'   : nodes,
            'preparation_time': preparation_time, 
            'shear' : shear,
            'nside' : nside, 
            'commit' : commit
        }

        with open(f'{path}/sim_info.json', 'w') as json_file:
            json.dump(info, json_file)


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
    @classmethod
    def prepared(cls):
        prepared = {
            "status" : "prepared"
        }
        return ["Prepared",prepared]
    
    @classmethod
    def crashed(cls):
        crashed = {
            "status" : ["crashed","crashed on shear data computation"]
        }
        return ["Crashed",crashed]

    @classmethod
    def running(cls):
        running = {
            "status" : ["running","running shear data computation"]
        }
        return ["Running",running]
    
    @classmethod
    def done(cls):
        done = {
            "status" : "done"
        }
        return ["Done", done]

    @classmethod
    def filters(cls):
        return [cls.prepared(),cls.crashed(),cls.running(),cls.done()]