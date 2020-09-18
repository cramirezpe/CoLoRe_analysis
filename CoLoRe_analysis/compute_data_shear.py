## This code will compute strings for a given simulation (path should point to the path where sim_info is locatded

import argparse
import logging
import os
import sys
import warnings
from contextlib import contextmanager

import healpy as hp
import numpy as np
from astropy.io import fits

log = logging.getLogger(__name__)


###############################################################################
### Functions
###############################################################################
def savetofile(location,variables,variables_names):
    for i,variable in enumerate(variables):
        np.savetxt( location + '/' + variables_names[i] + '.dat', variable)
    return
    
@contextmanager   # Code to avoid output temporarily
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
        
def fxn():
    warnings.warn("deprecrated", DeprecationWarning)

def compute_data_shear(path,source=1, do_cls=False, do_kappa=False, minz=None,maxz=None, output_path=None):
    if not output_path:
        output_path = path + f'/shear_data/source_{ source }'
    os.makedirs(output_path, exist_ok=True)
    
    log.debug(f'path: { path }, source: { source }, do_cls: { do_cls }, do_kapa: { do_kappa }, minz: { minz }, maxz: { maxz }, output_path: { output_path }')

    minz = 0 if minz==None else minz
    maxz = 2000 if maxz==None else maxz

    with suppress_stdout():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fxn()
            nside = 512
            npix = hp.nside2npix(nside)

            # Analyze sources
            ifile = 0
            nmap = np.zeros(hp.nside2npix(nside))
            e1map = np.zeros(hp.nside2npix(nside))
            e2map = np.zeros(hp.nside2npix(nside))

            while os.path.isfile(path+f'/out_srcs_s{ source }_{ ifile }.fits'):
                hdulist = fits.open(path+f'/out_srcs_s{ source }_{ ifile }.fits')
                tbdata = hdulist[1].data
                mask = (tbdata['Z_COSMO'] >= minz) & (tbdata['Z_COSMO'] < maxz)
                tbdata = tbdata[mask]

                pix = hp.ang2pix(nside,
                                np.radians(90-tbdata['DEC']),
                                np.radians(tbdata['RA']))
                n = np.bincount(pix, minlength=npix)
                e1 = np.bincount(pix, minlength=npix, weights=tbdata['E1'])
                e2 = np.bincount(pix, minlength=npix, weights=tbdata['E2'])
                nmap += n
                e1map += e1
                e2map += e2
                ifile += 1
                hdulist.close()

            ndens = (np.sum(nmap)+0.0)/(4*np.pi)
            mp_e1 = e1map/nmap
            mp_e1[nmap <= 0] = 0
            mp_e2 = e2map / nmap
            mp_e2[nmap <= 0] = 0
            mp_d = (nmap + 0.0) / np.mean(nmap + 0.0) - 1
            mp_db, mp_E, mp_B = hp.alm2map(hp.map2alm(np.array([mp_d, mp_e1, mp_e2]),
                                                    pol=True),
                                        pol=False,
                                        nside=nside)
        
    savetofile(output_path,[mp_e1,mp_e2,mp_d,mp_db,mp_E,mp_B], ["mp_e1","mp_e2","mp_d","mp_db","mp_E","mp_B"])

    if do_cls:
        with suppress_stdout():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fxn()
            # lt, cls_dd = np.loadtxt(path+'/pred_lj/outlj_cl_dd.txt',
            #                         unpack=True)
            # lt, clt_dl = np.loadtxt(path+'/pred_lj/outlj_cl_d1l2.txt',
            #                         unpack=True)
            # lt, clt_ll = np.loadtxt(path+'/pred_lj/outlj_cl_ll.txt',
            #                         unpack=True)
            # lt, clt_kd = np.loadtxt(path+'/pred_lj/outlj_cl_dc.txt',
            #                         unpack=True)
            # lt, clt_kk = np.loadtxt(path+'/pred_lj/outlj_cl_cc.txt',
            #                         unpack=True)
            # lt, clt_id = np.loadtxt(path+'/pred_lj/outlj_cl_di.txt',
            #                         unpack=True)
            # lt, clt_ii = np.loadtxt(path+'/pred_lj/outlj_cl_ii.txt',
            #                         unpack=True)
            # cln_dd = np.ones_like(lt) / ndens
            # clt_dd = cls_dd + cln_dd
            d = hp.anafast(np.array([mp_d, mp_e1, mp_e2]), pol=True)
            cld_dd, cld_ee, cld_bb, cld_de, cld_eb, cld_db = d
            ld = np.arange(len(cld_dd))
            
        savetofile(output_path, [cld_dd,cld_ee,cld_bb,cld_de,cld_eb,cld_db,ld], ["cld_dd","cld_ee","cld_bb","cld_de","cld_eb","cld_db","ld"] )
        
    if do_kappa:
        # Analyze kappa
        with suppress_stdout():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fxn()
                mp_k = hp.read_map(path+"/out_kappa_z000.fits")
                if do_cls:
                    cld_kk = hp.anafast(mp_k)
                    ld = np.arange(len(cld_kk))
                    cld_kd = hp.anafast(mp_k, map2=mp_d)
                    savetofile(output_path, [cld_kk, cld_kd], ["cld_kk", "cld_kd"] )
        savetofile(output_path, [mp_k], ["mp_k"] )
    
if __name__ == "__main__": #pragma: no cover
    parser = argparse.ArgumentParser(description="Save useful parameters into .dat files")
    parser.add_argument("-p","--path", required=True, type=str, help="Path of CoLoRe run")
    parser.add_argument("-c","--cls", action='store_true', help="Compute cls (it should be provided by simulation")
    parser.add_argument("-k","--kappa", action='store_true', help="Analyse kappa")
    parser.add_argument("-s","--source", required=False, type=int, default=1, help="Sources to be computed")
    parser.add_argument("-o","--output", required=False, type=str, default=None, help="Path for output files")
    parser.add_argument("-mz","--minz", required=False, type=float, default=None, help="min. redshift")
    parser.add_argument("-Mz","--maxz", required=False, type=float, default=None, help="max. redshift")

    args = parser.parse_args()

    path    = args.path
    do_cls  = args.cls
    do_kappa= args.kappa
    source  = args.source
    minz    = args.minz
    maxz    = args.maxz 
    output  = args.output
   
    compute_data_shear(path, source, do_cls, do_kappa, minz, maxz, output)
