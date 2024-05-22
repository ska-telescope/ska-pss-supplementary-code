import matplotlib.pyplot as plt
import numpy as np
from modules.template_generator import Template
from modules.template_generator import filter_padding_and_fft
from modules.template_generator import final_filter_write
from modules.template_generator import final_filter_read
from modules.template_generator import filters

f1=open('template_integer.dat','rb')
f2=open('fitlers_little_endian.dat','rb')

for i in range(42):

    matlab_file=final_filter_read(f1)
    matlab_file.read_little_endian()
    real=matlab_file.real
    imag=matlab_file.imag
    filter_fft1=real+1j*imag

#    plt.plot(np.abs(filter_fft1))

    matlab_file=final_filter_read(f2)
    matlab_file.read_little_endian()
    real=matlab_file.real
    imag=matlab_file.imag
    filter_fft2=real+1j*imag

#    plt.plot(np.abs(filter_fft2))
#    plt.show()

    plt.plot(np.angle(filter_fft1),label='matlab')
    plt.plot(np.angle(filter_fft2),label='python')
    plt.legend()
    plt.show()

    filter1=np.fft.ifft(filter_fft1)
    filter2=np.fft.ifft(filter_fft2)
    plt.plot(np.abs(filter1),label='matlab')
    plt.plot(np.abs(filter2),label='python')
    plt.legend()
    plt.show()

    plt.plot(np.angle(filter1),label='matlab')
    plt.plot(np.angle(filter2),label='python')
    plt.legend()
    plt.show()   