import numpy as np 
import matplotlib.pyplot as plt

class ClsPlotter():
    cld_dd_string = '$\\delta_g\\times\\delta_g$'
    cld_de_string = '$\\gamma^E_g\\times\\delta_g$'
    cld_ee_string = '$\\gamma^E_g\\times\\gamma^E_g$'
    cld_bb_string = '$\\gamma^B_g\\times\\gamma^B_g$'
    cld_eb_string = '$\\gamma^E_g\\times\\gamma^B_g$'
    cld_db_string = '$\\gamma^B_g\\times\\delta_g$'
    cld_kd_string = '$\\kappa-\\delta_g$'
    cld_kk_string = '$\\kappa-\\kappa$'
    
    strings = ['cld_dd','cld_ee','cld_de','cld_bb']
    labels = [cld_dd_string, cld_ee_string,cld_de_string,cld_bb_string]
    colors = ['r','y','c','m']

    @classmethod
    def plot(cls,ld, values, ax=None, colors=None, labels=None, alpha=None,  **kwargs):
        ''' Plotting the cls with defined format.k

        Parameters:
            ld: Angular distance values
            values: 4-dim array containing the following cls: (cld_dd, cld_ee, cld_de, cld_bb)
            labels: Label to use, by default they are the ones corresponding with values
            colors: Colors to use for the values. None for default values.
            kwargs: Additional arguments will be sent to the plot function.
            alpha: Alpha array to apply to the values. 
        '''
        if not ax: ax = plt.gca()
        if not labels: labels = cls.labels
        if not colors: colors = cls.colors
        if not alpha: alpha = [1,1,1,1]

        if len(values) != 4:
            raise ValueError('Values should be a 4dim array')

        for i in range(len(values)):
            ax.plot(ld, values[i], colors[i]+'-', label=labels[i],alpha=alpha[i], **kwargs)

        ax.set_xlabel('$\\ell$', fontsize=16)
        ax.set_xlim([2,192])
        ax.legend()
        return


