//  make
// example call: ./cusanity > inout.csv &
// uses in-place data calc
//
// uses sine signal+ND-noise in real part of the complex input vector, just ND-noise for imaginary part
// writes out input sine wave, input array (real+ima) and then output array (real, ima) of each run 
// for double checking with other FFT routines and recovering test of input sine signal


#include <stdlib.h>
#include <math.h>
#include <complex.h>
#include <iostream>
#include <chrono>
#include <random>

// following
//https://github.com/NVIDIA/CUDALibrarySamples/blob/master/cuFFT/1d_c2c/1d_c2c_example.cpp
//https://docs.nvidia.com/cuda/cufft/index.html#function-cufftexecc2c-cufftexecz2z
#include <cufftXt.h>
#include <cuda_runtime.h>

//#include <cufft_utils.h>
//------- not found on sharabha

// ----- how many tests with the same plan?
auto numruns=2;
int Narray[]={1024*1024*2};


#define tscan 10.0*60.0 

int main()
{
    std::random_device rd;
    std::mt19937 rng(rd());
    std::normal_distribution<float> generate_data(128,10 );
    std::normal_distribution<float> generate_amplitude(30,5 );
    std::normal_distribution<float> generate_frequency(1000,10 );

    std::cout<<"cuFFTWwhat,amp,freq,runid,idx,t_freq,real,ima\n";

 // ----- how many of the Ns should be done?
    for (int ni {0}; ni<1; ++ni)
    {
        int Nlauf=Narray[ni];    
// handles for plan and (default) stream        
        cufftHandle plan;
        cudaStream_t stream = NULL;

        using scalar_type = float;
        using data_type = std::complex<scalar_type>;


// --- define data array [CPU]
        std::vector<data_type> input_data(Nlauf);

// --- define data array pointer (GPU)
        cufftComplex *d_data = nullptr;

// cuda has only one plan, not estimate/measure
        int batchnr =1;   // maybe to be changed later [combining several DM-data sets here could help with speed]
        cufftCreate(&plan);
        cufftPlan1d(&plan, Nlauf, CUFFT_C2C, batchnr);

// Create device data arrays --- this should only be done once (cudafree also only done once)
        cudaMalloc(reinterpret_cast<void **>(&d_data), sizeof(data_type) * input_data.size());


// ============================= FORWARD
//------- do for the same N (same plan), numruns times
        for(int k=0; k<numruns; k++)
        {
           double freq=generate_frequency(rng);
           double amp=generate_amplitude(rng);
           for(int i=0; i<Nlauf; i++)
            {
                double t = static_cast<double>(i)* tscan / static_cast<double>(Nlauf);
                double pulse_i=amp * std::sin(2.0 * M_PI * freq * t); 
    //            input_data[i][0] = pulse_i + generate_data(rng);
    //            input_data[i][1] = generate_data(rng);
                input_data[i] = data_type(pulse_i+generate_data(rng), generate_data(rng));
                std::cout<<"cuFFTWin,"<<amp<<","<<freq<<","<<k<<","<<i<<","<<t<<","<<input_data[i].real()<<","<<input_data[i].imag()<<"\n";
            }


//--------- start stop watch here
            auto fft_start = std::chrono::high_resolution_clock::now();
 // copy input_data (CPU) to d_data (GPU)
            cudaMemcpy(d_data, input_data.data(), sizeof(data_type) * input_data.size(), cudaMemcpyHostToDevice);

    /*
     * Note:
     *  Identical pointers to data and output arrays implies in-place transformation
     */
            cufftExecC2C(plan, d_data, d_data, CUFFT_FORWARD);
 
//CUDA kernels are asynchronous, 
//forces the program to wait for all previously issued commands in all streams on the device to finish before continuing
// can slow down program
            cudaDeviceSynchronize();

// copy.modified. d_data (GPU) to input_data (CPU) -> overwrite
            cudaMemcpy(input_data.data(), d_data, sizeof(data_type) * input_data.size(), cudaMemcpyDeviceToHost);
 
            auto fft_stop = std::chrono::high_resolution_clock::now();
//--------- end stop watch
//        std::cout<<"Time elapsed: "<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";

//        std::printf("Output array:\n");
            for (int i = 0; i < Nlauf; i++) {
                std::cout<<"cuFFTWout,0,0,"<<k<<","<<i<<","<<i<<","<<input_data[i].real()<<","<<input_data[i].imag()<<"\n";

            }
//        std::printf("=====\n");
//            std::cout<<"cufft,SINpND,"<<Nlauf<<",FORWARD,"<<k<<","<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";
        }


        /* free resources */
        cudaFree(d_data);

        cufftDestroy(plan);

        cudaStreamDestroy(stream);

        cudaDeviceReset();
    }
    return 0;
}
