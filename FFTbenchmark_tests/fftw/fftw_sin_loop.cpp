// to compile on sharabha:
//  g++ -g -Wall -o fftw_sin_loop fftw_sin_loop.cpp -lfftw3 -lm
// example call:  ./fftw_sin > SinIn0_f0p001A30_2Mio_Meas.txt &

// ND=normal distribution
// uses sine signal+ND-noise in real part of the complex input vector, just ND-noise for imaginary part
// FFTs with N equal to number(s) in Narray
// Do  Plan=Estimate (E) then = Measure (M), Forward (F) and Inverse (I) FFTs, numruns times, each time with new input data
//     1. EF 2. EI 3. MF 4. MI
// writes out execution times of each run [without time to create plan] of numruns

#define N 1024*1024*2

#include <stdlib.h>
#include <math.h>
//#include <complex.h>
//If you have a C compiler, such as gcc, that supports the C99 standard, and you #include
//<complex.h> before <fftw3.h>, then fftw_complex is the native double-precision complex
//type and you can manipulate it with ordinary arithmetic. Otherwise, FFTW defines its
//own complex type,
#include <fftw3.h>
#include <iostream>
#include <chrono>
#include <random>

// ----- how many tests with the same plan?
auto numruns=10000;

//----- define array for number of FFT points
//int Narray[]={1024*1024*2,1024*1024*3,1024*1024*4,1024*1024*5,1024*1024*6,1024*1024*7,1024*1024*8};
// only 1024*1024*2/4/8 are powers of two!
// MEASURE takes ages for, e.g., 1024*1024*3...
int Narray[]={1024*1024*2,1024*1024*4,1024*1024*8};
// test performance for non-multiple of 2 
//int Narray[]={1024*1024*3,1024*1024*5,1024*1024*2+1024*500};

// do half-hour run and 1Mio run
//int Narray[]={1024*1024*8*4,1024*1024*8*2,1024*1024};


int main()
{
    std::random_device rd;
    std::mt19937 rng(rd());
    std::normal_distribution<float> generate_data(128,10 );

    std::normal_distribution<float> generate_amplitude(30,5 );
    std::normal_distribution<float> generate_frequency(1000,10 );

// csv header
    std::cout<<"code,indata,plan,Nsam,direc,runid,time,timeunit\n";

// somehow it matters if doing first ESTIMATE or MEASURE (plan not fully forgotten?)
//   ============================ ESTIMATE AND FORWARD ================================================
 // ----- how many of the Ns should be done?
    for (int ni {0}; ni<3; ++ni){
        int Nlauf=Narray[ni];
        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);

        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_FORWARD, FFTW_ESTIMATE);
//        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_FORWARD, FFTW_MEASURE);


        for(int k=0; k<numruns; k++)
        {
            for(int i=0; i<Nlauf; i++)
            {
                double freq=generate_frequency(rng);
                double amp=generate_amplitude(rng);
                double t = static_cast<double>(i) /N;
                double pulse_i=amp * std::sin(2.0 * M_PI * freq * t); 
                input_data[i][0] = pulse_i + generate_data(rng);
                input_data[i][1] = generate_data(rng);
            }

            auto fft_start = std::chrono::high_resolution_clock::now();
            fftw_execute(p);
            auto fft_stop = std::chrono::high_resolution_clock::now();

            std::cout<<"fftw,SINpND,ESTIMATE,"<<Nlauf<<",FORWARD,"<<k<<","<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";

        }
        fftw_destroy_plan(p);
        fftw_free(input_data); fftw_free(output_data);
    }
//   ============================ ESTIMATE AND BACKWARD ================================================
 // ----- how many of the Ns should be done?
    for (int ni {0}; ni<3; ++ni){
        int Nlauf=Narray[ni];
        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);

        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_BACKWARD, FFTW_ESTIMATE);
//        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_FORWARD, FFTW_MEASURE);

//        std::cout<<"\n--- will do "<<numruns<<" runs of FFTW (same plan) with N="<<Nlauf<<"\n";  

        for(int k=0; k<numruns; k++)
        {
            for(int i=0; i<Nlauf; i++)
            {
                double freq=generate_frequency(rng);
                double amp=generate_amplitude(rng);
                double t = static_cast<double>(i) /N;
                double pulse_i=amp * std::sin(2.0 * M_PI * freq * t); 
                input_data[i][0] = pulse_i + generate_data(rng);
                input_data[i][1] = generate_data(rng);
            }

            auto fft_start = std::chrono::high_resolution_clock::now();
            fftw_execute(p);
            auto fft_stop = std::chrono::high_resolution_clock::now();

            std::cout<<"fftw,SINpND,ESTIMATE,"<<Nlauf<<",BACKWARD,"<<k<<","<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";

        }
        fftw_destroy_plan(p);
        fftw_free(input_data); fftw_free(output_data);
    }
//   ============================ MEASURE AND FORWARD ================================================
 // ----- how many of the Ns should be done?
    for (int ni {0}; ni<3; ++ni){
        int Nlauf=Narray[ni];
        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);

//      fftw_plan p = fftw_plan_dft_1d(N, input_data, output_data, FFTW_FORWARD, FFTW_ESTIMATE);
        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_FORWARD, FFTW_MEASURE);


        for(int k=0; k<numruns; k++)
        {
            for(int i=0; i<Nlauf; i++)
            {
                double freq=generate_frequency(rng);
                double amp=generate_amplitude(rng);
                double t = static_cast<double>(i) /N;
                double pulse_i=amp * std::sin(2.0 * M_PI * freq * t); 
                input_data[i][0] = pulse_i + generate_data(rng);
                input_data[i][1] = generate_data(rng);
            }

            auto fft_start = std::chrono::high_resolution_clock::now();
            fftw_execute(p);
            auto fft_stop = std::chrono::high_resolution_clock::now();

            std::cout<<"fftw,SINpND,MEASURE,"<<Nlauf<<",FORWARD,"<<k<<","<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";

        }
        fftw_destroy_plan(p);
        fftw_free(input_data); fftw_free(output_data);
   }
//   ============================ MEASURE AND BACKWARD ================================================
 // ----- how many of the Ns should be done?
    for (int ni {0}; ni<3; ++ni){
        int Nlauf=Narray[ni];
        fftw_complex *input_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);
        fftw_complex *output_data = (fftw_complex *) malloc(sizeof(fftw_complex)*Nlauf);

//      fftw_plan p = fftw_plan_dft_1d(N, input_data, output_data, FFTW_FORWARD, FFTW_ESTIMATE);
        fftw_plan p = fftw_plan_dft_1d(Nlauf, input_data, output_data, FFTW_BACKWARD, FFTW_MEASURE);


        for(int k=0; k<numruns; k++)
        {
            for(int i=0; i<Nlauf; i++)
            {
                double freq=generate_frequency(rng);
                double amp=generate_amplitude(rng);
                double t = static_cast<double>(i) /N;
                double pulse_i=amp * std::sin(2.0 * M_PI * freq * t); 
                input_data[i][0] = pulse_i + generate_data(rng);
                input_data[i][1] = generate_data(rng);
            }

            auto fft_start = std::chrono::high_resolution_clock::now();
            fftw_execute(p);
            auto fft_stop = std::chrono::high_resolution_clock::now();

            std::cout<<"fftw,SINpND,MEASURE,"<<Nlauf<<",BACKWARD,"<<k<<","<<std::chrono::duration_cast<std::chrono::nanoseconds>(fft_stop - fft_start).count()<<",ns\n";

        }
        fftw_destroy_plan(p);
        fftw_free(input_data); fftw_free(output_data);
    }
}