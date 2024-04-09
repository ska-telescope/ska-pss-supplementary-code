#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    **************************************************************************
    |             Routines to read in config files
    **************************************************************************
    | Author: B. Posselt
    **************************************************************************
    | Description:                                                           
    | includes 
    |      read_cheetah_config(file: str)
    |      read_POM_config(file: str)
    |      wanted_vs_exist(dfexistflags, dfparameters,dfwantedflags,dfcheetah)
    **************************************************************************
"""

import numpy as np
import pandas as pd
import xmltodict

def read_cheetah_config(file: str):
    """
    Parameters
    ----------
    file : path+filename
    
    Converts Cheetah pipeline xml file into dictionary
    then pandas data frame (1 row)
    
    Note: Updates required as more modules become available in POM and Cheetah


    Returns
    -------
    dicd : dictionary of Cheetah config (produced from xml file)  
           [kept for now for easy checking]
           
    dfout: pandas data frame with relevant Cheetah parameter values 
    
    df_flags: noting if the relevant parameters are existent in config 
              [NO-flags: 1 if there is no such entry in Cheetah config]

    """
    with open(file) as fd:    
# Produce dictionary from xml file
        dicd = xmltodict.parse(fd.read())

# Extract individual parameters
# Note for further processing: some values can be a list! 
#                      -> get e.g. number of elements in list
        
        try:        
            beams_beam_active=dicd['cheetah']['beams']['beam']['active']
            print('* beams/beam/active: ', beams_beam_active)
            NO_beams_beam_active=0
        except:
            print('* NO beams/beam/active *')
            NO_beams_beam_active=1
            beams_beam_active=np.nan
        
        try:        
            help_bbca1=dicd['cheetah']['beams']['beam']['cpu']['affinity']
#            print('* beams/beam/cpu/affinity: ', help_bbca1)
            help_bbca2 = [int(e) if e.isdigit() else e for e in help_bbca1.split(',')]
            beams_beam_cpu_affinity=len(help_bbca2)
            print('* beams/beam/cpu/affinity: ', help_bbca1, '; # =',beams_beam_cpu_affinity)
            NO_beams_beam_cpu_affinity=0
        except:
            print('* NO beams/beam/cpu/affinity *')
            NO_beams_beam_cpu_affinity=1
            beams_beam_cpu_affinity=np.nan 
            beams_beam_active=np.nan
        
        try:        
            beams_beam_sinks_threads=dicd['cheetah']['beams']['beam']['sinks']['threads']
            print('* beams/beam/sink/threads: ', beams_beam_sinks_threads)
            NO_beams_beam_sinks_threads=0
        except:
            print('* NO beams/beam/sink/threads *')
            NO_beams_beam_sinks_threads=1
            beams_beam_sinks_threads=np.nan
        print('')
       
        try:        
            help_pca1=dicd['cheetah']['pools']['pool']['cpu']['affinity']
#            print('* beams/beam/cpu/affinity: ', help_bbca1)
            help_pca2 = [int(e) if e.isdigit() else e for e in help_pca1.split(',')]
#            pools_cpu_affinity=dicd['cheetah']['pools']['pool']['cpu']['affinity']
            pools_cpu_affinity=len(help_pca2)
            print('* pools/cpu/affinity: ',help_pca1, '; # =',pools_cpu_affinity) 
            NO_pools_cpu_affinity=0
        except:
            print('* NO pools/cpu/affinity *')
            NO_pools_cpu_affinity=1
            pools_cpu_affinity=np.nan
        try:        
            pools_cpu_devices=dicd['cheetah']['pools']['pool']['cpu']['devices']
            print('* pools/cpu/devices: ', pools_cpu_devices)
            NO_pools_cpu_devices=0
        except:
            print('* NO pools/cpu/devices *')
            NO_pools_cpu_devices=1
            pools_cpu_devices=np.nan
        print('')
        
        try:        
            fdas_active=dicd['cheetah']['acceleration']['fdas']['active']
            print('* acc/fdas/active: ', fdas_active)
            NO_fdas_active=0
        except:
            print('* NO acc/fdas/active *')
            NO_fdas_active=1
            fdas_active=np.nan
            
        try:        
            tdas_active=dicd['cheetah']['acceleration']['tdas']['active']
            print('* acc/tdas/active: ', tdas_active)
            NO_tdas_active=0
        except:
            print('* NO acc/tdas/active *')
            NO_tdas_active=1
            tdas_active=np.nan

        print('')

        try:        
            ddtr_astroacc_active=dicd['cheetah']['ddtr']['astroaccelerate']['active']
            print('* ddtr/astroacc/active: ', ddtr_astroacc_active)
            NO_ddtr_astroacc_active=0
        except:
            print('* NO ddtr/astroacc/active *')
            NO_ddtr_astroacc_active=1
            ddtr_astroacc_active=np.nan
        try:        
            ddtr_cpu_active=dicd['cheetah']['ddtr']['cpu']['active']
            print('* ddtr/cpu/active: ', ddtr_cpu_active)
            NO_ddtr_cpu_active=0
        except:
            print('* NO ddtr/cpu/active *')
            NO_ddtr_cpu_active=1
            ddtr_cpu_active=np.nan
        try:        
            ddtr_dedisp_start=dicd['cheetah']['ddtr']['dedispersion']['start']
            print('* ddtr/dedispersion/start: ', ddtr_dedisp_start)
            NO_ddtr_dedisp_start=0
        except:
            NO_ddtr_dedisp_start=1
            ddtr_dedisp_start=np.nan
        try:        
            ddtr_dedisp_end=dicd['cheetah']['ddtr']['dedispersion']['end']
            print('* ddtr/dedispersion/end: ', ddtr_dedisp_end)
            NO_ddtr_dedisp_end=0
        except:
            NO_ddtr_dedisp_end=1
            ddtr_dedisp_end=np.nan
        try:        
            ddtr_dedisp_step=dicd['cheetah']['ddtr']['dedispersion']['step']
            print('* ddtr/dedispersion/step: ', ddtr_dedisp_step)
            NO_ddtr_dedisp_step=0
        except:
#            print('* NO ddtr/dedispersion/step *')
            NO_ddtr_dedisp_step=1
            ddtr_dedisp_step=np.nan
 
        try:        
            ddtr_fpga_active=dicd['cheetah']['ddtr']['fpga']['active']
            print('* ddtr/fpga/active: ', ddtr_fpga_active)
            NO_ddtr_fpga_active=0
        except:
            print('* NO ddtr/fpga/active *')
            NO_ddtr_fpga_active=1
            ddtr_fpga_active=np.nan
        try:        
            ddtr_gpubrute_active=dicd['cheetah']['ddtr']['gpu_bruteforce']['active']
            print('* ddtr/gpu_bruteforce/active: ', ddtr_gpubrute_active)
            NO_ddtr_gpubrute_active=0
        except:
            print('* NO ddtr/gpu_bruteforce/active *')
            NO_ddtr_gpubrute_active=1
            ddtr_gpubrute_active=np.nan
        try:        
            ddtr_rfiexcision_active=dicd['cheetah']['ddtr']['rfiexcision']['active']
            print('* ddtr/rfiexcision/active: ', ddtr_rfiexcision_active)
            NO_ddtr_rfiexcision_active=0
        except:
            print('* ddtr/rfiexcision/active *')
            NO_ddtr_rfiexcision_active=1
            ddtr_rfiexcision_active=np.nan
        print('')
        
        try:        
            fldo_cpu_active=dicd['cheetah']['fldo']['cpu']['active']
            print('* fldo/cpu/active: ', fldo_cpu_active)
            NO_fldo_cpu_active=0
        except:
            print('* NO fldo/cpu/active *')
            NO_fldo_cpu_active=1
            fldo_cpu_active=np.nan
        try:        
            fldo_oricuda_active=dicd['cheetah']['fldo']['origami_cuda']['active']   
            print('* fldo/origami_cuda/active: ', fldo_oricuda_active)
            NO_fldo_oricuda_active=0
        except:
            print('* NO fldo/origami_cuda/active *')
            NO_fldo_oricuda_active=1
            fldo_oricuda_active=np.nan  
        print('')
        
        try:        
            rfim_ampp_active=dicd['cheetah']['rfim']['rfim_ampp']['active']
            print('* rfim/rfim_ampp/active: ', rfim_ampp_active)
            NO_rfim_ampp_active=0
        except:
            print('* NO rfim/rfim_ampp/active *')
            NO_rfim_ampp_active=1
            rfim_ampp_active=np.nan
        try:        
            rfim_cuda_active=dicd['cheetah']['rfim']['rfim_cuda']['active']
            print('* rfim/rfim_cuda/active: ', rfim_cuda_active)
            NO_rfim_cuda_active=0
        except:
            print('* NO rfim/rfim_cuda/active *')
            NO_rfim_cuda_active=1
            rfim_cuda_active=np.nan
        try:        
            rfim_iqrmcpu_active=dicd['cheetah']['rfim']['rfim_iqrmcpu']['active']
            print('* rfim/rfi_iqrmcpu/active: ', rfim_iqrmcpu_active)
            NO_rfim_iqrmcpu_active=0
        except:
            print('* NO rfim/rfi_iqrmcpu/active *')
            NO_rfim_iqrmcpu_active=1
            rfim_iqrmcpu_active=np.nan
        try:        
            rfim_sumthreshold_active=dicd['cheetah']['rfim']['rfim_sum_threshold']['active']
            print('* rfim/rfim_ampp/active: ', rfim_sumthreshold_active)
            NO_rfim_sumthreshold_active=0
        except:
            print('* NO rfim/rfim_ampp/active *')
            NO_rfim_sumthreshold_active=1
            rfim_sumthreshold_active=np.nan
        try:        
            rfim_flagpolicy=dicd['cheetah']['rfim']['flag-policy']
            NO_rfim_flagpolicy=0
            print('* rfim/flag_policy: ', rfim_flagpolicy)
        except:
            print('* NO rfim/flag_policy *')
            NO_rfim_flagpolicy=1
            rfim_flagpolicy=np.nan
        print('')

        try:        
            print(dicd['cheetah']['scan']) 
            NO_scan=0
        except:
            print('* NO scan info *')
            NO_scan=1
            
        try:        
            scan_accel_range=dicd['cheetah']['scan']['accel_range']
            NO_scan_accel_range=0
        except:
            NO_scan_accel_range=1
            scan_accel_range=np.nan
        try:        
            scan_beam_bw=dicd['cheetah']['scan']['beam_bw']
            NO_scan_beam_bw=0
        except:
            NO_scan_beam_bw=1
            scan_beam_bw=np.nan
        try:        
            scan_beam_id=dicd['cheetah']['scan']['beam_id']
            NO_scan_beam_id=0
        except:
            NO_scan_beam_id=1
            scan_beam_id=np.nan
        try:        
            scan_bit_per_sample=dicd['cheetah']['scan']['bit_per_sample']
            NO_scan_bit_per_sample=0
        except:
            NO_scan_bit_per_sample=1
            scan_bit_per_sample=np.nan
        try:        
            scan_disp_measure=dicd['cheetah']['scan']['disp_measure']
            NO_scan_disp_measure=0
        except:
            NO_scan_disp_measure=1
            scan_disp_measure=np.nan
        try:        
            scan_freq_channels=dicd['cheetah']['scan']['freq_channels']
            NO_scan_freq_channels=0
        except:
            NO_scan_freq_channels=1
            scan_freq_channels=np.nan
        try:        
            scan_scan_id=dicd['cheetah']['scan']['scan_id']
            NO_scan_scan_id=0
        except:
            NO_scan_scan_id=1
            scan_scan_id=np.nan
        try:        
            scan_scan_time=dicd['cheetah']['scan']['scan_time']
            NO_scan_scan_time=0
        except:
            NO_scan_scan_time=1
            scan_scan_time=np.nan
        try:        
            scan_sub_array_id=dicd['cheetah']['scan']['sub_array_id']
            NO_scan_sub_array_id=0
        except:
            NO_scan_sub_array_id=1
            scan_sub_array_id=np.nan
        try:        
            scan_time_resolution=dicd['cheetah']['scan']['time_resolution']
            NO_scan_time_resolution=0
        except:
            NO_scan_time_resolution=1
            scan_time_resolution=np.nan
        try:        
            scan_time_samples=dicd['cheetah']['scan']['time_samples']
            NO_scan_time_samples=0
        except:
            NO_scan_time_samples=1
            scan_time_samples=np.nan
        try:        
            scan_trials_number=dicd['cheetah']['scan']['trials_number']
            NO_scan_trials_number=0
        except:
            NO_scan_trials_number=1
            scan_trials_number=np.nan

        print('')

        try:        
            sift_simplesift_active=dicd['cheetah']['sift']['simple_sift']['active']
            print('* sift/simplesift/active: ', sift_simplesift_active)
            NO_sift_simplesift_active=0
        except:
            print('* NO sift/simplesift/active *')
            NO_sift_simplesift_active=1
            sift_simplesift_active=np.nan

        print('')
        
        try:        
            sps_astroacc_active=dicd['cheetah']['sps']['astroaccelerate']['active']
            print('* sps/astroaccelerate/active: ', sps_astroacc_active)
            NO_sps_astroacc_active=0
        except:
            print('* NO sps/astroaccelerate/active *')
            NO_sps_astroacc_active=1
            sps_astroacc_active=np.nan
        try:        
            sps_cpu_active=dicd['cheetah']['sps']['cpu']['active']
            print('* sps/cpu/active: ', sps_cpu_active)
            NO_sps_cpu_active=0
        except:
            print('* NO sps/cpu/active *')
            NO_sps_cpu_active=1
            sps_cpu_active=np.nan
        try:        
            sps_emulator_active=dicd['cheetah']['sps']['emulator']['active']
            print('* sps/emulator/active: ', sps_emulator_active)
            NO_sps_emulator_active=0
        except:
            print('* NO sps/emulator/active *')
            NO_sps_emulator_active=1
            sps_emulator_active=np.nan

        print('')
        
        try:        
            sps_clustering_active=dicd['cheetah']['sps_clustering']['active']
            print('* sps_clustering/active: ', sps_clustering_active)
            NO_sps_clustering_active=0
        except:
            print('* NO sps_clustering/active *')
            NO_sps_clustering_active=1
            sps_clustering_active=np.nan
        try:        
            sps_clustering_numberOfThreads=dicd['cheetah']['sps_clustering']['number_of_threads']
            NO_sps_clustering_numberOfThreads=0
            print('')
        except:
            NO_sps_clustering_numberOfThreads=1
            sps_clustering_numberOfThreads=np.nan
        
        
        try:        
            spsift_active=dicd['cheetah']['spsift']['active']
            print('* spsift/active: ', spsift_active)
            NO_spsift_active=0
        except:
            print('* NO spsift/active *')
            NO_spsift_active=1
            spsift_active=np.nan
        try:        
            spsift_max_candis=dicd['cheetah']['spsift']['maximum_candidates']
            NO_spsift_max_candis=0
            print('')
        except:
            NO_spsift_max_candis=1
            spsift_max_candis=np.nan

# Put extracted Cheetah pipeline parameters in easy-to-query dataframe

        dfout=pd.DataFrame({'beams_beam_active':         [beams_beam_active],
                            'beams_beam_cpu_affinity':   [beams_beam_cpu_affinity],
                            'beams_beam_sinks_threads':  [beams_beam_sinks_threads],
                            'pools_cpu_affinity':        [pools_cpu_affinity],
                            'pools_cpu_devices':         [pools_cpu_devices],
                            'fdas_active':               [fdas_active],
                            'tdas_active':               [tdas_active],
                            'ddtr_astroacc_active':      [ddtr_astroacc_active],
                            'ddtr_cpu_active':           [ddtr_cpu_active],
                            'ddtr_dedisp_start':         [ddtr_dedisp_start],
                            'ddtr_dedisp_end':           [ddtr_dedisp_end],
                            'ddtr_dedisp_step':          [ddtr_dedisp_step],
                            'ddtr_fpga_active':          [ddtr_fpga_active],
                            'ddtr_gpubrute_active':      [ddtr_gpubrute_active],
                            'ddtr_rfiexcision_active':   [ddtr_rfiexcision_active],
                            'fldo_cpu_active':           [fldo_cpu_active],
                            'fldo_oricuda_active':       [fldo_oricuda_active],
                            'rfim_ampp_active':          [rfim_ampp_active],
                            'rfim_cuda_active':          [rfim_cuda_active],
                            'rfim_iqrmcpu_active':       [rfim_iqrmcpu_active],
                            'rfim_sumthreshold_active':  [rfim_sumthreshold_active],
                            'rfim_flagpolicy':           [rfim_flagpolicy],
                            'scan_accel_range':          [scan_accel_range], 
                            'scan_beam_bw':              [scan_beam_bw],
                            'scan_beam_id':              [scan_beam_id],
                            'scan_bit_per_sample':       [scan_bit_per_sample], 
                            'scan_disp_measure':         [scan_disp_measure],
                            'scan_freq_channels':        [scan_freq_channels],
                            'scan_scan_id':              [scan_scan_id],
                            'scan_scan_time':            [scan_scan_time],
                            'scan_sub_array_id':         [scan_sub_array_id],
                            'scan_time_resolution':      [scan_time_resolution],
                            'scan_time_samples':         [scan_time_samples],
                            'scan_trials_number':        [scan_trials_number],
                            'sift_simplesift_active':    [sift_simplesift_active],
                            'sps_astroacc_active':       [sps_astroacc_active],
                            'sps_cpu_active':            [sps_cpu_active],
                            'sps_emulator_active':       [sps_emulator_active],
                            'sps_clustering_active':     [sps_clustering_active] ,
                            'sps_clustering_numberOfThreads': [sps_clustering_numberOfThreads],
                            'spsift_active':             [spsift_active],
                            'spsift_max_candis':         [spsift_max_candis]                         
                            })
        

        df_flags=pd.DataFrame({'NO_beams_beam_active':         [NO_beams_beam_active],
                               'NO_beams_beam_cpu_affinity':   [NO_beams_beam_cpu_affinity],
                               'NO_beams_beam_sinks_threads':  [NO_beams_beam_sinks_threads],
                               'NO_pools_cpu_affinity':        [NO_pools_cpu_affinity],
                               'NO_pools_cpu_devices':         [NO_pools_cpu_devices],
                               'NO_fdas_active':               [NO_fdas_active],
                               'NO_tdas_active':               [NO_tdas_active],
                               'NO_ddtr_astroacc_active':      [NO_ddtr_astroacc_active],
                               'NO_ddtr_cpu_active':           [NO_ddtr_cpu_active],
                               'NO_ddtr_dedisp_start':         [NO_ddtr_dedisp_start],
                               'NO_ddtr_dedisp_end':           [NO_ddtr_dedisp_end],
                               'NO_ddtr_dedisp_step':          [NO_ddtr_dedisp_step],
                               'NO_ddtr_fpga_active':          [NO_ddtr_fpga_active],
                               'NO_ddtr_gpubrute_active':      [NO_ddtr_gpubrute_active],
                               'NO_ddtr_rfiexcision_active':   [NO_ddtr_rfiexcision_active],
                               'NO_fldo_cpu_active':           [NO_fldo_cpu_active],
                               'NO_fldo_oricuda_active':       [NO_fldo_oricuda_active],
                               'NO_rfim_ampp_active':          [NO_rfim_ampp_active],
                               'NO_rfim_cuda_active':          [NO_rfim_cuda_active],
                               'NO_rfim_iqrmcpu_active':       [NO_rfim_iqrmcpu_active],
                               'NO_rfim_sumthreshold_active':  [NO_rfim_sumthreshold_active],
                               'NO_rfim_flagpolicy':           [NO_rfim_flagpolicy],
                               'NO_scan_accel_range':          [NO_scan_accel_range], 
                               'NO_scan':                      [NO_scan], 
                               'NO_scan_beam_bw':              [NO_scan_beam_bw],
                               'NO_scan_beam_id':              [NO_scan_beam_id],
                               'NO_scan_bit_per_sample':       [NO_scan_bit_per_sample],    
                               'NO_scan_disp_measure':         [NO_scan_disp_measure],
                               'NO_scan_freq_channels':        [NO_scan_freq_channels],
                               'NO_scan_scan_id':              [NO_scan_scan_id],
                               'NO_scan_scan_time':            [NO_scan_scan_time],
                               'NO_scan_sub_array_id':         [NO_scan_sub_array_id],
                               'NO_scan_time_resolution':      [NO_scan_time_resolution],
                               'NO_scan_time_samples':         [NO_scan_time_samples],
                               'NO_scan_trials_number':        [NO_scan_trials_number],
                               'NO_sift_simplesift_active':    [NO_sift_simplesift_active],
                               'NO_sps_astroacc_active':       [NO_sps_astroacc_active],
                               'NO_sps_cpu_active':            [NO_sps_cpu_active],
                               'NO_sps_emulator_active':       [NO_sps_emulator_active],
                               'NO_sps_clustering_active':     [NO_sps_clustering_active] ,
                               'NO_sps_clustering_numberOfThreads': [NO_sps_clustering_numberOfThreads],
                               'NO_spsift_active':             [NO_spsift_active],
                               'NO_spsift_max_candis':         [NO_spsift_max_candis]                         
                            })
        

    return(dicd,dfout,df_flags)    
#---------- example  usage case:  [done in main routine]      
# get dictionary, pandas data frames for further use        
#dict_cheetah,df_cheetah,df_cheetahflags=read_cheetah_config(file1)
#print(df_cheetah.columns.values)
#print(df_cheetah)
#print(df_cheetahflags)

#~-----------------------------------------------------
def read_POM_config(file: str):
    """
    Parameters
    ----------
    file : path + csv file [see eample /config_examples/POM_config.csv]

    Returns
    -------
    df_pom: pandas data frame of POM config parameters
    
    df_pomT: transposed version of df_pom

    """
    df_pom  =pd.read_csv(file,sep=',',comment='#')
    df_pomT =df_pom.set_index('parameter').T
    print('--- read in POM config file ---')
    print(df_pom)
#    print(df_pomT)
    return(df_pom,df_pomT)


#~-----------------------------------------------------
def wanted_vs_exist(dfexistflags, dfparameters,dfwantedflags,dfcheetah):
    """
    screens wanted modules from cheetah config and POM config against 
    what is (so far) implemented in POM;
    takes care of choice for precedence among configs

    Parameters
    ----------
    dfexistflags : pandas data frame of POM-Exist flags (set in main program)

    dfparameters : (transposed) POM config parameters; pandas DF
        
    dfwantedflags : Cheetah config relevant parameter flags; pandas DF 
        
    dfcheetah : Cheetah config relevant parameter values, pandas DF

    Returns
    -------
    df_run_flags : actual POM run flags to be used in main program 

    """
    dfe=dfexistflags.copy()
    dfp=dfparameters.copy()
    dfw=dfwantedflags.copy()
    dfc=dfcheetah.copy()
    
    print('/// ignore_cheetah_config_modules = ',dfp.ignore_cheetah_config_modules.iat[0])
    
    if (dfp.ignore_cheetah_config_modules.iat[0]==0):
        print('/// ONLY use Cheetah config for run modules')
    if (dfp.ignore_cheetah_config_modules.iat[0]==1):
        print('/// ignore Cheetah config for run modules')
    if (dfp.ignore_cheetah_config_modules.iat[0]==2):
        print('/// POM config takes precedence over Cheetah config for run modules')


#~------   begin of figuring out which modules we WANT to run          
        
# reminder: POM parameter file 
#ignore_cheetah_config_modules,0  
#       0 = only use cheetah config; 
#       1 = ignore cheetah config; 
#       2 = POM run_... parameters takes precedence IF existent (no comment before run...)


#-------------------------------------------------------------------
    if (dfp.ignore_cheetah_config_modules.iloc[0] > 0):      
        try:        
            run_rcpt=dfp.run_rcpt.iloc[0]
        except:
            run_rcpt=np.nan

        try:        
            run_ddbc=dfp.run_ddbc.iloc[0]
        except:
            run_ddbc=np.nan

        try:        
            run_rfim=dfp.run_rfim.iloc[0]
        except:
            run_rfim=np.nan

        try:        
            run_ddtr=dfp.run_ddtr.iloc[0]
        except:
            run_ddtr=np.nan

        try:        
            run_spdt=dfp.run_spdt.iloc[0]
        except:
            run_spdt=np.nan

        try:        
            run_spsift=dfp.run_spsift.iloc[0]
        except:
            run_spsift=np.nan

        try:        
            run_ffbc=dfp.run_ffbc.iloc[0]
        except:
            run_ffbc=np.nan

        try:        
            run_psbc=dfp.run_psbc.iloc[0]
        except:
            run_psbc=np.nan

        try:        
            run_cxft=dfp.run_cxft.iloc[0]
        except:
            run_cxft=np.nan

        try:        
            run_brdz=dfp.run_brdz.iloc[0]
        except:
            run_brdz=np.nan

        try:        
            run_dred=dfp.run_dred.iloc[0]
        except:
            run_dred=np.nan

        try:        
            run_fdas=dfp.run_fdas.iloc[0]
        except:
            run_fdas=np.nan

        try:        
            run_sift=dfp.run_sift.iloc[0]
        except:
            run_sift=np.nan

        try:        
            run_fldo=dfp.run_fldo.iloc[0]
        except:
            run_fldo=np.nan

        try:        
            run_cdos=dfp.run_cdos.iloc[0]
        except:
            run_cdos=np.nan
            
        df_run_flags=pd.DataFrame({'run_rcpt': [run_rcpt],
                                   'run_ddbc': [run_ddbc],
                                   'run_rfim': [run_rfim],
                                   'run_ddtr': [run_ddtr],
                                   'run_spdt': [run_spdt],
                                   'run_spsift':[run_spsift],
                                   'run_ffbc': [run_ffbc],
                                   'run_psbc': [run_psbc],
                                   'run_cxft':[run_cxft],
                                   'run_brdz':[run_brdz],
                                   'run_dred':[run_dred],
                                   'run_fdas':[run_fdas],
                                   'run_sift':[run_sift],
                                   'run_fldo':[run_fldo],
                                   'run_cdos':[run_cdos]     
                                       })    
    

#----------------------------------------------------------------
    if ((dfp.ignore_cheetah_config_modules.iloc[0]==0) 
        or (dfp.ignore_cheetah_config_modules.iloc[0]==2)):
# first test if NO-flag is off, then check for actual value/choice [will be important later]
        
#--- proxy for RCP module 
        try:
# check first if Cheetah entry exists            
            if (dfw.NO_beams_beam_active.iloc[0] == 0):
# then check if entry has a value 'true' [can be 'false' too]                
                if (dfc.beams_beam_active.iloc[0] == 'true'):  run_rcpt=1
                else: run_rcpt=0
            else:
                run_rcpt=0
                print(' /// no incoming beam data ! This would not work.')
        except:
            run_rcpt=0
            print(' /// no incoming beam data ! This would not work.  (b)')

#---    FDAS     
        try:
            if (dfw.NO_fdas_active.iloc[0] == 0):
                if (dfc.fdas_active.iloc[0] == 'true'):  run_fdas=1
                else: run_fdas=0             
            else:
                run_fdas=0
#               print(' /// FDAS module inactive!')
        except:
            run_fdas=0
#            print(' /// FDAS module inactive!')


#---    TDAS (not active anyway)     
#        try:
#            if (dfw.NO_tdas_active == 0):
#                run_tdas=1
#                print(' /// TDAS module will be simulated')
#            else:
#                run_tdas=0
#               print(' /// TDAS module inactive!')
#        except:
#            run_tdas=0
#            print(' /// TDAS module inactive!')



#---    DDTR     
        try:
            if ((dfw.NO_ddtr_astroacc_active.iloc[0] == 0) or 
                (dfw.NO_ddtr_cpu_active.iloc[0] == 0) or 
                (dfw.NO_ddtr_fpga_active.iloc[0] == 0)
                or (dfw.NO_ddtr_gpubrute_active.iloc[0]==0)                
                ):
                if ((dfc.ddtr_astroacc_active.iloc[0] == 'true') 
                    or (dfc.ddtr_cpu_active.iloc[0] == 'true') 
                    or (dfc.ddtr_gpubrute_active.iloc[0] == 'true') 
                    or (dfc.ddtr_fpga_active.iloc[0] == 'true')):  run_ddtr=1
                else: run_ddtr=0             
            else:
                run_ddtr=0
        except:
            run_ddtr=0


#---   FLDO      
        try:
            if ((dfw.NO_fldo_cpu_active.iloc[0] == 0) 
                or (dfw.NO_fldo_oricuda_active.iloc[0] == 0)):
                
                if ((dfc.fldo_cpu_active.iloc[0] == 'true') 
                    or (dfc.fldo_oricuda_active.iloc[0] == 'true')):  run_fldo=1
                else: run_fldo=0             
            else:
                run_fldo=0
        except:
            run_fldo=0


#---   RFIM      
        try:
            if ((dfw.NO_rfim_ampp_active.iloc[0] == 0) 
                or (dfw.NO_rfim_cuda_active.iloc[0] == 0)
                or (dfw.NO_rfim_iqrmcpu_active.iloc[0] == 0)):
                
                if ((dfc.rfim_ampp_active.iloc[0] == 'true') 
                    or (dfc.rfim_cuda_active.iloc[0] == 'true') 
                    or (dfc.rfim_iqrmcpu_active.iloc[0] == 'true')):  run_rfim=1
                else: run_rfim=0             
            else:
                run_rfim=0
        except:
            run_rfim=0


#--- SIFT        
        try:
            if (dfw.NO_sift_simplesift_active.iloc[0] == 0):
                if (dfc.sift_simplesift_active.iloc[0] == 'true'): run_sift=1
                else: run_sift=0             
            else:
                run_sift=0
        except:
            run_sift=0


#--- SPS is proxy for spdt       
        try:
            if ((dfw.sps_cpu_active.iloc[0] == 0) 
                or (dfw.sps_astroacc_active.iloc[0] == 0)):
                if ((dfc.sps_astroacc_active.iloc[0] == 'true') 
                    or (dfc.sps_cpu_active.iloc[0] == 'true') ):  run_spdt=1
                else: run_spdt=0             
            else:
                run_spdt=0
        except:
            run_spdt=0

#--- SSPIFT        
        try:
            if (dfw.NO_spsift_active.iloc[0] == 0):
                if ((dfc.spsift_active.iloc[0] == 'true') ):  run_spsift=1
                else: run_spsift=0             
            else:
                run_spsift=0
        except:
            run_spsift=0

#---  for later implementation...       
#        try:
#            if (dfw. == 0):
#                run_=1
#            else:
#                run_=0
#        except:
#            run_=0


#--- currently not implemented or not obvious from Cheetah config file
# meanwhile: use reasonable choices for current POM          
        print('--- Note from function wanted_vs_exist: DDBC not in Cheetah config yet, set to > NOT run<')
        run_ddbc=0  # boolean
        print('--- Note from function wanted_vs_exist: FFBC not in Cheetah config yet, set to > run<')
        run_ffbc=1  # boolean
        print('--- Note from function wanted_vs_exist: PSBC not in Cheetah config yet, set to > NOT run<')
        run_psbc=0  # boolean
        print('--- Note from function wanted_vs_exist: CXFT not in Cheetah config yet, set to > NOT run<')
        run_cxft=0  # boolean
        print('--- Note from function wanted_vs_exist: BRDZ not in Cheetah config yet, set to > NOT run<')
        run_brdz=0  # boolean
        print('--- Note from function wanted_vs_exist: DRED not in Cheetah config yet, set to > NOT run<')
        run_dred=0  # boolean
        print('--- Note from function wanted_vs_exist: CDOS not in Cheetah config yet, set to > run<')
        run_cdos=1  # boolean

        df_run_flagsh1=pd.DataFrame({'run_rcpt': [run_rcpt],
                                   'run_ddbc': [run_ddbc],
                                   'run_rfim': [run_rfim],
                                   'run_ddtr': [run_ddtr],
                                   'run_spdt': [run_spdt],
                                   'run_spsift':[run_spsift],
                                   'run_ffbc': [run_ffbc],
                                   'run_psbc': [run_psbc],
                                   'run_cxft':[run_cxft],
                                   'run_brdz':[run_brdz],
                                   'run_dred':[run_dred],
                                   'run_fdas':[run_fdas],
                                   'run_sift':[run_sift],
                                   'run_fldo':[run_fldo],
                                   'run_cdos':[run_cdos]     
                                   })


        if (dfp.ignore_cheetah_config_modules.iloc[0]==0):
            df_run_flags=df_run_flagsh1.copy()


#        print(df_run_flags)
#        print('----')
#        print(df_run_flagsh1)
        

# if commented out in POM parameter file, use cheetah config value
# for =2 we have two data frames ...flags and ...flagsh1
        if (dfp.ignore_cheetah_config_modules.iloc[0]==2):
            
            if (df_run_flags.run_rcpt.iat[0] == np.nan): 
                df_run_flags.run_rcpt.iat[0] = df_run_flagsh1.run_rcpt.iat[0]

            if (df_run_flags.run_ddbc.iat[0] == np.nan): 
                df_run_flags.run_ddbc.iat[0] = df_run_flagsh1.run_ddbc.iat[0]

            if (df_run_flags.run_rfim.iat[0] == np.nan): 
                df_run_flags.run_rfim.iat[0] = df_run_flagsh1.run_rfim.iat[0]

            if (df_run_flags.run_ddtr.iat[0] == np.nan): 
                df_run_flags.run_ddtr.iat[0] = df_run_flagsh1.run_ddtr.iat[0]

            if (df_run_flags.run_spdt.iat[0] == np.nan): 
                df_run_flags.run_spdt.iat[0] = df_run_flagsh1.run_spdt.iat[0]

            if (df_run_flags.run_spsift.iat[0] == np.nan): 
                df_run_flags.run_spsift.iat[0] = df_run_flagsh1.run_spsift.iat[0]

            if (df_run_flags.run_ffbc.iat[0] == np.nan): 
                df_run_flags.run_ffbc.iat[0] = df_run_flagsh1.run_ffbc.iat[0]

            if (df_run_flags.run_psbc.iat[0] == np.nan): 
                df_run_flags.run_psbc.iat[0] = df_run_flagsh1.run_psbc.iat[0]

            if (df_run_flags.run_cxft.iat[0] == np.nan): 
                df_run_flags.run_cxft.iat[0] = df_run_flagsh1.run_cxft.iat[0]

            if (df_run_flags.run_brdz.iat[0] == np.nan): 
                df_run_flags.run_brdz.iat[0] = df_run_flagsh1.run_brdz.iat[0]

            if (df_run_flags.run_dred.iat[0] == np.nan): 
                df_run_flags.run_dred.iat[0] = df_run_flagsh1.run_dred.iat[0]

            if (df_run_flags.run_fdas.iat[0] == np.nan): 
                df_run_flags.run_fdas.iat[0] = df_run_flagsh1.run_fdas.iat[0]

            if (df_run_flags.run_sift.iat[0] == np.nan): 
                df_run_flags.run_sift.iat[0] = df_run_flagsh1.run_sift.iat[0]

            if (df_run_flags.run_fldo.isna().iat[0]): 
                df_run_flags.run_fldo.iat[0] = df_run_flagsh1.run_fldo.iat[0]

            if (df_run_flags.run_cdos.iat[0] == np.nan): 
                df_run_flags.run_cdos.iat[0] = df_run_flagsh1.run_cdos.iat[0]
#
# Note: nan is float, hence value will be 0.0 instead of 0            
#            
#~------   end of figuring out which modules we WANT to run          
        
#~------   compare what we WANT with what EXISTs in the POM          

    if ((dfe.rcpt.iloc[0] == 1) and (df_run_flags.run_rcpt.iloc[0] == 1)):
        print('/// RCPT will be simulated')        
    if ((dfe.rcpt.iloc[0] == 0) and (df_run_flags.run_rcpt.iloc[0] == 1)):
        df_run_flags.run_rcpt.iloc[0] = 0
        print('/// Warning: RCPT module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_rcpt.iloc[0] == 0)):
        print('///  RCPT module NOT simulated')        
 
    if ((dfe.ddbc.iloc[0] == 1) and (df_run_flags.run_ddbc.iloc[0] == 1)):
        print('/// DDBC will be simulated')        
    if ((dfe.ddbc.iloc[0] == 0) and (df_run_flags.run_ddbc.iloc[0] == 1)):
        df_run_flags.run_ddbc.iloc[0] = 0
        print('/// Warning: DDBC module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_ddbc.iloc[0] == 0)):
        print('///  DDBC module NOT simulated')        

    if ((dfe.rfim.iloc[0] == 1) and (df_run_flags.run_rfim.iloc[0] == 1)):
        print('/// RFIM will be simulated')        
    if ((dfe.rfim.iloc[0] == 0) and (df_run_flags.run_rfim.iloc[0] == 1)):
        df_run_flags.run_rfim.iloc[0] = 0
        print('/// Warning: RFIM module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_rfim.iloc[0] == 0)):
        print('///  RFIM module NOT simulated')        

    if ((dfe.ddtr.iloc[0] == 1) and (df_run_flags.run_ddtr.iloc[0] == 1)):
        print('/// DDTR will be simulated')        
    if ((dfe.ddtr.iloc[0] == 0) and (df_run_flags.run_ddtr.iloc[0] == 1)):
        df_run_flags.run_ddtr.iloc[0] = 0
        print('/// Warning: DDTR module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_ddtr.iloc[0] == 0)):
        print('///  DDTR module NOT simulated')        

    if ((dfe.spdt.iloc[0] == 1) and (df_run_flags.run_spdt.iloc[0] == 1)):
        print('/// SPDT will be simulated')        
    if ((dfe.spdt.iloc[0] == 0) and (df_run_flags.run_spdt.iloc[0] == 1)):
        df_run_flags.run_spdt.iloc[0] = 0
        print('/// Warning: SPDT module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_spdt.iloc[0] == 0)):
        print('///  SPDT module NOT simulated')        

    if ((dfe.spsift.iloc[0] == 1) and (df_run_flags.run_spsift.iloc[0] == 1)):
        print('/// SPSIFT will be simulated')        
    if ((dfe.spsift.iloc[0] == 0) and (df_run_flags.run_spsift.iloc[0] == 1)):
        df_run_flags.run_spsift.iloc[0] = 0
        print('/// Warning: SPSIFT module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_spsift.iloc[0] == 0)):
        print('///  SPSIFT module NOT simulated')        

    if ((dfe.ffbc.iloc[0] == 1) and (df_run_flags.run_ffbc.iloc[0] == 1)):
        print('/// FFBC will be simulated')        
    if ((dfe.ffbc.iloc[0] == 0) and (df_run_flags.run_ffbc.iloc[0] == 1)):
        df_run_flags.run_ffbc.iloc[0] = 0
        print('/// Warning: FFBC module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_ffbc.iloc[0] == 0)):
        print('///  FFBC module NOT simulated')        

    if ((dfe.psbc.iloc[0] == 1) and (df_run_flags.run_psbc.iloc[0] == 1)):
        print('/// PSBC will be simulated')        
    if ((dfe.psbc.iloc[0] == 0) and (df_run_flags.run_psbc.iloc[0] == 1)):
        df_run_flags.run_psbc.iloc[0] = 0
        print('/// Warning: PSBC module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_psbc.iloc[0] == 0)):
        print('///  PSBC module NOT simulated')        

    if ((dfe.cxft.iloc[0] == 1) and (df_run_flags.run_cxft.iloc[0] == 1)):
        print('/// CXFT will be simulated')        
    if ((dfe.cxft.iloc[0] == 0) and (df_run_flags.run_cxft.iloc[0] == 1)):
        df_run_flags.run_cxft.iloc[0] = 0
        print('/// Warning: CXFT module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_cxft.iloc[0] == 0)):
        print('///  CXFT module NOT simulated')        

    if ((dfe.brdz.iloc[0] == 1) and (df_run_flags.run_brdz.iloc[0] == 1)):
        print('/// BRDZ will be simulated')        
    if ((dfe.brdz.iloc[0] == 0) and (df_run_flags.run_brdz.iloc[0] == 1)):
        df_run_flags.run_brdz.iloc[0] = 0
        print('/// Warning: BRDZ module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_brdz.iloc[0] == 0)):
        print('///  BRDZ module NOT simulated')        

    if ((dfe.dred.iloc[0] == 1) and (df_run_flags.run_dred.iloc[0] == 1)):
        print('/// DRED will be simulated')        
    if ((dfe.dred.iloc[0] == 0) and (df_run_flags.run_dred.iloc[0] == 1)):
        df_run_flags.run_dred.iloc[0] = 0
        print('/// Warning: DRED module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_dred.iloc[0] == 0)):
        print('///  DRED module NOT simulated')        

    if ((dfe.fdas.iloc[0] == 1) and (df_run_flags.run_fdas.iloc[0] == 1)):
        print('/// FDAS will be simulated')        
    if ((dfe.fdas.iloc[0] == 0) and (df_run_flags.run_fdas.iloc[0] == 1)):
        df_run_flags.run_fdas.iloc[0] = 0
        print('/// Warning: FDAS module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_fdas.iloc[0] == 0)):
        print('///  FDAS module NOT simulated')        

    if ((dfe.sift.iloc[0] == 1) and (df_run_flags.run_sift.iloc[0] == 1)):
        print('/// SIFT will be simulated')        
    if ((dfe.sift.iloc[0] == 0) and (df_run_flags.run_sift.iloc[0] == 1)):
        df_run_flags.run_sift.iloc[0] = 0
        print('/// Warning: SIFT module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_sift.iloc[0] == 0)):
        print('///  SIFT module NOT simulated')        

    if ((dfe.fldo.iloc[0] == 1) and (df_run_flags.run_fldo.iloc[0] == 1)):
        print('/// FLDO will be simulated')        
    if ((dfe.fldo.iloc[0] == 0) and (df_run_flags.run_fldo.iloc[0] == 1)):
        df_run_flags.run_fldo.iloc[0] = 0
        print('/// Warning: FLDO module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_fldo.iloc[0] == 0)):
        print('///  FLDO module NOT simulated')        

    if ((dfe.cdos.iloc[0] == 1) and (df_run_flags.run_cdos.iloc[0] == 1)):
        print('/// CDOS will be simulated')        
    if ((dfe.cdos.iloc[0] == 0) and (df_run_flags.run_cdos.iloc[0] == 1)):
        df_run_flags.run_cdos.iloc[0] = 0
        print('/// Warning: CDOS module wanted, but not yet implemented, run parameter reset')        
    if ((df_run_flags.run_cdos.iloc[0] == 0)):
        print('///  CDOS module NOT simulated')        
        
        
    return(df_run_flags)    



