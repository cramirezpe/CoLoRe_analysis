#!/usr/bin/env python3

'''
    Script to make pseudo-Cls plots from two different simulations.

'''
import argparse
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

from CoLoRe_analysis import sims_reader, plots, ccl_reader


def getArgs():
    parser = argparse.ArgumentParser(description="Compare Cls plots from multiple simulations")
    parser.add_argument('--sims', required=True, nargs='+', type=str, help='Path to simulations')
    parser.add_argument('--sims-labels', required=False, default=None, nargs='+', type=str, help='Sims labels for plots')
    parser.add_argument('--sims-colors', required=False, default=None, nargs='+', type=str, help='Colors in the plots for the previous simulations (matplotlib color naming, e.g: b, r, g, k)')
    parser.add_argument('--rebin', required=False, default=None, type=int, help='Rebin size for plots')
   
    parser.add_argument("--source",       required=False, type=int, default=1, help="Sources to be computed")
    parser.add_argument("--nside",        required=False, type=int , default=1024 , help="nside to use ")
    parser.add_argument("--zbins",        required=False, type=float, nargs='+', default=[-10,0.82,1000] , help="defines the binning in redshift of the analysis")
    parser.add_argument("--nz_h",         required=False, type=int , default=50 , help="pixelization of the redshift analysis ")
    parser.add_argument("--nz_min",       required=False, type=float , default=0 , help="min redshift for the redshfit analysis")
    parser.add_argument("--nz_max",       required=False, type=float , default=3 , help="max redshift for the redshfit analysis")
    parser.add_argument('--code',         required=False, choices=['anafast','namaster'], default='anafast', help='Which code use to compute the cls')
    parser.add_argument('--skip-bmodes',  action='store_true')
    parser.add_argument('--read-leff', action='store_true', help='Set to True to read leff file for Cls plots x axis')
    parser.add_argument('--l-lim', required=False, type=float, nargs='+', default=[1,1000], help='l limits for Cls plots')

    args = parser.parse_args()
    return args

