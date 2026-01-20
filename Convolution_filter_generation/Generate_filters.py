import matplotlib.pyplot as plt
import numpy as np
import argparse
from modules.template_generator import Template
from modules.template_generator import filter_padding_and_fft
from modules.template_generator import final_filter_write
from modules.template_generator import filters

### Parsign arguments  #######

parser = argparse.ArgumentParser(description ='Generates convolution filters for acceleration search (developed for PSS-Cheetah).')

parser.add_argument('-num_filters',
                    type = int,
                    default=43,
                    required = False,
                    help ='Number of filters to generate (default: 43 for chettah-fpga-fdas)')

parser.add_argument('-fil_sep',
                    type = int,
                    default=4,
                    required = False,
                    help ='Seperation between two consecutive filters (default: 4 for Cheetah-fpga-fdas)')

parser.add_argument('-fft_len',
                    type = int,
                    default=1024,
                    required = False,
                    help ='FFT length used for padding and fft (default: 1024)')


parser.add_argument('-outfile',
                    type = str,
                    default= 'fitlers_little_endian.dat',
                    required = False,
                    help ='Name of the output file (default: fitlers_little_endian.dat)')

args = parser.parse_args()

print("Generating filters with width spacing: "+str(args.fil_sep)+'\n')

### Number of drifts to generate generate filters for  ###  
widths=filters(args.num_filters, args.fil_sep).uniform[1:]                           ### Widths of filters excluding the 1 bin drift filter.
###  One can select multiplicative filters and any other filter choice after adding it to filters class of template_generator.py
print('Filters will be created for the following widths: \n')
print(widths)
max_drift = max(widths)
fft_len=args.fft_len              ### FFT length used by convlution process
max_fil_len=2*(max_drift)+1           ### Maximum size of filters

print("Maximum length of the fitler is: "+str(max_fil_len)+"\n")
### Open binary files to write out the FFT of padded filter templates ###
fl=open(args.outfile,'wb')
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
