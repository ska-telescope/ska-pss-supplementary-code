### This python program works on logfile generated as a result of FDAS run. It flags most of the duplicate detections in the neighbouring FoP bins.
### But this code still does not have capability to flag related harmonics. A functionality to flag the harmonically related detections should be implmented.
### Also, the code should be tested on negative accelerations. 

import matplotlib.pyplot as plt
import numpy as np
from ast import literal_eval

def read_logfile(logfile):
    harmonic_list=[]
    frequencybin_list=[]
    Filter_list=[]
    Power_list=[]
    f=open(logfile,'r')
    filenames=[]
    trigger=0
    run_start=0
    results_start=0
    results_end=0
    for line in f:
        if(line=='Triggering ...\n'):
            trigger=1

        if(trigger==1):
            if(line!='Triggering ...\n'):
                filenames.append(line)
                trigger=0
                file_name=line
        if(line=='ANALYSIS RUN 1\n'):
            run_start=1
        if(line=='=========================================================\n'):
            if(run_start==1):
                results_start=1
                results_end=0
                harmonic=[]
                frequency_bin=[]
                Filter_num=[]
                Power=[]
        if(line=='SIFTED RESULT\n'):

            results_start=0
            results_end=1
            harmonic=np.array(harmonic)
            frequency_bin=np.array(frequency_bin)
            Filter_num=np.array(Filter_num)
            Power=np.array(Power)
            frequencybin_list.append(frequency_bin)
            Power_list.append(Power)
            Filter_list.append(Filter_num)
            harmonic_list.append(harmonic)

        if(results_start==1):
            if(results_end==0):
                if(line!='=========================================================\n'):
                    s=[str(r) for r in line.split()]
                    harmonic.append(int(s[0]))
                    frequency_bin.append(int(s[1]))
                    Filter_num.append(int(s[3]))
                    Power.append(float(s[5]))
    return filenames, harmonic_list, frequencybin_list, Filter_list, Power_list

def uniq_values(harmonic,freq,accel,power):
    hms=8
    uniq_frq=[]
    uniq_accl=[]
    uniq_pwr=[]
    for hrmc in range(hms):
        hmc=hrmc
        frq_list=[]
        accl_list=[]
        pwr_list=[]
        indices=np.where(harmonic==hmc)
        if(len(indices)!=0):
            freq1=freq[indices]
            accel1=accel[indices]
            power1=power[indices]
            uniq_freq=np.unique(freq1)
            for uniqf in uniq_freq:
                indices1=np.where(freq1==uniqf)
                if(len(indices1)!=0):
                    accel2=accel1[indices1]
                    power2=power1[indices1]
                    uniq_accel=np.unique(accel2)
                    for uniqa in uniq_accel:
                        indices2=np.where(accel2==uniqa)
                        power3=power2[indices2]
                        pwr=max(power3)
                        frq_list.append(uniqf)
                        accl_list.append(uniqa)
                        pwr_list.append(pwr)
        uniq_frq.append(frq_list)
        uniq_accl.append(accl_list)
        uniq_pwr.append(pwr_list)
    return uniq_frq, uniq_accl, uniq_pwr

def sift_data(harmonic,freq,accel,power):
    hms=8
    uniq_frq, uniq_accl, uniq_pwr = uniq_values(harmonic,freq,accel,power)

    fseed_list=[]
    aseed_list=[]
    pseed_list=[]

    for hm in range(hms):
        seed_f=np.array(uniq_frq[hm])
        seed_a=43-np.array(uniq_accl[hm])
        seed_p=np.array(uniq_pwr[hm])
        seed_f, seed_a, seed_p = flag_within_harmonic(seed_f,seed_a,seed_p,hm)
        fseed_list.append(seed_f)
        aseed_list.append(seed_a)
        pseed_list.append(seed_p)
    return fseed_list, aseed_list, pseed_list



def flag_within_harmonic(freq,acc,pwr,hm):
    hm=hm+1
    summing_tree=[]
    seed_f=freq
    seed_a=acc
    seed_p=pwr
    if(hm != 1):
        seed_frq=[]
        seed_acc=[]
        seed_pwr=[]
        for fseed in seed_f:
            f0=np.round(fseed/float(hm))
            fl=np.round(hm*(f0-0.5))
            fu=np.round(hm*(f0+0.5))
            indices=np.intersect1d(np.where(seed_f>=fl), np.where(seed_f<=fu))
            if(len(indices)==0):
                continue
            seed_f1=seed_f[indices]
            seed_a1=seed_a[indices]
            seed_p1=seed_p[indices]
            for aseed in seed_a1:
                a0=np.round(aseed/float(hm))
                al=np.round(hm*(a0-0.5))
                au=np.round(hm*(a0+0.5))
                indices1=np.intersect1d(np.where(seed_a1>=al), np.where(seed_a1<=au))
                if(len(indices1)==0):
                    continue
                seed_f2=seed_f1[indices1]
                seed_a2=seed_a1[indices1]
                seed_p2=seed_p1[indices1]
                index=np.where(seed_p2==max(seed_p2))[0][0]
                power_gp=seed_p2[index]
                frequency_gp=seed_f2[index]
                acceleration_gp=seed_a2[index]
                summing_tree.append([frequency_gp,acceleration_gp,power_gp])
                seed_frq.append(frequency_gp)
                seed_acc.append(acceleration_gp)
                seed_pwr.append(power_gp)
                indices2=indices[indices1]
                seed_f1=np.delete(seed_f1,indices1)
                seed_a1=np.delete(seed_a1,indices1)
                seed_p1=np.delete(seed_p1,indices1)                
                seed_f=np.delete(seed_f,indices2)
                seed_a=np.delete(seed_a,indices2)
                seed_p=np.delete(seed_p,indices2)
                if(len(seed_f1)==0):
                    break
            if(len(seed_f)==0):
                break
        seed_frq=np.array(seed_frq)
        seed_acc=np.array(seed_acc)
        seed_pwr=np.array(seed_pwr)
    else:
        seed_frq=seed_f
        seed_acc=seed_a
        seed_pwr=seed_p
    return seed_frq, seed_acc, seed_pwr







######    Main Body   #######
duration=536.87
c=2.998e8
logfile='Loop_signal_to_noise_vectors_500Hz_20_m_s_s_uniform_filters_integer_matlab_domed_power_thresholds.log'
files,hm,fr,ac,pw = read_logfile(logfile)
f=open(logfile.split('.')[0]+'_sifted.txt','w')
filenum=len(hm)

for num in range(filenum):
    f.write('\n')
    f.write('\n')
    f.write(files[num]+'\n')
    f.write('Harmonic    Frequency (Hz)    acceleration (m/ss)    Power\n')
    f.write('============================================================\n')
    harmonic=hm[num]
    frequency=fr[num]
    accel=ac[num]
    power=pw[num]
    fseed_list,aseed_list,pseed_list=sift_data(harmonic, frequency, accel, power)
    for h in range(len(fseed_list)):
        frequencies=np.array(fseed_list[h])*1.0/duration
        accelerations=np.array(aseed_list[h])*5.0*c/(frequencies*duration**2)
        powers=np.array(pseed_list[h])
        for j in range(len(frequencies)):
            f.write(str(h)+'   '+str(frequencies[j])+'   '+str(accelerations[j])+'   '+str(powers[j])+'\n')

f.close()

    


    