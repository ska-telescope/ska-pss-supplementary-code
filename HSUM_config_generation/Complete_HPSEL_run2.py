import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

filters2=[]           # Filter 2 is uniformly sampled filters

for i in range(1,43):
    filters2.append(i*5)

#   Filters is the new multiplicatively sampled filters
filters1=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 28, 31, 34, 38, 42, 46, 51, 56, 62, 69, 76, 84, 93, 103, 114, 126, 139, 154, 170, 188, 208, 230, 254]
filter_pos_values=['0x00','0x02','0x04','0x06','0x08','0x0A','0x0C','0x0E','0x12','0x14','0x16','0x18','0x1A','0x1C','0x1E','0x22','0x24','0x26','0x28','0x2A','0x2C','0x2E','0x32','0x34','0x36','0x38','0x3A','0x3C','0x3E','0x42','0x44','0x46','0x48','0x4A','0x4C','0x4E','0x52','0x54','0x56','0x58','0x5A','0x5C','0x5E']
filter_neg_values=['0x01','0x03','0x05','0x07','0x09','0x0B','0x0D','0x0F','0x13','0x15','0x17','0x19','0x1B','0x1D','0x1F','0x23','0x25','0x27','0x29','0x2B','0x2D','0x2F','0x33','0x35','0x37','0x39','0x3B','0x3D','0x3F','0x43','0x45','0x47','0x49','0x4B','0x4D','0x4F','0x53','0x55','0x57','0x59','0x5B','0x5D','0x5F']

print(len(filters1))
filters=np.array(filters1)

# Define seed region 
seed_start=21
seed_end=42
seed_len=seed_end-seed_start
seeds_run1=filters[seed_start:seed_end]
transition=15   # Transition defines the filter number after which width sampling is multiplicative

def return_W(p):
    if(p==-1):
        return 0
    elif(p==len(filters)):
        return filters[-1]
    else:
        return filters[p]

def Nslopes(rl,rc):
    if (2*np.ceil((rc-rl)/2.0)+1)>9:
        slps=9
    else:
        slps=(2*np.ceil((rc-rl)/2.0)+1)
    return slps
    
    
def return_index(i,j,p,ho,amb0):
    picks=[1,3,3,5,5,7,7,9]
    if(picks[j]>amb0):
        amb=amb0
    else:
        amb=picks[j]
    if(j==0):
       if(i<(amb0/2.0)):
            if(p0-1<0):
                return p0
            else:
                return p0-1
       else:
           return p0
    else:
        corr=int(np.round((amb-1)/2.0))
        corrections=np.arange(-corr,corr+1)
        idx=int(np.floor((amb/float(amb0))*i))
        if(p+corrections[idx]<0):
            return 0
        elif(p+corrections[idx]<=41):
            return p+corrections[idx]
        else:
            return 42
    

seeds=[]
slopes=[]
AH=np.zeros((11*seed_len,8))
AW=np.zeros((11*seed_len,8))
AV1=[]
AV2=[]
for p0 in range(seed_start,seed_end):
    perr=(return_W(p0)-return_W(p0-1))
#    perrr=(return_W(p0+1)-return_W(p0))

#  Decide number of available harmonics
    if(8*seeds_run1[p0-seed_start] <= filters[-1]):
        harms=8
    else:
        for i in range(8):
            if((i+1)*seeds_run1[p0-seed_start] > filters[-1]):
                harms=i
                break

#  Decide number of ambiguity slopes
    if(p0>transition/2.0):
        if(p0<transition):
            amb_slopes=3
        else:
            amb_slopes=1
    else:
        th=int(float(transition)/filters[p0])
        Rl=np.argmin(np.abs(filters-((th*(filters[p0]-perr)))))
#        Rr=np.argmin(np.abs(filters-((th*(filters[p0]+perrr)))))
        Rc=np.argmin(np.abs(filters-((th*(filters[p0])))))
        amb_slopes=Nslopes(Rl,Rc)
        print(amb_slopes)
        
