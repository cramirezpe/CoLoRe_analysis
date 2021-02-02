'''
    Module built to compute the data needed to make the CLs analysis comparing with theoretical expectations. 

    It can be imported as a module or used as script.
'''

import argparse
import io
import json
import logging
import os
import sys
import warnings
from contextlib import contextmanager
from datetime import datetime
from itertools import combinations_with_replacement

import healpy as hp
import numpy as np
import pyccl as ccl
import pymaster as nmt
from astropy.io import fits

from CoLoRe_analysis import sims_reader
from CoLoRe_analysis.debug_tools import Stopwatch

log = logging.getLogger(__name__)
h = 0.7



def getArgs(): #pragma: no cover
    parser = argparse.ArgumentParser(description="Save values to compute CCL test into .dat files")

    io_args = parser.add_argument_group('io')
    io_args.add_argument("--input", required=True, type=str, help="Path of ColoRe run")
    io_args.add_argument("--output", required=True, type=str, default=None, help="Path for output files")
    io_args.add_argument("--param", required=True, type=str, help="Path of ColoRe param.cfg file")
    io_args.add_argument("--source",       required=False, type=int, default=1, help="Sources to be computed")
    io_args.add_argument("--max_files",    required=False, type=int, default=None , help="number of srcs files to consider (default: None, consider all the files)")
    io_args.add_argument("--update_INFO_files", action='store_true', help='Update json files when searching for results')

    run_args = parser.add_argument_group('run')
    run_args.add_argument("--nside",        required=False, type=int , default=1024 , help="nside to use ")
    run_args.add_argument("--rsd",          action='store_true', help='Apply RSD to objects')
    run_args.add_argument("--downsampling", required=False, type=float , default=1 , help="downsampling to apply to the data")
    run_args.add_argument("--zbins",        required=False, type=float, nargs='+', default=[0,0.15,1] , help="defines the binning in redshift of the analysis")
    run_args.add_argument("--nz_h",         required=False, type=int , default=50 , help="pixelization of the redshift analysis ")
    run_args.add_argument("--nz_min",       required=False, type=float , default=0 , help="min redshift for the redshfit analysis")
    run_args.add_argument("--nz_max",       required=False, type=float , default=None , help="max redshift for the redshfit analysis")
    run_args.add_argument("--sigz",         required=False, type=float, default=0.03, help='Gaussian sigma applied to generate photo-z')
    run_args.add_argument('--code',         required=False, choices=['anafast','namaster'], default='namaster', help='Which code use to compute the cls')
    run_args.add_argument('--log',          required=False, default=None, help='Setup logging, use levelname as string  (Set to INFO to see script timings)')
    run_args.add_argument('--skip-lensing', action='store_true', help='Skip lensing components')
    run_args.add_argument('--skip-theory',  action='store_true', help='Skip theory computations')
    run_args.add_argument('--skip-data',    action='store_true', help='Skip computing cls from data')

    args = parser.parse_args()
    return args

def main(args=None):
    if args is None:
        args = getArgs()

    path   = args.input
    output  = args.output

    options = dict(vars(args))
    options.pop('input')
    options.pop('output')
    options.pop('param')
    options.pop('log')
    options.pop('update_INFO_files')

    if args.log is not None:
        level = logging.getLevelName(args.log)
        logging.basicConfig(level=level)

    if not os.path.isfile(args.param):
        raise FileNotFoundError('Param cfg not found')

    if os.path.isdir(output):
        if not os.path.isfile(output + '/sim_info.json'):
            raise FileNotFoundError("Output path already exists but doesn't contain a sim_info.json file. Select an empty output")
        elif sims_reader.Sim0404(output).location != path:
            raise ValueError("Output path already exists with a different simulation analysis")
        else:
            sim = sims_reader.Sim0404(output)
            sim.set_ccl_reader(args.update_INFO_files)
            f1 = sys.stdin 
            f = io.StringIO('y') # "mocking" input to force a yes
            sys.stdin = f
            _ = sim.ccl_reader.get_values('cl_mm_t', **options)
            sys.stdin = f1
    else:
        os.makedirs(output)
        info = {
            'version': None,
            'factor': 1,
            'template': None,
            'status': 'done',
            'nodes': None,
            'path': args.input,
            'preparation_time': datetime.today().strftime('%Y%m%d_%H%M%S'),
            'commit': None
        }

        with open(output + '/sim_info.json', 'w') as json_file:
            json.dump(info, json_file, indent=4, sort_keys=True)

        f1 = sys.stdin
        f = io.StringIO(args.param)
        sys.stdin = f
        sim = sims_reader.Sim0404(output)

        sim.set_ccl_reader(args.update_INFO_files)
        f = io.StringIO('y')
        sys.stdin = f
        sim.ccl_reader.get_values('cl_mm_t', **options)
        sys.stdin = f1

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

