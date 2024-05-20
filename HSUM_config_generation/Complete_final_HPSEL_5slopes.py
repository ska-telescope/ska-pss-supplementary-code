import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os


def return_addr(summer1,run1,seed1,slope1,harmonic1):
    addr=hex(int(0x1800000)+summer1*131072+run1*65536+seed1*2048+slope1*128+harmonic1*8)
    return '0'+addr.split('x')[1]

#   Filters is the new multiplicatively sampled filters
filters1=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 28, 31, 34, 38, 42, 46, 51, 56, 62, 69, 76, 84, 93, 103, 114, 126, 139, 154, 170, 188, 208, 230, 254]
filter_pos_values=['0x00','0x02','0x04','0x06','0x08','0x0A','0x0C','0x0E','0x12','0x14','0x16','0x18','0x1A','0x1C','0x1E','0x22','0x24','0x26','0x28','0x2A','0x2C','0x2E','0x32','0x34','0x36','0x38','0x3A','0x3C','0x3E','0x42','0x44','0x46','0x48','0x4A','0x4C','0x4E','0x52','0x54','0x56','0x58','0x5A','0x5C','0x5E']
filter_neg_values=['0x01','0x03','0x05','0x07','0x09','0x0B','0x0D','0x0F','0x13','0x15','0x17','0x19','0x1B','0x1D','0x1F','0x23','0x25','0x27','0x29','0x2B','0x2D','0x2F','0x33','0x35','0x37','0x39','0x3B','0x3D','0x3F','0x43','0x45','0x47','0x49','0x4B','0x4D','0x4F','0x53','0x55','0x57','0x59','0x5B','0x5D','0x5F']

summer_inst=[]
run_inst=[]
seed_num=[]
seeds=[]
amb_slope=[]
harmonic_num=[]
address=[]
values=[]
values1=[]
widths=[]

run=0
rows=231
for summer in [0,1]:
    df=pd.read_excel('Complete_HPSEL_runs_combined_5slopes_seed_harmonic_values_summer'+str(summer)+'.xlsx')
    for row in np.arange(0,rows):
        harmonics=['H1','H2','H3','H4','H5','H6','H7','H8']
        for harmonic in np.arange(0,8):
            row_idx=row
            seed=df['Apr seed'][row_idx]
            seed1=df['Seed'][row_idx]
            slope=df['Slope'][row_idx]-1
            summer_inst.append(summer)
            run_inst.append(run)
            seed_num.append(seed)
            seeds.append(seed1)
            amb_slope.append(slope)
            harmonic_num.append(harmonic)
            address.append(return_addr(summer,run,seed,slope,harmonic))
            values.append(df[harmonics[harmonic]][row_idx])
            values1.append(str('000000')+df[harmonics[harmonic]][row_idx].split('x')[1])
            if(df[harmonics[harmonic]][row_idx]=='0x60'):
                widths.append(np.nan)
            else:
                indx=0
                if(summer==0):
                    indx=0
                    for str1 in filter_pos_values:
                        if(str1==df[harmonics[harmonic]][row_idx]):
                            break;
                        else:
                            indx=indx+1
                if(summer==1):
                    indx=0
                    for str1 in filter_neg_values:
                        if(str1==df[harmonics[harmonic]][row_idx]):
                            break;
                        else:
                            indx=indx+1    
                print(indx) 
                print(df[harmonics[harmonic]][row_idx])          
                widths.append(filters1[indx])

df1=pd.DataFrame({'summer':summer_inst, 'run':run_inst, 'seed':seed_num, 'Actual seed':seeds, 'slope':amb_slope, 'harmonic':harmonic_num, 'address':address, 'value':values, 'width':widths})
df1.to_excel('Complete_HPSEL_final_addresses_values_single_run_5slopes.xlsx')
df2=pd.DataFrame({'address':address, 'values':values1})
df2.to_csv('Complete_HPSEL_only_addresses_values_single_run_5slopes.txt',sep='\t',index=False,header=False)

f1=open('Complete_HPSEL_only_addresses_values_single_run_5slopes.txt','r')
f2=open('FDAS_config.txt','r')
f3=open('Complete_HPSEL_only_addresses_values_single_run_5slopes_with_config.txt','a')
for line in f2:
    f3.write(line)

f3.write('\n')
for line in f1:
    f3.write(line)
f1.close()
f2.close()
f3.close()