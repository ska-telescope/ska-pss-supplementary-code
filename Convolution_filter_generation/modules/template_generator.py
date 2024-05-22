import matplotlib.pyplot as plt
import numpy as np
import scipy
import struct

### A class filters to hold both multiplicative and uniformly sampling of filter width
class filters:
    ### Constructor
    def __init__(self):
        ### Multiplicative filters
        self.multiplicative=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 28, 31, 34, 38, 42, 46, 51, 56, 62, 69, 76, 84, 93, 103, 114, 126, 139, 154, 170, 188, 208, 230, 254]
        filters2=[1]           # Filter 2 is uniformly sampled filters
        ### Uniform filters
        for i in range(1,43):
            filters2.append((i*5))
        self.uniform=filters2

###  Function to compute filter templates
def Compute_template(drift):
    ### Bin range to compute template for
    q=np.arange(-drift,drift+1,1.0)
    ### Variable for the left side edge
    Y=np.sqrt(2.0/drift)*(q-drift/2.0)
    ### Variable for the right side edge
    Z=np.sqrt(2.0/drift)*(q+drift/2.0)

    ### Computing the fresnels integrals for the two variables
    Sy, Cy=scipy.special.fresnel(Y)
    Sz, Cz=scipy.special.fresnel(Z)

    ### Extra phase term of the template
    template1=1.0/np.sqrt(2.0*drift)*np.exp(1j*np.pi*(q-drift/2.0)**2.0/drift)
    ### Combination of the fresnel integrals for the filter template
    template2=(Sz - Sy + 1j*(Cz-Cy))
    ### Final template
    template=template1*template2
    return template

###  Class to represent filter templates 
class Template:
    ### Constructor
    def __init__(self,drift):
        self.drift=drift
        self.template=Compute_template(drift)

    ### Method to return amplitudes of the templates
    def amplitude(self):
        q=np.arange(-self.drift, self.drift + 1, 1.0)
        qt=np.abs(self.template)
        return q, qt
    
    ### Method to return phases of the templates
    def phase(self):
        q=np.arange(-self.drift, self.drift + 1, 1.0)
        qt=np.angle(self.template)*180.0/np.pi
        return q, qt

class filter_padding_and_fft:
    ###  Constructor  ####
    def __init__(self,filter,fil_len,max_fil_len,fft_len):
        self.filter=filter
        self.fil_len=fil_len
        self.fft_len=fft_len
        self.max_fil_len=max_fil_len
    ###  Padding to make it 1024 taps
    def padding(self):
        zeros=np.zeros(self.fft_len-self.fil_len,dtype=float)
        complex_zeros=zeros + 1j*zeros
        padded_filter=np.concatenate((self.filter,complex_zeros))
        padded_filter=np.roll(padded_filter,int(self.max_fil_len/2.0 - self.fil_len/2.0))
        self.filter=padded_filter
    ###  FFT of the padded filters
    def fft(self):
        filter_fft=np.fft.fft(self.filter)
        self.filter=filter_fft

###  Class to write filters in text and binary files
class final_filter_write:
    def __init__(self,filter_fft,file_base):   ###  filter_fft is fft of the filter and file_base is the pointer to opened file
        self.filter=filter_fft
        self.file=file_base
    
### Write out in binary file with little endian format
    def write_little_endian(self):
        for element in self.filter:
            bytes_seq=struct.pack('<ff',element.real,element.imag)
            self.file.write(bytes_seq)

### Writeout in binary file with big endian format
    def write_big_endian(self):
        for element in self.filter:
            bytes_seq=struct.pack('>ff',element.real,element.imag)
            self.file.write(bytes_seq)

###  Reading a binary file in little endian format
class final_filter_read:
    def __init__(self,file_base):
        self.file=file_base
        self.length=1024
    
    def read_little_endian(self):
        filter_real=[]
        filter_imag=[]
        for itr_num in range(self.length):
            byte_seq=self.file.read(8)
            float_seq=struct.unpack('<ff',byte_seq)
            filter_real.append(float_seq[0])
            filter_imag.append(float_seq[1])
        self.real=np.array(filter_real)
        self.imag=np.array(filter_imag)