def compute_data(sim_path, analysis_path, source=1, nside=128, max_files=None, downsampling=1, zbins=[-1,0.15,1], nz_h = 50, nz_min=0, nz_max=None, sigz=0.03, skip_lensing=False, skip_theory=False, skip_data=False, code=None, rsd=False):
    ''' Method to compute the values needed for CCL test plots.
    
    Args:
        sim_path (str): Path where the CoLoRe simulation is located.
        source (int, optional): Source of which to compute data (default: 1)
        output_path (str, optional): Output where to save the data (default: { sim_path }/ccl_data/{ datetime.now() }/)
    '''
    id_ = datetime.today().strftime('%Y%m%d_%H%M%S')
    output_path = analysis_path + f"/ccl_data/{ id_ }"
    os.makedirs(output_path, exist_ok = True)
    
    log.debug(f'Computing data for:\nsim_path: { sim_path }\nsource: { source }\noutput_path: { output_path }')
    timer = Stopwatch()
    
    log.info('Reading maps from CoLoRe output')
    maps = get_maps(sim_path, source, nside, max_files, downsampling, zbins, nz_h, nz_min, nz_max, sigz, skip_lensing, rsd)
    log.info(f'\t Relative time: {timer.lap()}\n')

    if not skip_theory:
        log.info('Computing theoretical values using pyccl')
        if code == 'namaster':
            t_values = get_cls_pred(sim_path, maps, nside, skip_lensing)
        else:
            t_values = get_cls_pred(sim_path, maps, nside, skip_lensing, bin_cell=False)
        log.info(f'\t Relative time: {timer.lap()}\n')
    else:
        t_values = dict()

    if not skip_data:
        if code == 'namaster':
            d_values = get_cls_namaster(maps, nside, skip_lensing)
        elif code == 'anafast':
            d_values = get_cls_anafast(maps, nside, skip_lensing)
        else:
            raise ValueError('Not a valid code name, enter namaster/anafast')
        log.info(f'\t Relative time: {timer.lap()}\n')
    else:
        d_values = dict()
    
    log.info(f'TOTAL time: {timer.full()}')

    log.info(f'\t Writing data to files')
    values = {**t_values, **d_values, **maps}
    for name, value in values.items():
        savetofile( output_path, (value,), (name,) )

    info = {
        'id'            : id_,
        'source'        : source,
        'nside'         : nside,
        'max_files'     : max_files,
        'downsampling'  : downsampling,
        'zbins'         : zbins,
        'nz_h'          : nz_h,
        'nz_min'        : nz_min,
        'nz_max'        : nz_max,
        'code'          : code,
        'sigz'          : sigz,
        'skip_theory'   : skip_theory,
        'skip_data'     : skip_data,
        'skip_lensing'  : skip_lensing,
        'rsd'           : rsd
    }

    with open(output_path + '/INFO.json','w') as outfile:
        json.dump(info, outfile, indent=4, sort_keys=True)

