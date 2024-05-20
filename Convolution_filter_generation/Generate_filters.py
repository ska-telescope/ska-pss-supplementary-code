import matplotlib.pyplot as plt
import numpy as np
from modules.template_generator import Template
from modules.template_generator import filter_padding_and_fft
from modules.template_generator import final_filter_write
from modules.template_generator import filters

### Number of drifts to generate generate filters for  ###  
widths=filters().uniform[1:]                           ### Widths of filters excluding the 1 bin drift filter.
###  One can select multiplicative filters and any other filter choice after adding it to filters class of template_generator.py
print('Filters will be created for the following widths: \n')
print(widths)

fft_len=1024              ### FFT length used by convlution process
max_fil_len=421           ### Maximum size of filters

### Open binary files to write out the FFT of padded filter templates ###
fl=open('fitlers_little_endian.dat','wb')
fb=open('fitlers_big_endian.dat','wb')

###  Generate filter for each value of drifts  ###
for drift in widths:
    filter=Template(drift).template                        ### Generate template for the drift
    fil_len=len(filter)                                    
    filter1=filter_padding_and_fft(filter,fil_len,max_fil_len,fft_len)    ### Genrating object to be used for padding and FFT
    filter1.padding()                                      ###  Padding with (0+i0) symmetrically
    filter1.fft()                                          ### Taking FFT of the padded fitler template
    fwritel=final_filter_write(filter1.filter,fl)          ### Object to write the in little endian format
    fwritel.write_little_endian()                          ### Writting in little endian format
    fwriteb=final_filter_write(filter1.filter,fb)          ### Object to write in big endian format
    fwriteb.write_big_endian()                             ### Writting in big endian format

###   Closing the binary files
fl.close()
fb.close()