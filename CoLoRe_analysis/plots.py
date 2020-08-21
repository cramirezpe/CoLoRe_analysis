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
    def plot(cls,ld, values, ax=None, colors=None, labels=None, alpha=None, mask=None, **kwargs):
        ''' Plotting the cls with defined format.k

        Parameters:
            ld: Angular distance values
            values: 4-dim array containing the following cls: (cld_dd, cld_ee, cld_de, cld_bb)
            labels: Label to use, by default they are the ones corresponding with values
            colors: Colors to use for the values. None for default values.
            alpha: Alpha array to apply to the values. 
            mask: Mask to apply to everything (exclude some values to be plotted)
            kwargs: Additional kw arguments will be sent to the plot function.
        '''
        if not ax: ax = plt.gca()
        if not labels: labels = cls.labels
        if not colors: colors = cls.colors
        if not alpha: alpha = [1,1,1,1]
        if not mask: mask = [True,True,True,True]

        if len(values) != 4:
            raise ValueError('Values should be a 4dim array')

        for i in range(len(values)):
            if not mask[i]: continue
            ax.plot(ld, values[i], colors[i]+'-', label=labels[i],alpha=alpha[i], **kwargs)

        ax.set_xlabel('$\\ell$', fontsize=16)
        ax.set_xlim([2,192])
        ax.legend()
        return

class CCLPlotter():
    '''
        Class to plot CCL values. 
    '''
    def __init__(self, dd, dm, md, mm, pairs, nside):    
        '''
            Args:
                dd: Array with the values of the galaxy galaxy Cls. An array with shape (n. of pairs, 2, 3*nside) is expected.
                dm: Array with the vales of the galaxy matter Cls. An array with shape (n. of pairs, 2, 3*nside) is expected.
                md: Array with the values of the matter galaxy Cls. An array with shape (n. of pairs, 2, 3*nside) is expected.
                mm: Array with the values of matter matter Cls.  An array with shape (n. of pairs, 2, 3*nside) is expected.
                pairs: Pairs used. Array of arrays is expected (e.g: [(0,0),(0,1),(1,0)])
                nside (int): Nside to use.
        '''

        self.raw_values = dict()
        self.raw_values['dd'] = dd
        self.raw_values['dm'] = dm/2
        self.raw_values['md'] = md/2
        self.raw_values['mm'] = mm/4
        
        self.values = dict()
        self.values['dd'] = dd
        self.values['dm'] = dm/2
        self.values['md'] = md/2
        self.values['mm'] = mm/4
        
        self.pairs = pairs
        
        self.nside = nside
        self.larr  = np.arange(3*nside)
        self.l     = np.arange(3*nside)
        
    def compute_error_bars(self):
        '''
            Compute the error bars associated with the Cls. 
        '''
        Dl = self.larr[1]-self.larr[0]
        
        self.raw_errors = dict()

        for name in ('dd','dm','md','mm'):
            self.raw_errors[name] = np.zeros_like(self.raw_values[name])
            for i, (pair1,pair2) in enumerate(self.pairs):
                a, b = name[0], name[1]
                
                self.raw_errors[name][i] = self.get_raw_values(a,a,pair1,pair1)*self.get_raw_values(b,b,pair2,pair2) + self.get_raw_values(a,b,pair1,pair2)**2
                self.raw_errors[name][i] = self.raw_errors[name][i] / (Dl*(2*self.larr+1))
                self.raw_errors[name][i] = np.sqrt(self.raw_errors[name][i])           
                
    def reshape(self, rebin):
        '''
            Reshape the values averaging over the rebinning.

        Args:
            rebin (int): Number of bins to average within.
        '''
        for name in ('dd','dm','md','mm'):
            self.values[name] = np.mean( self.raw_values[name].reshape([3,-1,rebin]), axis=2)
                
        self.l = np.mean( self.larr.reshape([-1,rebin]), axis=1)
                                                         
    
    def reshape_error_bars(self, rebin):
        '''
            Reshape the errors averaging over the rebinning.

        Args:
            rebin (int): Number of bins to average within.
        '''

        self.errors = dict()
        for name in ('dd', 'dm', 'md', 'mm'):
            self.errors[name] = np.mean( self.raw_errors[name].reshape([3,-1,rebin]), axis=2)
            
    def get_raw_values(self, a, b, pair1, pair2):
        '''
        Get the values without rebinning.

        Args:
            a (str): First component (m or d)
            b (str): Second component (m or d)
            pair1 (int): First component region.
            pair2 (int): Second component region.

        Returns:
            Array of length 3*nside with the values without rebinning.
        '''
        return self.raw_values[a+b][ self.get_index(pair1, pair2) ]
            
    def get_values(self,a,b,pair1, pair2):
        '''
        Get the rebinned values

        Args:
            a (str): First component (m or d)
            b (str): Second component (m or d)
            pair1 (int): First component region.
            pair2 (int): Second component region.

        Returns:
            Array of length 3*nside/rebin with the rebinned values.
        '''
        return self.values[a+b][ self.get_index(pair1, pair2) ]
    
    def get_raw_errors(self, a, b, pair1, pair2):
        '''
        Get the errors without rebinning.

        Args:
            a (str): First component (m or d)
            b (str): Second component (m or d)
            pair1 (int): First component region.
            pair2 (int): Second component region.

        Returns:
            Array of length 3*nside with the errors without rebinning.
        '''
        return self.raw_errors[a+b][ self.get_index(pair1, pair2) ]
    
    def get_errors(self, a, b, pair1, pair2):
        '''
        Get the rebinned errors

        Args:
            a (str): First component (m or d)
            b (str): Second component (m or d)
            pair1 (int): First component region.
            pair2 (int): Second component region.

        Returns:
            Array of length 3*nside/rebin with the rebinned errors.
        '''
        return self.errors[a+b][ self.get_index(pair1, pair2) ]
    
    def get_index(self, pair1, pair2):
        ''' Get the index in the pairs array of a given pair:

        Args:
            pair1 (int): First pair region
            pair2 (int): Second pair region

        Returns:
            Index of the element (pair1,pair2) in the pairs array.
        '''
        return np.where((self.pairs == [pair1, pair2]).all(axis=1))[0][0]
