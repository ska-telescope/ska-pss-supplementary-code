import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def return_addr(summer1,run1,seed1,slope1,harmonic1):
    addr=hex(int(0x1800000)+summer1*131072+run1*65536+seed1*2048+slope1*128+harmonic1*8)
    return '0'+addr.split('x')[1]

# Read the run1 and run 2 spreadsheet for each summer instance. Create a spreadsheet for each summer instance combining the two runs.

for summer in [0,1]:
    seed0=0
    seeds1=[]
    extra_padding=2
    S=[]
    Sl=[]
    H1=[]
    H2=[]
    H3=[]
    H4=[]
    H5=[]
    H6=[]
    H7=[]
    H8=[]
    for run in [0,1]:            
        df=pd.read_excel('Complete_HPSEL_run'+str(run+1)+'_seed_slope_harmonic_values_summer'+str(summer+1)+'.xlsx')
        seed1=run*21
        seed2=seed1+21
        for seed in np.arange(seed1,seed2):      ## Loop aims to read all used rows in the given run
            for slope in range(0,11):
                row_idx=(seed-seed1)*11+slope
                if(df.loc[[row_idx]].to_numpy()[0][3] != '0x60'):
                    row_info=df.loc[[row_idx]].to_numpy()[0]
                    S.append(row_info[1])
                    Sl.append(row_info[2])
                    H1.append(row_info[3])
                    H2.append(row_info[4])
                    H3.append(row_info[5])
                    H4.append(row_info[6])
                    H5.append(row_info[7])
                    H6.append(row_info[8])
                    H7.append(row_info[9])
                    H8.append(row_info[10])

## Define empty lists to store the 5 slope configuration of the used rows
    rows=len(H1)
    S1=[]
    Sl1=[]
    H11=[]
    H21=[]
    H31=[]
    H41=[]
    H51=[]
    H61=[]
    H71=[]
    H81=[]
    i=0   
    print(max(S))
    print(rows)
    for idx in range(rows):

        ##  Append the five consecutive used rows in the list
        S1.append(S[idx])
        Sl1.append(i+1)
        H11.append(H1[idx])
        H21.append(H2[idx])
        H31.append(H3[idx])
        H41.append(H4[idx])
        H51.append(H5[idx])
        H61.append(H6[idx])
        H71.append(H7[idx])
        H81.append(H8[idx])
        seeds1.append(seed0)
        i=i+1
        if(idx == rows-1):          ##  After the last used row, fill remainign slopes with '0x60' value
            for j in range(11 - i):
                S1.append(S[idx])
                Sl1.append(i+j+1)
                H11.append('0x60')
                H21.append('0x60')
                H31.append('0x60')
                H41.append('0x60')
                H51.append('0x60')
                H61.append('0x60')
                H71.append('0x60')
                H81.append('0x60')
                seeds1.append(seed0)  
        if(i == 5):               ## After 5 consecutive rows, append next six rows with '0x60' value
            for j in range(6):
                S1.append(S[idx])
                Sl1.append(i+j+1)
                H11.append('0x60')
                H21.append('0x60')
                H31.append('0x60')
                H41.append('0x60')
                H51.append('0x60')
                H61.append('0x60')
                H71.append('0x60')
                H81.append('0x60')
                seeds1.append(seed0)
            i=0
            seed0=seed0+1

## 19 seeds were enough to capture all used summing instances. But to complete the 21 seed config of a run, we do a padding for rest of 2 seeds
    for k in range(extra_padding):
        seed0=seed0+1
        i=0
        for j in range(11):
            S1.append(S[idx])
            Sl1.append(i+j+1)
            H11.append('0x60')
            H21.append('0x60')
            H31.append('0x60')
            H41.append('0x60')
            H51.append('0x60')
            H61.append('0x60')
            H71.append('0x60')
            H81.append('0x60')
            seeds1.append(seed0)
        
        i=0


## Create a new dataframe for the given summer instance and save it to a file
    print(len(H1))
    print(len(seeds1))

    df1=pd.DataFrame({'Seed': S1, 'Slope':Sl1, 'H1':H11, 'H2':H21, 'H3':H31, 'H4':H41, 'H5':H51, 'H6':H61, 'H7':H71, 'H8':H81, 'Apr seed':seeds1})
    df1.to_excel('Complete_HPSEL_runs_combined_5slopes_seed_harmonic_values_summer'+str(summer)+'.xlsx')