def main(args=None):
    if args is None:
        args = getArgs()

    options = dict(vars(args))
    options.pop('sims')
    options.pop('sims_labels')
    options.pop('rebin')
    options.pop('sims_colors')
    options.pop('skip_bmodes')
    options.pop('read_leff')
    options.pop('l_lim')

    sims = []
    args.sims_labels = list(range(len(args.sims)))          if args.sims_labels is None else args.sims_labels
    args.sims_colors = ["" for x in range(len(args.sims))]  if args.sims_colors is None else args.sims_colors
    
    for i, (path, label) in enumerate(zip(args.sims,args.sims_labels)):
        sims.append( sims_reader.Sim0404(path, label) )
        sims[i].color = args.sims_colors[i]

    values_names = ['shotnoise','pairs','nz_tot','z_nz','cl_dd_d','cl_dm_d','cl_mm_d','cl_dd_t',
                'cl_dm_t', 'cl_mm_t','cl_md_d','cl_md_t']

    for sim in sims:
        sim.set_ccl_reader()
        x = sim.ccl_reader

        (x.shotnoise, x.pairs, x.nz_tot, x.z_nz, x.cl_dd_d, x.cl_dm_d, x.cl_mm_d, x.cl_dd_t, 
            x.cl_dm_t, x.cl_mm_t, x.cl_md_d, x.cl_md_t) = [x.get_values(value, **options) for value in values_names]

        if args.read_leff:
            x.leff = x.get_values('leff', **options)
        else:
            x.leff = None

    for sim in sims:
        x = sim.ccl_reader

        x.d_values = plots.CCLPlotter([x.cl_dd_d, x.cl_dm_d/2, x.cl_md_d/2, x.cl_mm_d/4], 
                            ['dd', 'dm', 'md', 'mm'], x.pairs, args.nside, leff=x.leff)
        x.t_values = plots.CCLPlotter([x.cl_dd_t, x.cl_dm_t, x.cl_md_t, x.cl_mm_t],
                            ['dd', 'dm', 'md', 'mm'], x.pairs, args.nside, leff=x.leff)
        x.d_values.reshape(args.rebin)
        x.t_values.reshape(args.rebin)
        x.d_values.compute_error_bars()
        x.d_values.reshape_error_bars(args.rebin)

    # FIRST PLOT
    fig = plt.figure(constrained_layout=True, figsize=(20,30))
    gs = matplotlib.gridspec.GridSpec(6,4)

    for i, (p1,p2) in enumerate(sims[0].ccl_reader.pairs):
        p1 = int(p1)
        p2 = int(p2)
        axs = []
        axs.append(fig.add_subplot(gs[i,0]))
        axs.append(fig.add_subplot(gs[i,1]))
        axs.append(fig.add_subplot(gs[i,2]))
        axs.append(fig.add_subplot(gs[i,3]))

        for j, (x, ax) in enumerate( zip(('dd','dm','md','mm'), axs) ):
            a, b = x[0], x[1]
            ax.set_title(f'{a}-{p1} {b}-{p2}')

            msk = sims[0].ccl_reader.d_values.l < sims[0].ccl_reader.d_values.nside
            l = sims[0].ccl_reader.d_values.l[msk]

            if p1 == p2 and x=='dd':
                for sim in sims:
                    sim.ccl_reader.nl = sim.ccl_reader.shotnoise[p1]
                    ax.plot(l, sim.ccl_reader.nl*np.ones_like( sim.ccl_reader.d_values.l[msk] ),
                        sim.color+'--', label=f'Shot noise {str(sim)}')
            else:
                for sim in sims:
                    sim.ccl_reader.nl = 0

            for i, sim in enumerate(sims):
                sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk) - sim.ccl_reader.nl
                sim.clt = sim.ccl_reader.t_values.get_values(a, b, p1, p2, msk)
                sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)

                delta = (l[1]-l[0])*i/len(sims)*0.5
                
                ax.errorbar(l+delta, sim.cl*l, yerr=sim.err, fmt=sim.color+'.', label=f'Sim {str(sim)}', lw=0.5, alpha=0.5)
                ax.plot(l+delta, sim.clt*l, sim.color+'-', lw=0.5, label=f'Prediction {str(sim)}')

            ax.set_xlabel(r'$\ell$', fontsize=15)
            ax.set_ylabel(r'$\ell\,C_\ell$', fontsize=15)
            ax.set_xlim(args.l_lim[0], args.l_lim[1])
            ax.legend()
            ax.set_yscale('log')
            ax.set_xscale('log')
    plt.tight_layout()
    plt.show()

    # SECOND PLOT
    fig = plt.figure(constrained_layout=True, figsize=(20,30)) 
    gs = matplotlib.gridspec.GridSpec(6,4)

    for i, (p1,p2) in enumerate(sims[0].ccl_reader.pairs):
        p1 = int(p1)
        p2 = int(p2)
        axs = []
        axs.append(fig.add_subplot(gs[i,0]))
        axs.append(fig.add_subplot(gs[i,1]))
        axs.append(fig.add_subplot(gs[i,2]))
        axs.append(fig.add_subplot(gs[i,3]))

        for j, (x, ax) in enumerate( zip(('dd','dm','md','mm'), axs) ):
            a, b = x[0], x[1]
            ax.set_title(f'{a}-{p1} {b}-{p2}')

            msk = sims[0].ccl_reader.d_values.l < 2*sims[0].ccl_reader.d_values.nside
            y_lim_msk = sims[0].ccl_reader.d_values.l<750
            l = sims[0].ccl_reader.d_values.l[msk]
            y_max = y_min = 0

            if p1 == p2 and x=='dd':
                for sim in sims:
                    sim.ccl_reader.nl = sim.ccl_reader.shotnoise[p1]
                    ax.plot(l, sim.ccl_reader.nl*np.ones_like( sim.ccl_reader.d_values.l[msk] ),
                        sim.color+'--', label=f'Shot noise {str(sim)}')
            else:
                for sim in sims:
                    sim.ccl_reader.nl = 0


            for i, sim in enumerate(sims):
                sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk) - sim.ccl_reader.nl
                sim.clt = sim.ccl_reader.t_values.get_values(a, b, p1, p2, msk)
                sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)

                high_value_masked_for_ylim  = (sim.ccl_reader.d_values.get_values(a, b, p1, p2, y_lim_msk) - sim.ccl_reader.nl + sim.ccl_reader.d_values.get_errors(a, b, p1, p2, y_lim_msk))/sim.ccl_reader.t_values.get_values(a, b, p1, p2, y_lim_msk) -1 
                low_value_masked_for_ylim    = (sim.ccl_reader.d_values.get_values(a, b, p1, p2, y_lim_msk) - sim.ccl_reader.nl - sim.ccl_reader.d_values.get_errors(a, b, p1, p2, y_lim_msk))/sim.ccl_reader.t_values.get_values(a, b, p1, p2, y_lim_msk) -1
                y_max = max( y_max, np.max(high_value_masked_for_ylim) )
                y_min = min( y_min, np.min(low_value_masked_for_ylim) )

                delta = (l[1]-l[0])*i/len(sims)*0.5
                
                ax.errorbar(l+delta, sim.cl/sim.clt - 1, yerr=sim.err/sim.clt, fmt=sim.color+'.', label=f'Sim {str(sim)}/pred', lw=0.5)
            
            ax.plot(l,np.zeros_like(l),'k-', lw=0.8)
            ax.set_xlabel(r'$\ell$', fontsize=15)
            ax.set_ylabel(r'$C_\ell$', fontsize=15)
            ax.set_ylim(y_min, y_max)  
            ax.set_xlim(args.l_lim[0], args.l_lim[1])
            ax.set_xscale('log')
            ax.legend()
    plt.tight_layout()
    plt.show()

    if not args.skip_bmodes:
        b_values_names = ['cl_bb_d','cl_mb_d','cl_db_d']

        for sim in sims:
            (x.cl_bb_d, x.cl_mb_d, x.cl_db_d) = [x.get_values(value, **options) for value in b_values_names]
        # B-MODES PLOT
        for sim in sims:
            x = sim.ccl_reader
            x.d_values = plots.CCLPlotter([x.cl_bb_d, x.cl_mb_d, x.cl_db_d, x.cl_dd_d, x.cl_mm_d], 
                                    ['bb','mb','db','dd','mm'],  x.pairs, args.nside)

            x.d_values.reshape(args.rebin)
            x.d_values.compute_error_bars()
            x.d_values.reshape_error_bars(args.rebin)

        fig = plt.figure(constrained_layout=True, figsize=(20,30))
        gs = matplotlib.gridspec.GridSpec(6,3)

        for i, (p1,p2) in enumerate(sims[0].ccl_reader.pairs):
            p1 = int(p1)
            p2 = int(p2)
            axs = []
            axs.append(fig.add_subplot(gs[i,0]))
            axs.append(fig.add_subplot(gs[i,1]))
            axs.append(fig.add_subplot(gs[i,2]))

            for j, (x,ax) in enumerate( zip(('bb','mb','db'), axs) ):
                a, b = x[0], x[1]
                ax.set_title(f'{a}-{p1} {b}-{p2}')

                msk = sims[0].ccl_reader.d_values.l<2*sims[0].ccl_reader.d_values.nside
                l = sims[0].ccl_reader.d_values.l[msk]

                for i, sim in enumerate(sims):
                    sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk)
                    sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)
                    
                    delta = (l[1]-l[0])*i/len(sims)*0.5
                    ax.errorbar(l+delta, sim.cl*l, yerr=sim.err, fmt=sim.color+'.', label=f'Sim {str(sim)}')
                ax.plot(l, np.zeros_like(l), 'k-', label='Prediction')
                ax.set_xlabel(r'$\ell$', fontsize=15)
                ax.set_ylabel(r'$\ell\,C_ell$', fontsize=15)
                ax.set_xlim(args.l_lim[0], args.l_lim[1])
                ax.set_xscale('log')
                ax.legend()
        plt.tight_layout()
        plt.show()

    return


if __name__ == '__main__':
    main()