def get_maps(sim_path, source=1, nside=128, max_files=None, downsampling=1, zbins=[-1, 0.15, 1], nz_h=50, nz_min=0, nz_max=None, sigz=0.03, skip_lensing=False, rsd=False):
    ''' Function to get maps from CoLoRe output files:
    
    Args:
        sim_path (str): Path where the CoLoRe simulation is located.
        source (int, optional): Source from which to compute data (default: 1)
        nside (int, optional): nside to use (default:128)
        max_files (int, optional): number of srcs files to consider (default: None, consider all the files) 
        downsampling (float, optional): downsampling to apply to the data (from 0 to 1) (default: 1)
        zbins (array of floats, optional): defines the binning in redshift of the data analysis (default: [0,0.15,0.5])
        nz_h (int, optional): pixelization of the redshift analysis (default: 50)
        nz_min (float, optional): min redshift for the N(z) histogram (default: 0)
        nz_max (float, optional): max redshift for the N(z) histogram (default: None (set to the max value in zbins))
        sigz (float, optional): Gaussian sigma applied to generate photo-z.
        skip_lensing (bool, optional): Skip lensing components
    
    '''

    nside = nside
    npix = hp.nside2npix(nside)

    nbins   = len(zbins) - 1
    pairs   = list(combinations_with_replacement(range(nbins), r=2))

    # This will contain the N(z) of the different bins
    nz_tot = np.zeros([nbins, nz_h])
    nz_max = nz_max if nz_max is not None else zbins[-1]

    # These will be the density and ellipticity maps
    dmap = np.zeros([nbins, npix])
    nmap = np.zeros([nbins, npix])
    if not skip_lensing:
        e1map = np.zeros([nbins, npix])
        e2map = np.zeros([nbins, npix])

    # Now we loop over all source files
    if max_files is None:
        file_limit = False
    else:
        file_limit = True

    ifile = 0

    log.info('Reading output files...')
    while os.path.isfile(sim_path + '/out_srcs_s1_%d.fits' % ifile) and ( (not file_limit) or ifile <= max_files):
        file_watch = Stopwatch()
        log.info('Reading file: ' + str(ifile))
        hdulist = fits.open(sim_path + '/out_srcs_s1_%d.fits' % ifile)
        d = hdulist[1].data
        n_g = len(d)

        # Generate random photo-z
        z_photo = d['Z_COSMO'] + sigz*(1+d['Z_COSMO'])*np.random.randn(n_g)

        if downsampling != 1: 
            d_mask = np.random.random(len(z_photo)) < downsampling #pylint: disable=no-member
        else:
            d_mask = np.full(len(z_photo), True, dtype=bool)

        masks = []
        for i in range(nbins):
            masks.append( (zbins[i] <= z_photo) & (z_photo < zbins[i+1]) )
        
        masks = [(mask & d_mask) for mask in masks]  # applying downsampling here

        # For each bin, add to the number and ellipticity maps
        for ibin, msk in enumerate( masks ):
            dd = d[msk]

            pix = hp.ang2pix(nside,
                            np.radians(90-dd['DEC']),
                            np.radians(dd['RA']))
            n = np.bincount(pix, minlength=npix)
            if not skip_lensing:
                e1 = np.bincount(pix, minlength=npix, weights=dd['E1'])
                e2 = np.bincount(pix, minlength=npix, weights=dd['E2'])
                e1map[ibin, :] += e1
                e2map[ibin, :] += e2
            nmap[ibin, :] += n

            # Add also to N(z)
            nz, z_edges = np.histogram(dd['Z_COSMO'], bins=nz_h,
                                    range=[nz_min, nz_max])
            nz_tot[ibin, :] += nz
        ifile += 1
        log.info(f'File {ifile} processed. Time ellapsed: {file_watch.full()} s')

    # Midpoint of N(z) histogram
    z_nz = 0.5*(z_edges[1:] + z_edges[:-1])
    log.info('Computing maps...')
    # Compute <e> map and overdensity map
    # Compute also shot noise level
    shotnoise = np.zeros(nbins)
    for ib in range(nbins):
        ndens = (np.sum(nmap[ib])+0.0)/(4*np.pi)
        shotnoise[ib] = 1./ndens
        if not skip_lensing:
            e1map[ib, :] = e1map[ib]/nmap[ib]
            e1map[ib, nmap[ib] <= 0] = 0
            e2map[ib, :] = e2map[ib]/nmap[ib]
            e2map[ib, nmap[ib] <= 0] = 0
        dmap[ib, :] = (nmap[ib, :] + 0.0) / np.mean(nmap[ib] + 0.0) - 1

    maps = {
        'shotnoise':    shotnoise,
        'dmap':         dmap,
        'nmap':         nmap,
        'nz_tot':       nz_tot,
        'z_nz':         z_nz,
        'zbins':        zbins,
        'pairs':        pairs
    }

    if not skip_lensing:
        maps['e1map'] = e1map
        maps['e2map'] = e2map

    return maps