#  Work out filters for each harmonic of this seed
    filts=[]
    for j in range(1,harms+1):
        ph=np.argmin(np.abs(filters-np.ceil((j*(filters[p0]-perr/2.0)))))
        filts.append(ph)

 
    for i in range(0,11):
        seeds.append(p0)
        slopes.append(i+1)
        V1=[]
        V2=[]
        for j in range(0,8):
            if(i+1>amb_slopes):
                AH[(p0-seed_start)*11+i,j]=np.NAN
                AW[(p0-seed_start)*11+i,j]=np.NAN
                V1.append('0x60')
                V2.append('0x60')
            
            elif(j+1>harms):
                AH[(p0-seed_start)*11+i,j]=np.NAN   
                AW[(p0-seed_start)*11+i,j]=np.NAN
                V1.append('0x60')
                V2.append('0x60')
            else:
                AH[(p0-seed_start)*11+i,j]=return_index(i,j,filts[j],harms,amb_slopes)
                AW[(p0-seed_start)*11+i,j]=filters[return_index(i,j,filts[j],harms,amb_slopes)]
                V1.append(filter_pos_values[return_index(i,j,filts[j],harms,amb_slopes)])
                V2.append(filter_neg_values[return_index(i,j,filts[j],harms,amb_slopes)])
        AV1.append(V1)
        AV2.append(V2)

H1=AH[:,0]
H2=AH[:,1]
H3=AH[:,2]
H4=AH[:,3]
H5=AH[:,4]
H6=AH[:,5]
H7=AH[:,6]
H8=AH[:,7]
dataframe=pd.DataFrame({'seeds':seeds, 'slopes':slopes, 'H1':H1, 'H2':H2, 'H3':H3, 'H4':H4, 'H5':H5, 'H6':H6, 'H7':H7, 'H8':H8})
dataframe.to_excel('Complete_HPSEL_run2_seed_slope_harmonic_number.xlsx')
seeds1=seeds
seeds=filters[seeds]

H1=AW[:,0]
H2=AW[:,1]
H3=AW[:,2]
H4=AW[:,3]
H5=AW[:,4]
H6=AW[:,5]
H7=AW[:,6]
H8=AW[:,7]
dataframe=pd.DataFrame({'seeds':seeds, 'slopes':slopes, 'H1':H1, 'H2':H2, 'H3':H3, 'H4':H4, 'H5':H5, 'H6':H6, 'H7':H7, 'H8':H8})
dataframe.to_excel('Complete_HPSEL_run2_seed_slope_harmonic_width.xlsx')

H1=[]
H2=[]
H3=[]
H4=[]
H5=[]
H6=[]
H7=[]
H8=[]
for x in AV1:
    H1.append(x[0])
    H2.append(x[1])
    H3.append(x[2])
    H4.append(x[3])
    H5.append(x[4])
    H6.append(x[5])
    H7.append(x[6])
    H8.append(x[7])
dataframe=pd.DataFrame({'seeds':seeds1, 'slopes':slopes, 'H1':H1, 'H2':H2, 'H3':H3, 'H4':H4, 'H5':H5, 'H6':H6, 'H7':H7, 'H8':H8})
dataframe.to_excel('Complete_HPSEL_run2_seed_slope_harmonic_values_summer1.xlsx')

H1=[]
H2=[]
H3=[]
H4=[]
H5=[]
H6=[]
H7=[]
H8=[]
for x in AV2:
    H1.append(x[0])
    H2.append(x[1])
    H3.append(x[2])
    H4.append(x[3])
    H5.append(x[4])
    H6.append(x[5])
    H7.append(x[6])
    H8.append(x[7])
dataframe=pd.DataFrame({'seeds':seeds1, 'slopes':slopes, 'H1':H1, 'H2':H2, 'H3':H3, 'H4':H4, 'H5':H5, 'H6':H6, 'H7':H7, 'H8':H8})
dataframe.to_excel('Complete_HPSEL_run2_seed_slope_harmonic_values_summer2.xlsx')

