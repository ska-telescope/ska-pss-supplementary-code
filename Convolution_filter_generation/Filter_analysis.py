#### This code was written to generate some diagnostic plots of filters #######


import matplotlib.pyplot as plt
import numpy as np
from modules.template_generator import Template

#####   Convolution result for integer bin filter   ######
plt.xlabel('Trial drift (bins)')
plt.ylabel('Recovered power')
bins0_list=[50]
for bins0 in bins0_list:
    detections=[]
    detections_inc=[]
    bins0=bins0
    trial_range=np.arange(bins0-20,bins0+21,0.1)

    filter0=Template(bins0).template
    for bin in trial_range:
        filter=Template(bin).template
        power=np.max(np.abs(np.convolve(filter, np.conjugate(filter0), 'full')))
        detections.append(power)
        power_inc=np.max(np.abs(np.convolve(np.abs(filter), np.abs(filter0), 'full')))
        detections_inc.append(power_inc)

    plt.plot(trial_range,detections,label='real drift '+str(bins0)+' bins')
#    plt.scatter(trial_range,detections)
    plt.plot(trial_range,detections_inc,ls='--',c='k')
    plt.axvline(x=bins0-2.5,c='r',ls='dashed',alpha=0.4)
    plt.axvline(x=bins0+2.5,c='r',ls='dashed',alpha=0.4)
plt.axhline(y=0.834,c='r',ls='dashed',alpha=0.4)
plt.grid(which='both',alpha=0.5)
plt.legend()
plt.show()

#####   Filter phase comparison  ######

trial_drifts=[30.5,60.5]
plt.xlabel('Filter Taps (frequency bins)')
plt.ylabel('Phase (degrees)')
for drift in trial_drifts:
    q,qt=Template(drift).phase()
    plt.plot(q,qt,label='Drift '+str(drift))
plt.legend()
plt.show()

#####   Filter amplitude comparison  ######

trial_drifts=[30.5,60.5]
plt.xlabel('Filter Taps (frequency bins)')
plt.ylabel('Amplitude')
for drift in trial_drifts:
    q,qt=Template(drift).amplitude()
    plt.plot(q,qt,label='Drift '+str(drift))
plt.legend()
plt.show()

####  Loss in 5 bin seperation of filter widths #####


plt.xlabel('Trial drift (bins)')
plt.ylabel('Recovered power')
bins0_list=[1,2,3,4,5]
for bins0 in bins0_list:
    detections=[]
    detections_inc=[]
    bins0=bins0
    trial_range=np.arange(bins0-(bins0-1),bins0+10)

    filter0=Template(bins0).template
    for bin in trial_range:
        filter=Template(bin).template
        power=np.max(np.abs(np.convolve(filter, np.conjugate(filter0), 'full')))
        detections.append(power)
        power_inc=np.max(np.abs(np.convolve(np.abs(filter), np.abs(filter0), 'full')))
        detections_inc.append(power_inc)

    plt.plot(trial_range,detections,label='real drift '+str(bins0)+' bins')
#    plt.plot(trial_range,detections_inc,ls='--',c='k')
    plt.axvline(x=5.0,c='r',ls='dashed',alpha=0.4)
#    plt.axvline(x=bins0+2.5,c='r',ls='dashed',alpha=0.4)
#    plt.axhline(y=0.834,c='r',ls='dashed',alpha=0.4)
plt.grid()
plt.legend()
plt.show()

filter1=Template(150.0).template
filter2=Template(150.5).template
filter3=Template(149.5).template

phase1=np.angle(filter1)*180.0/np.pi
phase2=np.angle(filter2)*180.0/np.pi
phase3=np.angle(filter3)*180.0/np.pi
phase12=phase2[:301]-phase1
phase13=phase1[:300]-phase3
plt.xlabel('Filter taps')
plt.ylabel('Phase (degrees)')
plt.plot(phase12,label='Phase difference between filters of drift 150 and 150.5 bins')
plt.plot(phase13,label='Phase difference between filters of drift 150 and 149.5 bins')
plt.legend()
plt.show()