def get_cls_pred(sim_path, maps, nside, skip_lensing=False, bin_cell=True):
    zs =        []
    pks_dd =    []
    z_pk   =    0.
    
    zbins   = maps['zbins'] 
    z_nz    = maps['z_nz']
    nz_tot  = maps['nz_tot']
    nbins = len(zbins) - 1
    pairs   = maps['pairs']

    if not skip_lensing:
        pks_dm = []
        pks_mm = []

    log.info('Reading pk files...')
    while os.path.isfile(sim_path + "/out_pk_srcs_pop0_z%.3lf.txt" % z_pk):
        ks, pdd, pdm, pmm = np.loadtxt(sim_path + "/out_pk_srcs_pop0_z%.3lf.txt" % z_pk, unpack=True)
        # The delta-delta prediction involves some Fourier transforms that make it unstable
        # at high-k, so we just set it to zero.
        pdd[pmm<1E-30] = 0
        pdd[pdd<0] = 0
        pdd[ks>1.9] = 0
        pdd[ks<3E-4] = 0
        pks_dd.append(pdd)
        if not skip_lensing:
            pks_dm.append(pdm)
            pks_mm.append(pmm)
        zs.append(z_pk)
        z_pk += 0.1

    # Reverse order (because CCL needs increasing scale factor - not redshift).
    # Also, CCL uses non-h units.
    zs = np.array(zs)[::-1]
    ks = np.array(ks) * h
    pks_dd = np.array(pks_dd)[::-1, :] / h**3
    if not skip_lensing:
        pks_dm = np.array(pks_dm)[::-1, :] / h**3
        pks_mm = np.array(pks_mm)[::-1, :] / h**3

    log.info('Creating CCL structures...')
    # Create CCL P(k) structures
    cosmo = ccl.Cosmology(Omega_c=0.25, Omega_b=0.05, h=h, n_s=0.96, sigma8=0.8)
    pk2d_dd = ccl.Pk2D(a_arr=1./(1+zs), lk_arr=np.log(ks), pk_arr=pks_dd,
                    is_logp=False, extrap_order_hik=0, extrap_order_lok=0)
    if not skip_lensing:
        pk2d_dm = ccl.Pk2D(a_arr=1./(1+zs), lk_arr=np.log(ks), pk_arr=pks_dm,
                        is_logp=False, extrap_order_hik=0, extrap_order_lok=0)
        pk2d_mm = ccl.Pk2D(a_arr=1./(1+zs), lk_arr=np.log(ks), pk_arr=pks_mm,
                        is_logp=False, extrap_order_hik=0, extrap_order_lok=0)
    # These can be evaluated as follows:
    pk2d_dd.eval(k=0.1, a=1/(1+0.2), cosmo=cosmo) # This was printed by David!
    if not skip_lensing:
        pk2d_dm.eval(k=0.1, a=1/(1+0.2), cosmo=cosmo)
        pk2d_mm.eval(k=0.1, a=1/(1+0.2), cosmo=cosmo)

    # Create a number counts and a weak lensing tracer for each of the bins
    tr_d = [ccl.NumberCountsTracer(cosmo, False, (z_nz, nz_tot[i]), bias=(z_nz, np.ones_like(z_nz)))
            for i in range(nbins)]
    if not skip_lensing:
        tr_l = [ccl.WeakLensingTracer(cosmo, (z_nz, nz_tot[i])) for i in range(nbins)]
    
    log.info('Computing CCL power spectra')
    larr = np.arange(3*nside)

    def get_cl_t(t1, t2, pk):
        try:
            cl = ccl.angular_cl(cosmo, t1, t2, larr, p_of_k_a=pk)
        except:
            print('SHIT')
            cl = np.zeros_like(larr)
        if bin_cell:    
            bn = nmt.NmtBin(nside, nlb=4)
            return bn.bin_cell(np.array([cl]))[0]
        else:
            return cl

    cl_dd_t = []
    for p1, p2 in pairs:
        cl_dd_t.append( get_cl_t(tr_d[p1], tr_d[p2], pk2d_dd) )
    cl_dd_t = np.asarray( cl_dd_t )
    if not skip_lensing:
        cl_dm_t = []
        cl_md_t = []
        cl_mm_t = []
        for p1, p2 in pairs:
            cl_dm_t.append( get_cl_t(tr_d[p1], tr_l[p2], pk2d_dm) )
            cl_mm_t.append( get_cl_t(tr_l[p1], tr_l[p2], pk2d_mm) )
            cl_md_t.append( get_cl_t(tr_d[p2], tr_l[p1], pk2d_dm) )

        cl_dm_t, cl_mm_t, cl_md_t = list( map(np.asarray, (cl_dm_t, cl_mm_t, cl_md_t)) )
    
    values_t_d = {
        'cl_dd_t':  cl_dd_t
    }

    if not skip_lensing:
        values_t_lensing = {
            'cl_dm_t':  cl_dm_t,
            'cl_md_t':  cl_md_t,
            'cl_mm_t':  cl_mm_t
        }
        return {**values_t_d, **values_t_lensing}
    else:
        return values_t_d

