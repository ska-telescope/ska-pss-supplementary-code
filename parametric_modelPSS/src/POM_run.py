#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    **************************************************************************
    |        main program to run the PSS Parametric Operational Model
    **************************************************************************
    | Author: B. Posselt
    **************************************************************************
    | Description:
    |  (1) read config files and choose modules(and parameters) to run POM
    |                                                        
    | 
    | Usage on shell: [put in one line]
    |  python POM_run.py 
    |  .../parametric_modelPSS/config_examples/protest_mid_single_beam.xml 
    |  .../parametric_modelPSS/config_examples/POM_config.csv
    |      
    |  1st argument: Cheetah config file - .xml
    |  2nd argument: POM config file - .csv    
    **************************************************************************
"""

import POM_readin as pr

import simpy
import pandas as pd
import numpy as np

import argparse





#------------------------------------------------------------------------------
# read arguments
#------------------------------------------------------------------------------
parser=argparse.ArgumentParser()
parser.add_argument("cheetah_config_file",type=str,help="path/CheetahConfigFile")
parser.add_argument("pom_config_file",type=str,help="path/POMConfigFile")

args = parser.parse_args()
cheetah_config_file=args.cheetah_config_file
pom_config_file=args.pom_config_file
print(cheetah_config_file)
print(pom_config_file)

#------------------------------------------------------------------------------
# define flags which modules currently exist in POM; 
#        1: exists 0: does not exist
# TDAS ignored since not planned to do
#------------------------------------------------------------------------------
pom_exist_flags=pd.DataFrame({'rcpt':       [1],
                              'ddbc':       [0],
                              'rfim':       [0],
                              'ddtr':       [0],
                              'spdt':       [0],
                              'spsift':     [0],
                              'ffbc':       [1], # for unmodified obs
                              'psbc':       [0],
                              'cxft':       [0],
                              'brdz':       [0],
                              'dred':       [0],
                              'fdas':       [0],
                              'sift':       [0],
                              'fldo':       [0],
                              'cdos':       [1]
                              })

#------------------------------------------------------------------------------
# Read in configs, cross-check against existing capabilities
#------------------------------------------------------------------------------
print('------------- Reading of cheetah config file ------------- ')
dict_cheetah,df_cheetah,df_cheetahflags=pr.read_cheetah_config(cheetah_config_file)
print(' ')
print('=== read (selected) Cheetah config - column header')
print(df_cheetah.columns.values)
print(' ')
print('=== read (selected) Cheetah config parameter - full data frame')
print(df_cheetah)
# config files might defer because entries were removed:
print(' ')
print('=== NO-flags data frame column header')
print('=== indicating if (selected) Cheetah pars exist in config file')
print(df_cheetahflags.columns.values)

print(' ')
print('------------- Reading of parametric model config file ------------- ')
df_POM_par,df_POM_parT=pr.read_POM_config(pom_config_file)
print('=== transposed POM config column values:')
print(df_POM_parT.columns.values)

print('------------- Check existing POM modules versus the wanted ones------------- ')
df_POM_run_flags=pr.wanted_vs_exist(pom_exist_flags, df_POM_parT,df_cheetahflags,df_cheetah)
print(df_POM_run_flags)

#------------------------------------------------------------------------------
# use configs to populate POM parameters, available globally
#------------------------------------------------------------------------------
class g:
    """
    Class to store global parameters
    
    """
    
    number_of_runs=df_POM_parT.number_of_runs.iloc[0]  # how many simulations
    sim_duration=df_POM_parT.sim_duration.iloc[0]      # run time of one sim

    obs_length= df_POM_parT.obs_length.iloc[0]         #  observation length in time
    chunk_buffer_length= df_POM_parT.chunk_length.iloc[0]  # chunk size in time
    N_chunks = np.round(obs_length/chunk_buffer_length)    # number chunks per obs
  #    chunk_buffer_size= chunk_buffer_length * 8 # in bits [for now time *8 bit]
    
# time of RCP module to process one chunk of data    
    t_RCP_i =df_POM_parT.t_RCP_i.iloc[0]
# time to put one chunk in output buffer of FFBC    
#    time_chunk_in_output=3   
    t_FFBC_i=df_POM_parT.t_FFBC_i.iloc[0]  
    
# time to write out [modified] observation [all chunks] data + other output    
#    time_obs_in_output=10   
    t_CDOS_all=df_POM_parT.t_CDOS_all.iloc[0]  
    t_CDOS_sps=df_POM_parT.t_CDOS_sps.iloc[0]  
    
    available_cpu_ram = df_POM_parT.available_cpu_ram.iloc[0] # needs to be integer



#print(g.available_cpu_ram, g.t_CDOS_all, g.t_CDOS_sps,g.number_of_runs, 
#      g.obs_length, g.chunk_buffer_length,g.t_RCP_i,g.t_FFBC_i)

#------------------------------------------------------------------------------
#  general class definitions
#------------------------------------------------------------------------------

# Class representing one observation in one beam     
class Observation:
    def __init__(self,obs_id_in):
        self.obs_id=obs_id_in
        self.time_wo = 0
#        print('obs {}'.format(self.obs_id))
           
# Class representing one data chunk of a observation
class Chunk:
    def __init__(self,obs_id_in,chunk_id_in):
        self.obs_id2=obs_id_in
        self.chunk_id=chunk_id_in
        self.time_wc = 0
        print('--- obs {}'.format(self.obs_id2),' chunk {}'.format(self.chunk_id))


#------------------------------------------------------------------------------
#    
#------------------------------------------------------------------------------
class PSS_POM:
    def __init__(self):
        self.env = simpy.Environment()
        self.obs_counter = 0
        self.chunk_counter = 0
        # Set up ressources : actual resources
        self.cpu_ram = simpy.Resource(self.env,capacity = g.available_cpu_ram)
        
        # Set up ressources : helper resources to ensure conditions are met        
        self.FB_work_store = simpy.Store(self.env, capacity=1)
        
        
    def run(self):
        global out_data
        self.env.process(self.run_pss())
        self.env.run(until=g.sim_duration)
        print(out_data)


    def run_pss(self):
        """
        Main simulation part

        Returns
        -------
        out_data : pandas data frame with times of different event states

        """
        global out_data
        self.FB_work_store.put(1)  # 1/1 in store
        
        # if changed look for 'initialize' to update
        out_data=pd.DataFrame({'obs':[0],     #obsID
                               'chunk':[0],   #chunk ID
                               'time_r':[0],  #time when chunk has been read in 
                               'time_c':[0],  
                               #time when [later modified] chunk has been collected for obsID
                               'time_oo':[0]
                               #time when [modified] obsID is written out 
                               })


        # keeps generating observations
        while True:
            # --- Create/get new observation
            # --- Increment the obs counter
            self.obs_counter += 1
            time_obsID_started = self.env.now
            print('- obs counter: ',self.obs_counter,
                  ', started at time ',time_obsID_started)
            obs = Observation(self.obs_counter)
            # need to set 0 for each new observation
            self.chunk_counter = 0
            
            
            #  generate_data_chunks_for_one_obs until number-of-chunks is reached
            while self.chunk_counter < (g.N_chunks):
                  self.chunk_counter += 1
                  
                  # initialize each row in output data frame
                  out_data.loc[len(out_data)]= [self.obs_counter,self.chunk_counter,0,0,0]
                  #print(out_data)
                  
                  # reserve FB work resource to let output routine know when done 
                  # [then put back in store]
                  if (self.chunk_counter == g.N_chunks):
                      FB_work_store_item = yield self.FB_work_store.get() 
                      #now 0/1 in store
                      print('got FB_store', FB_work_store_item, 'at', self.env.now)       
                  
                  # *** Event: read 1 data chunk; wait until finished
                  evt_read_chunks = self.env.process(self.generate_data_1chunk_for_one_obs(obs,self.chunk_counter))
                  yield evt_read_chunks                  
                
 
    # TBD: Include other SPS/PSS processing steps 


                  # *** Event:  collect (processed) data chunk into structure 
                  # for folding, ..., output 
                  # runs immediately and synchronously
                  evt_collect_chunks = self.env.process(self.add_chunk_to_outbuffer(obs.obs_id,self.chunk_counter))
                 

            # end of chunks-of-one-observation loop 
            z_time_read_collect_chunk=self.env.now
            print(' time after chunk loop: ', z_time_read_collect_chunk)
            
            # *** Event: output of [full] observation
            # synchronous, BUT read-in may not have yet ended, 
            #   condition for completed read-in is in event process itself
            evt_obs_out = self.env.process(self.out_obs_data(self.obs_counter)) 
             
            time_obsID_transmitted = self.env.now
            print('- obs counter: ',self.obs_counter,', transmitted after ', 
                  (time_obsID_transmitted-time_obsID_started))
        
            
            
            
            
            
            
    #--------------------------------------------------------------------------
    #  The Receptor Module: generate data chunks from data
    #--------------------------------------------------------------------------
    def generate_data_1chunk_for_one_obs(self,obs_in,chunk_counter):  
            global out_data
            time_chunkID_started = self.env.now
#            print(' current time is ',self.env.now)
            chunk = Chunk(obs_in.obs_id,self.chunk_counter)
        
            #  needed time is chunk-observing time [obs data need first to arrive] 
            #               + chunk processing time [t_RCP_i which should be 0!]
            time_to_next_chunk =  g.t_RCP_i + g.chunk_buffer_length
            # Freeze this function until this time has elapsed
            yield self.env.timeout(time_to_next_chunk)
            time_chunkID_ended = self.env.now

            mask= (out_data.obs == obs_in.obs_id) & (out_data.chunk == chunk_counter)
            out_data['time_r'].loc[mask]=self.env.now
            print('--- read-in of chunk ',self.chunk_counter,' of obs',
                  chunk.obs_id2,' ended after ', 
                  (time_chunkID_ended-time_chunkID_started))

    #--------------------------------------------------------------------------
    #  FFBC:  collect all [later modified] chunks of one obs for folding, CDOS  
    #--------------------------------------------------------------------------

    def add_chunk_to_outbuffer(self,obs_id_in,chunk_id_in):
            global out_data
            if (chunk_id_in == g.N_chunks):
                #--- check if already run or not for correct chunk, 
                #   ensures asynchronous processing           
                mask1= (out_data.obs == obs_id_in) & (out_data.chunk == chunk_id_in)
                aus_out_data=out_data[mask1]
                aus_out_data.reset_index(inplace=True,drop=True)
                time_r_val=aus_out_data['time_r'][0]
                time_c_val=aus_out_data['time_c'][0]
            
                # only if read in AND collecting not yet done, then do
                if (time_r_val > time_c_val):

# ---- double check this yield condition when more processing is included !
# could be shorter then
                    # needed time is buffer transfer time
                    yield self.env.timeout(g.t_FFBC_i)  
                    
                    # *** mask can have changed due to asynchronous processes, 
                    # adding new data, need to obtain again ***                
                    mask11= (out_data.obs == obs_id_in) & (out_data.chunk == chunk_id_in)
                    out_data['time_c'].loc[mask11]=self.env.now
                    self.FB_work_store.put(1)
                    print('add_: put back FB_work_store item at', self.env.now) 
                    # now in condition store: 1/1, next get can work

            if (chunk_id_in < g.N_chunks):
                # check if already run or not for correct chunk, 
                # ensures asynchronous processing           
                mask1= (out_data.obs == obs_id_in) & (out_data.chunk == chunk_id_in)
                aus_out_data=out_data[mask1]
                aus_out_data.reset_index(inplace=True,drop=True)
                time_r_val=aus_out_data['time_r'][0]
                time_c_val=aus_out_data['time_c'][0]

                # only if read in AND collecting not yet done, then do
                if (time_r_val > time_c_val):
                    # needed time is buffer transfer time
                    yield self.env.timeout(g.t_FFBC_i)  
# ---- double check this yield condition when more processing is included !
# could be shorter then

                    # *** mask can have changed due to asynchronous processes, 
                    # adding new data, need to obtain again ***                
                    mask11= (out_data.obs == obs_id_in) & (out_data.chunk == chunk_id_in)
                    out_data['time_c'].loc[mask11]=self.env.now
                
               
# could be witten per chunk, currently done per observation

    #--------------------------------------------------------------------------
    #  CDOS module: output one full observation 
    #                      [condition: after all modified chunks assembled]  
    #--------------------------------------------------------------------------
    def out_obs_data(self,obs_id_in):
            global out_data
            
            # this routine can only proceed if there is an item in the store!
            FB_work_store_item = yield self.FB_work_store.get()
            print('out_: got FB_work_store', FB_work_store_item, 'at', self.env.now)
            # store: 0/1

            masko1= (out_data.obs == obs_id_in)
            aus_out_datao1=out_data[masko1]
            aus_out_datao1.reset_index(inplace=True,drop=True)
            # only do if last chunk read and [modified one] collected
            time_r_val=aus_out_datao1['time_r'][g.N_chunks-1]
            time_c_val=aus_out_datao1['time_c'][g.N_chunks-1]
            if ((time_r_val > 0) & (time_c_val > 0)):
                yield self.env.timeout(g.t_CDOS_all)  
                # in case mask changed                
                masko11= (out_data.obs == obs_id_in)
                out_data['time_oo'].loc[masko11]=self.env.now
            # restore store: 1/1    
            self.FB_work_store.put(1)
            print('out_: put back FB_work_store at', self.env.now)







#------------------------------------------------------------------------------
#  
#------------------------------------------------------------------------------













#------------------------------------------------------------------------------
#  run the POM for number of runs 
#------------------------------------------------------------------------------
for run in range(g.number_of_runs):
    print("Run ", run+1, " of ", g.number_of_runs)
    pom1=PSS_POM()
    pom1.run()
    print('***** end time for run ',run,' : ',pom1.env.now)
