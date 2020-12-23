from CoLoRe_analysis import file_manager


def main():
    sims_path       = '/global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/javier/'
    analysis_path   = '/global/cscratch1/sd/cramirez/CoLoRe_CCL/analysis' 
    extra_info = {
        'made_by': 'javier'
    }

    file_manager.FileManager.import_simulations(sims_path, analysis_path, extra_info)


if __name__ == '__main__':
    main()