def get_cls_namaster(maps, nside, skip_lensing=False):
    log.info('Computing cls from data using namaster')

    zbins   = maps['zbins']    
    nbins   = len(zbins) - 1
    pairs   = maps['pairs']
    npix = hp.nside2npix(nside)

    bn = nmt.NmtBin(nside, nlb=4)
    leff = bn.get_effective_ells()

    dmap = maps['dmap']
    nmap = maps['nmap']
    f_g = []
    for ib in range(nbins):
        f_g.append( nmt.NmtField(np.ones(npix), [dmap[ib]], n_iter=0) )
    
    if not skip_lensing:
        e1map = maps['e1map']
        e2map = maps['e2map']
        f_l = []
        for ib in range(nbins):
            f_l.append( nmt.NmtField(nmap[ib], [e1map[ib], e2map[ib]], n_iter=0) )
        
    def get_cl_d(f1, f2):
        w = nmt.NmtWorkspace()
        w.compute_coupling_matrix(f1, f2, bn)
        cl = w.decouple_cell(nmt.compute_coupled_cell(f1, f2))[0]
        return cl

    cl_dd_d = []
    for i, (p1, p2) in enumerate(pairs):
        cl_dd_d.append( get_cl_d(f_g[p1], f_g[p2]) )
    
    if not skip_lensing:
        cl_dm_d = []
        cl_mm_d = []
        cl_md_d = []
        for i, (p1, p2) in enumerate(pairs):
            cl_mm_d.append( get_cl_d(f_l[p1], f_l[p2]) )
            cl_dm_d.append( get_cl_d(f_g[p1], f_l[p2]) )
            if p1 == p2:
                cl_md_d.append( cl_dm_d[i] )
            else:
                cl_md_d.append( get_cl_d(f_l[p1], f_g[p2]) )

    values_cls_d = {
        'cl_dd_d':      cl_dd_d,
        'leff':         leff
    }

    if not skip_lensing:
        values_cls_lens = {
            'cl_dm_d':  cl_dm_d,
            'cl_md_d':  cl_md_d,
            'cl_mm_d':  cl_mm_d
        }
        return {**values_cls_d, **values_cls_lens} 
    else:
        return values_cls_d

def get_cls_anafast(maps, nside, skip_lensing=False):
    log.info('Computing cls from data using anafast')
  
    pairs   = maps['pairs']

    dmap = maps['dmap']

    if not skip_lensing:
        e1map = maps['e1map']
        e2map = maps['e2map'] 

        d_values = np.array([hp.anafast(np.asarray([dmap[p1],e1map[p1],e2map[p1]]),np.asarray([dmap[p2],e1map[p2],e2map[p2]]), pol=True) for p1,p2 in pairs])
        cl_md_d = np.copy(d_values[:,3])

        for i, (p1, p2) in enumerate(pairs):
            if p1 != p2:
                cl_md_d[i] = np.array(hp.anafast(np.asarray([dmap[p2],e1map[p2],e2map[p2]]), np.asarray([dmap[p1],e1map[p1],e2map[p1]])))[3]
            
        values_cls_d = {
            'cl_dd_d':  d_values[:,0],
            'cl_dm_d':  d_values[:,3],
            'cl_md_d':  cl_md_d,
            'cl_mm_d':  d_values[:,1],
            'cl_bb_d':  d_values[:,2],
            'cl_mb_d':  d_values[:,4],
            'cl_db_d':  d_values[:,5]
        }

        cl_dd_d_unlens = np.array([ hp.anafast(np.asarray(dmap[p1]), np.asarray(dmap[p2]), pol=True) for p1,p2 in pairs])

        np.testing.assert_almost_equal(d_values[:,0], cl_dd_d_unlens)
    else:
        cl_dd_d  = np.array([ hp.anafast(np.asarray(dmap[p1]), np.asarray(dmap[p2]), pol=True) for p1,p2 in pairs])

        values_cls_d = {
            'cl_dd_d':  cl_dd_d
        }

    return values_cls_d
  
if __name__ == '__main__': #pragma: no cover
    main()
