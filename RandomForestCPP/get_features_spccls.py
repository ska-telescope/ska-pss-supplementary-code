import numpy as np
import matplotlib.pyplot as plt
#from scipy.optimize import curve_fit
import argparse
import sys
import os

parser = argparse.ArgumentParser(
    description="A python script to compute features from the clustered spccl files. Requires spccl files from cheetah (with clustering on but spsift off). The spccl files should be kept in a folders. Needs detection threshold (threshold used in cheetah SPDT) and a user defined sifting threshold. Writes out a text file with features of the clusters."
)

parser.add_argument(
    "-i",
    "--input_folder",
    help="Name of the folder containing all the spccl files."
)

parser.add_argument(
    "-th1",
    "--detection_threshold",
    type=float,
    help="Threshold used during detection."
)

parser.add_argument(
    "-th2",
    "--sifting_threshold",
    type=float,
    help="Threshold for sifting."
)

parser.add_argument(
    "-o",
    "--output_filename",
    help="Name of the txt file to write out features."
)
args = parser.parse_args()


input_folder = str(args.input_folder)
detection_threshold = args.detection_threshold
sifting_threshold = args.sifting_threshold
output_filename = str(args.output_filename)

def get_features(time, dm, width, snr, threshold):

    max_id = np.where(snr == max(snr))[0][0]
    max_width = width[max_id]
    max_dm = dm[max_id]
    best_dm = max_dm
    max_snr = max(snr)
    dm_width = (max(dm) - min(dm))
    time_width = (max(time) - min(time))
    cluster_size = len(snr)
    print('cluster size '+str(cluster_size)+'\n')
    print('Max width '+str(max_width)+'\n')
    print('DM width '+str(dm_width)+'\n')
    print('Time width '+str(time_width)+'\n')
    print('Max snr '+str(max_snr)+'\n')

    #######     DM SNR symmetry feature      ##############

    new_snr_level = threshold + 0.3*(max_snr - threshold)    ## 30% SNR level
    new_dm = []
    new_snr = []
    for ii in range(len(snr)):
        if(snr[ii] >= new_snr_level):
            new_dm.append(dm[ii])
    new_dm = np.array(new_dm)
    left_extent = max_dm - min(new_dm)
    right_extent = max(new_dm) - max_dm
    ds_symmetry = left_extent/right_extent


    #######  Flatness of DM SNR plot #########

    ds_flatness = (max(snr) - threshold)/(np.median(snr) - threshold)

    #######   DM Time features      ##########

    time = time - time[0]
    sumx = 0.0
    sumy = 0.0
    sumxy = 0.0
    sumxx = 0.0
    n = float(len(dm))
    for jj in range(len(dm)):
        sumx = sumx + time[jj]
        sumy = sumy + dm[jj]
        sumxx = sumxx + time[jj]*time[jj]
        sumxy = sumxy + time[jj]*dm[jj]
    slope = (sumx*sumy - n*sumxy)/(sumx*sumx - n*sumxx)
    offset = (sumy - slope*sumx)/float(n)

    deviation = 0.0
    for kk in range(len(dm)):
        deviation = deviation + (dm[kk] - (slope*time[kk]+offset))*(dm[kk] - (slope*time[kk]+offset))

    td_scatter = deviation/float(n)
    td_slope = slope

    features = [max_snr, best_dm, max_width, dm_width, time_width, cluster_size, ds_symmetry, ds_flatness, td_slope, td_scatter]
    return features


fw = open(output_filename+'.feature','w')
fw.write('Best_snr, Best_dm, Best_width, DM_width, Time_width, Cluster_size, DM_snr_symmetry, DM_snr_flatness, Time_DM_slope, Time_DM_scatter\n')
spccl_files = os.listdir(input_folder)
j=0
for file in spccl_files:
    mjd=[]
    dm=[]
    width=[]
    snr=[]
    labels = []
    i=0
    for line in open(input_folder+'/'+file,'r'):
        if(i != 0):
            s=[float(r) for r in line.split()]
            mjd.append(s[0]*3600.0*24.0*1000.0)  ## time ms
            dm.append(s[1])  ## Dispersiond measure
            width.append(s[2])     ## Width in ms
            snr.append(s[3])  
            labels.append(s[4])
        i=i+1

    time = np.array(mjd)-mjd[0]
    dm = np.array(dm)
    width = np.array(width)
    snr = np.array(snr)
    labels = np.array(labels)
    uniq_labels = np.unique(labels)
    if(uniq_labels[0] == 0):
        uniq_labels = uniq_labels[1:]

    for label in uniq_labels:
        time1 = []
        dm1 = []
        width1 = []
        snr1 = []
        for j in range(len(snr)):
            if(labels[j] == label):
                time1.append(time[j])
                dm1.append(dm[j])
                width1.append(width[j])
                snr1.append(snr[j])
        time1 = np.array(time1)
        dm1 = np.array(dm1)
        width1 = np.array(width1)
        snr1 = np.array(snr1)
        if(max(snr1) > sifting_threshold):
            features = get_features(time1, dm1, width1, snr1, detection_threshold)
            fw.write(str(features[0])+','+str(features[1])+','+str(features[2])+','+str(features[3])+','+str(features[4])+','+str(features[5])+','+str(features[6])+','+str(features[7])+','+str(features[8])+','+str(features[9])+'\n')
fw.close()

