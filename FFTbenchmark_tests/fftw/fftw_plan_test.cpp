// to compile:  g++ -g -Wall -o fftw_plan_test fftw_plan_test.cpp -lfftw3 -lm
// to run: ./fftw_plan_test > out.csv &

// get the fftw "overhead" time for the ESITMAE/MEASURE plans
// only forward direction is considered (after similar performance times were found for different directions)

#define N 1024*1024*2

#include <stdlib.h>
#include <math.h>
#include <fftw3.h>
#include <iostream>
#include <chrono>
#include <random>

auto numruns=10000;

int main()
{
    std::random_device rd;
    std::mt19937 rng(rd());
    std::normal_distribution<float> generate_data(128,1 );
 
    std::cout<<"\n--- will do "<<numruns<<" runs of FFTW  ESTIMATE and MEASURE\n";  
    for(int k=0; k<numruns; k++)
    {

        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*N);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*N);

        auto fft_start = std::chrono::high_resolution_clock::now();
        fftw_plan p1 = fftw_plan_dft_1d(N, input_data, output_data, FFTW_FORWARD, FFTW_ESTIMATE);
        fftw_destroy_plan(p1);
        auto fft_stop = std::chrono::high_resolution_clock::now();

        std::cout<<"CPU time: "<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<" ns, ESTrunNr_"<<k<<" \n";

    }

    for(int k=0; k<numruns; k++)
    {

        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*N);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*N);

        auto fft_start = std::chrono::high_resolution_clock::now();
        fftw_plan p = fftw_plan_dft_1d(N, input_data, output_data, FFTW_FORWARD, FFTW_MEASURE);
        fftw_destroy_plan(p);
        auto fft_stop = std::chrono::high_resolution_clock::now();

        std::cout<<"CPU time: "<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<" ns, MEASrunNr_"<<k<<" \n";

    }


}