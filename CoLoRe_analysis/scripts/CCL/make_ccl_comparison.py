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
    parser.add_argument('--rebin', required=False, default=2**6, type=int, help='Rebin size for plots')
   
    parser.add_argument("--source",       required=False, type=int, default=1, help="Sources to be computed")
    parser.add_argument("--nside",        required=False, type=int , default=1024 , help="nside to use ")
    parser.add_argument("--zbins",        required=False, type=float, nargs='+', default=[-10,0.82,1000] , help="defines the binning in redshift of the analysis")
    parser.add_argument("--nz_h",         required=False, type=int , default=50 , help="pixelization of the redshift analysis ")
    parser.add_argument("--nz_min",       required=False, type=float , default=0 , help="min redshift for the redshfit analysis")
    parser.add_argument("--nz_max",       required=False, type=float , default=3 , help="max redshift for the redshfit analysis")
    parser.add_argument('--code',         required=False, choices=['anafast','namaster'], default='namaster', help='Which code use to compute the cls')

    args = parser.parse_args()
    return args

def main(args=None):
    if args is None:
        args = getArgs()

    options = dict(vars(args))
    options.pop('sims')
    options.pop('sims_labels')
    options.pop('rebin')

    sims = []
    args.sims_labels = list(range(len(args.sims))) if args.sims_labels is None else args.sims_labels
    for path, label in zip(args.sims,args.sims_labels):
        sims.append( sims_reader.Sim0404(path, label) )

    values_names = ['shotnoise','pairs','nz_tot','z_nz','cl_dd_d','cl_dm_d','cl_mm_d','cl_dd_t',
                'cl_dm_t', 'cl_mm_t','cl_md_d','cl_md_t','cl_bb_d','cl_mb_d','cl_db_d']

    for sim in sims:
        sim.set_ccl_reader()
        x = sim.ccl_reader

        (x.shotnoise, x.pairs, x.nz_tot, x.z_nz, x.cl_dd_d, x.cl_dm_d, x.cl_mm_d, x.cl_dd_t, 
            x.cl_dm_t, x.cl_mm_t, x.cl_md_d, x.cl_md_t, x.cl_bb_d, x.cl_mb_d,
            x.cl_db_d) = [x.get_values(value, **options) for value in values_names]

    for sim in sims:
        x = sim.ccl_reader
        x.d_values = plots.CCLPlotter([x.cl_dd_d, x.cl_dm_d/2, x.cl_md_d/2, x.cl_mm_d/4], 
                            ['dd', 'dm', 'md', 'mm'], x.pairs, args.nside)
        x.t_values = plots.CCLPlotter([x.cl_dd_t, x.cl_dm_t, x.cl_md_t, x.cl_mm_t],
                            ['dd', 'dm', 'md', 'mm'], x.pairs, args.nside)
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

            msk = sims[0].ccl_reader.d_values.l < 2*sims[0].ccl_reader.d_values.nside
            l = sims[0].ccl_reader.d_values.l[msk]

            if p1 == p2 and x=='dd':
                for sim in sims:
                    sim.ccl_reader.nl = sim.ccl_reader.shotnoise[p1]
                    ax.plot(l, sim.ccl_reader.nl*np.ones_like( sim.ccl_reader.d_values.l[msk] ),
                        '--', label=f'Shot noise {str(sim)}')
            else:
                for sim in sims:
                    sim.ccl_reader.nl = 0

            for i, sim in enumerate(sims):
                sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk) - sim.ccl_reader.nl
                sim.clt = sim.ccl_reader.t_values.get_values(a, b, p1, p2, msk)
                sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)

                delta = (l[1]-l[0])*i/len(sims)*0.5
                
                ax.errorbar(l+delta, sim.cl, yerr=sim.err, fmt='.', label=f'Sim {str(sim)}', lw=0.5)
                ax.plot(l+delta, sim.clt, lw=0.3, label=f'Prediction {str(sim)}')

            ax.set_xlabel(r'$\ell$', fontsize=15)
            ax.set_ylabel(r'$C_\ell$', fontsize=15)
            ax.legend()
            ax.set_yscale('log')
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
            y_lim_msk = sims[0].ccl_reader.d_values.l<1500
            l = sims[0].ccl_reader.d_values.l[msk]
            y_max = y_min = 10**5

            if p1 == p2 and x=='dd':
                for sim in sims:
                    sim.ccl_reader.nl = sim.ccl_reader.shotnoise[p1]
                    ax.plot(l, sim.ccl_reader.nl*np.ones_like( sim.ccl_reader.d_values.l[msk] ),
                        '--', label=f'Shot noise {str(sim)}')
            else:
                for sim in sims:
                    sim.ccl_reader.nl = 0


            for i, sim in enumerate(sims):
                sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk) - sim.ccl_reader.nl
                sim.clt = sim.ccl_reader.t_values.get_values(a, b, p1, p2, msk)
                sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)

                y_lim_msk = sim.ccl_reader
                y_max = max( y_max, np.max(sim.cl) )
                y_min = min( y_min, np.min(sim.cl) )

                delta = (l[1]-l[0])*i/len(sims)*0.5
                
                ax.errorbar(l+delta, sim.cl/sim.clt - 1, yerr=sim.err/sim.clt, fmt='.', label=f'Sim {str(sim)}/pred', lw=0.5)

            ax.set_xlabel(r'$\ell$', fontsize=15)
            ax.set_ylabel(r'$C_\ell$', fontsize=15)
            ax.legend()
            ax.set_yscale('log')
    plt.tight_layout()
    plt.show()

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

            for sim in sims:
                sim.cl  = sim.ccl_reader.d_values.get_values(a, b, p1, p2, msk)
                sim.err = sim.ccl_reader.d_values.get_errors(a, b, p1, p2, msk)
                 
                delta = (l[1]-l[0])*i/len(sims)*0.5
                ax.errorbar(l+delta, sim.cl, yerr=sim.err, fmt='.', label=f'Sim {str(sim)}')
            ax.plot(l, np.zeros_like(l), 'b-', label='Prediction')
            ax.set_xlabel(r'$\ell$', fontsize=15)
            ax.set_ylabel(r'$C_ell$', fontsize=15)
            ax.legend()
    # plt.tight_layout()
    plt.show()

    return


if __name__ == '__main__':
    main()