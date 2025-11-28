#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: bposselt
"""


import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import logging
import sys

import numpy as np
import pandas as pd

logger = logging.getLogger("plotlog")

###########################################################################
# input + output parameters

internal_calls_indir = "/home/bposselt/benchmark_worker1b/Nov1025/cheetah/"
benchmon_indir = "/home/bposselt/benchmark_worker1b/Nov1025/benchmon/benchmon_traces_ds-psi-pss-worker-1b/"

internal_call_csv="cheetah_fdas_101125_ThresholdON_FoFon_extract_forBM.csv"

outdir=benchmon_indir
outfile='cheetah_fdas_101125_ThresholdON_FoFon_extract.pdf'
fileout=outdir+outfile

# experimental, needs benchmon-traces directory structure because using benchmon code
do_power_plot = 1 # 1 do also plot power [needs benchmon code base], else only RAM plot
benchmon_vis_code_dir = "/home/bposselt/benchmon/benchmon_code/ska-sdp-benchmark-monitor/benchmon/visualization"


# Using -999 for both will use the beginning+end of benchmon timestamps
# otherwise a zoom-in is possible
begin_plot_time = -999
end_plot_time = -999
#begin_plot_time = -1
#end_plot_time = 520

###########################################################################

# Here: plot memory usage  
benchmon_csv = "mem_report.csv"

# power csv file
bm_power_csv = 'pow_report.csv'

###########################################################################

# read files
bm_df=pd.read_csv(benchmon_indir+benchmon_csv)
ic_df=pd.read_csv(internal_calls_indir+internal_call_csv)

# if we do the power plot 
if do_power_plot == 1:
    
    sys.path.append(benchmon_vis_code_dir)
    
    try:
        from power_metrics import PerfPowerData
    
        power_perf_metrics = PerfPowerData(logger=logger,
                                       csv_filename=benchmon_indir+bm_power_csv)
    
    
        #print(power_perf_metrics.pow_prof )
        #print(power_perf_metrics.cpus )
        #print(power_perf_metrics.time_stamps )

        cpus=power_perf_metrics.cpus
        events = power_perf_metrics.pow_prof[power_perf_metrics.cpus[0]].keys()

        pow_total = {event: 0 for event in events}  # noqa: C420
        for cpu in power_perf_metrics.cpus:
            for event in events:
                pow_total[event] += power_perf_metrics.pow_prof[cpu][event]
            #print(pow_total[event])


        time0=power_perf_metrics.time_stamps[0]
        pow_time = power_perf_metrics.time_stamps[1:] -time0
        pow_level = pow_total[event]
        assert len(pow_time) == len(pow_level), "pow_time and pow_level have different array lengths!"
        
    except Exception:   
        print(' ==== Problems with extracting power via benchmon tools! ')
        print('      (full benchmon-traces directory setup expected) ')
        # set variable to no-power-plot 
        do_power_plot = 0
        

    

# get covered time range with benchmon
bm_df.sort_values('timestamp',inplace=True) #in case not sorted



#  get start and end of pipeline run 
start_pipe=ic_df[(ic_df['name'] == 'cheetah_start')].calc_start[0]
end_pipe=ic_df[(ic_df['name'] == 'cheetah_end')].calc_start.iloc[-1]

# set zero time for reasonable labels
zero_time=start_pipe

# for upper panel apply zero time 
ic_df["ic_time1"] = ic_df['calc_start']-zero_time
ic_df["ic_time2"] = ic_df["ic_time1"] + (ic_df['dur_ns']/1e9)

# for lower plot (here RAM), subtract zero time    
bm_df['plot_time']=bm_df.timestamp - zero_time

# only get actual modules for later
drop_names = ["cheetah_start", "cheetah_end"]
#the ~ inverts that mask
df_f = ic_df[~ic_df["name"].isin(drop_names)].copy()


num_modules = len(df_f["name"].unique())
assert num_modules > 0, "no unique module names in the data"
print(num_modules,' module calls listed ')

# --- this could be later modified to allow selection for which ones to plot 
use_modules = df_f["name"].unique()
df_use = df_f[df_f["name"].isin(use_modules)].copy()

# ---  comment and change respective variable to zoom
#  begin and end of benchmon calls
if ((begin_plot_time == -999) and (end_plot_time == -999)):
    begin_plot_time = bm_df['plot_time'].iloc[0]
    end_plot_time = bm_df['plot_time'].iloc[-1]


def plot_all(bm_df,
             df_f,num_modules,
             fileout,
             begin_plot_time,end_plot_time,
             do_power_plot):

    #--- for benchmon: do RAM ratio plot
    max_ram =bm_df.MemTotal.iloc[0]
    inGB=' = %.3f' %( max_ram /1e9 ) +' GB'
    inTB=' = %.2f' %( max_ram /1e12 ) + ' TB'
    bm_ram_ratio_used_to_max  = (bm_df.MemTotal - bm_df.MemFree)/max_ram
    ratio_y_plot_max = np.max(bm_ram_ratio_used_to_max)+0.1

    colorlist = ["#0072B2",  # Blue
                  "#E69F00",  # Orange
                  "#56B4E9",  # Sky Blue
                  "#009E73",  # Bluish Green
                  "#F0E442",  # Yellow
                  "#D55E00",  # Vermillion
                  "#CC79A7",  # Reddish Purple
                  "#999999",  # Grey
                  "#332288",  # Indigo
                  "#88CCEE",  # Light Blue
                  "#117733",  # Dark Green
                  "#DDCC77",  # Sand
                  "#CC6677",  # Soft Red
                  "#AA4499",  # Purple
                  "#44AA99",  # Teal
                  "#882255",  # Dark Pink
                  "#661100",  # Brown
                  "#6699CC",  # Steel Blue
                  "#888888",  # Mid Grey
                  "#1E90FF"  # Dodger Blue
                  ]

    
    plt.rcParams.update({'font.size':20})
    plt.rcParams.update({'axes.labelsize':20})
    plt.rcParams.update({'axes.titlesize':20})
    plt.rcParams.update({'xtick.labelsize':20})
    plt.rcParams.update({'ytick.labelsize':20})
    plt.rcParams.update({'legend.fontsize':20})
    
    
    if do_power_plot == 1:
        fig, (ax,ax2,ax3) = plt.subplots(3, 1,  tight_layout=True,figsize=(29,12),
                              sharex=True,
                              gridspec_kw={'height_ratios': [2, 1,1]})
    else:    
        fig, (ax,ax2) = plt.subplots(2, 1,  tight_layout=True,figsize=(22,12),
                              sharex=True,gridspec_kw={'height_ratios': [2, 1]})
    
    fig.subplots_adjust(hspace=0.0, wspace=0.05, left=0.07, right=0.97)

    # --- Power plot if possible
    if do_power_plot == 1:
        ax3.plot(pow_time,pow_level,
                 label='benchmon total CPU power', 
                 color='black', linewidth=2)
        
        ax3.axvline([start_pipe-zero_time], color="red", 
                linestyle="-", linewidth=4, 
                #label='Cheetah START'
                )
        ax3.axvline([end_pipe-zero_time], color="red", 
                linestyle="--", linewidth=4, 
                #label='Cheetah END'
                )


      
        ax3.xaxis.set_label_position('top') 
        ax3.xaxis.tick_top()
        ax3.set(xlabel='time in sec')
        ax3.set(ylabel='Power (W)')        
        
        plot_pow_min=np.min(pow_level[0:-1])
        plot_pow_max=np.max(pow_level[0:-1])
        ax3.set(ylim=(plot_pow_min,plot_pow_max*1.1 ))

        ax3.legend(loc='upper center', ncol=3)
        
        ax3.xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
        ax3.grid(True)
        ax3.grid(which='minor',color='grey',ls='--',lw=1)
        ax3.grid(which='major',color='grey',lw=2)
        ax3.grid(which='minor', color='lightgrey', linestyle='--', linewidth=1)

    #----- RAM plot in lower panel + start/end of pipeline call
    ax2.plot(bm_df['plot_time'],bm_ram_ratio_used_to_max, 
             lw=3,zorder=4,color='blue', alpha=0.9,
             label='used CPU RAM, (available Max : '+inGB+' )')


    ax2.axvline([start_pipe-zero_time], color="red", 
                linestyle="-", linewidth=4, 
                label='Cheetah START')
    ax2.axvline([end_pipe-zero_time], color="red", 
                linestyle="--", linewidth=4, 
                label='Cheetah END')

    ax2.xaxis.set_label_position('top') 
    ax2.xaxis.tick_top()
    ax2.set(xlabel='time in sec')
    ax2.set(ylabel='used/max RAM')
    #plt.setp(ax2.get_xticklabels(), visible=True)
    ax2.tick_params(axis='x', which='both', labeltop=True, labelbottom=False)


    ax2.set(xlim=(begin_plot_time,end_plot_time))
    ax2.set(ylim=(0,ratio_y_plot_max ))

    ax2.grid(True)
    ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
    ax2.grid(which='minor',color='lightgrey',ls='--',lw=1)
    ax2.grid(which='major',color='grey',lw=2)
    ax2.legend(loc='lower center',ncol=3)

    # --- upper panel - internal module=on times 
    i=-1
    for name in df_f["name"].unique():
        i+=1
        subset = df_f[df_f["name"] == name]
        subset.reset_index(inplace=True,drop=True)
        sizesubset=len(subset)
        print('entries for ',name,' : ', sizesubset)
    
        if len(subset)>0:
             x1=np.asarray(subset['ic_time1'])
             x2=np.asarray(subset['ic_time2'])
             nf=x1/x1
    
             secsize= 1.0 / (num_modules)
             usec =0.2 *secsize
             y1=1.0-(secsize*i + usec) + secsize*0.3*nf
             y2=1.0-(secsize*i + 4.0*usec)+ secsize*0.3*nf    
             
             
             # use first entry of each for labels  
             ax.plot([x1[0],x2[0]],[y1[0],y2[0]], 
                 lw=8,zorder=1,color=colorlist[i],alpha=0.5,label=str(name))

             # other entries without labels
             for k in range(1,len(subset)):          
                 ax.plot([x1[k],x2[k]],[y1[k],y2[k]], 
                     lw=8,zorder=1,color=colorlist[i],alpha=0.5)

    # plot begin and end of Cheetah pipeline
    ax.axvline([start_pipe-zero_time], color="red", 
                linestyle="-", linewidth=4)
    ax.axvline([end_pipe-zero_time], color="red", 
                linestyle="--", linewidth=4)


    ax.set(xlim=(begin_plot_time,end_plot_time))
    ax.set(ylim=(0,1.4))
    ax.set_yticklabels([])
    ax.grid(True,axis='x',which='major',color='grey',lw=2,zorder=4)
    ax.legend(loc='upper center',ncol=8)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(10))
    ax.grid(which='minor',color='lightgrey',ls='--',lw=1)
   
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.subplots_adjust(hspace=0.35)
    plt.show()
    fig.savefig(fileout, dpi=300, bbox_inches='tight')
    print('--- created '+ fileout)


#############################################################################

plot_all(bm_df,
         df_use,
         num_modules,
         fileout,
         begin_plot_time,
         end_plot_time,
         do_power_plot)













