#include "source/LoadRFClassifier.h"
#include <vector>
#include <chrono>
#include <string>
#include <filesystem>
#include <iostream>
namespace fs = std::filesystem;

void GetFilenames(std::string foldername, std::vector<std::string> &FileNames)
{
	for (const auto &file : fs::recursive_directory_iterator(foldername)){
		if (fs::is_regular_file(file)){
			FileNames.push_back(file.path().filename().string());
		}
	}
}

std::vector<std::string> string_split(std::string line, char delimiter){
        std::vector<std::string> v;
        std::stringstream stream(line);
        std::string element;
        while(std::getline(stream, element, delimiter)){
                v.push_back(element);
        }
        return v;
}


int main(int argc, char* argv[]){

        auto now = std::chrono::system_clock::now();
        auto duration = now.time_since_epoch();
        auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();

        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Started reading file " << milliseconds << std::endl;
// Get the commandline arguments
        if(argc < 6)
        {
                std::cout << "./executable <astrophysical_signal_features> <rfi_features> <sifting_threshold> <input_model_file> <instaces>" << std::endl;
                exit(0);
        }

        std::string filename_signal=std::string(argv[1]);
        std::string filename_RFI=std::string(argv[2]);
        float sifting_th = std::stof(argv[3]);
	std::string modelfile=std::string(argv[4]);
	std::size_t instances = std::stoul(argv[5]);
// Read the training dataset for astorphysical cases
        std::cout << "Reading the astrophysical dataset ..." << std::endl;
        std::vector<std::vector<float>> pulses_dataset;
        std::string line;
        int k=0;
        std::ifstream input_pulse_stream;
        input_pulse_stream.open(filename_signal);
        while(getline(input_pulse_stream,line) && k < instances){
                if(k != 0){
                        std::vector<std::string> v = string_split(line, ',');
                        std::vector<float> features;
                        if(v.size() == 10){
                                for(size_t jj=0; jj<v.size(); ++jj){
                                        features.push_back(std::stof(v[jj]));
                                }
                        }
                        if(features.size() == 10){
                                if(features[0] > sifting_th){
                                pulses_dataset.push_back(features);
                                }
                        }
                }
                k=k+1;
        }

        std::cout << "Reading the RFI dataset ..." << std::endl;
        std::vector<std::vector<float>> rfi_dataset;
        k=0;
        std::ifstream input_rfi_stream;
        input_rfi_stream.open(filename_RFI);
        while(getline(input_rfi_stream,line) && k < instances){
                if(k != 0){
                        std::vector<std::string> v = string_split(line, ',');
                        std::vector<float> features;
                        if(v.size() == 10){
                                for(size_t jj=0; jj<v.size(); ++jj){
                                        features.push_back(std::stof(v[jj]));
                                }
                        }
                        if(features.size() == 10){
                                if(features[0] > sifting_th){
                                rfi_dataset.push_back(features);
                                }
                        }
                }
                k=k+1;
        }

	
        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Done reading file " << milliseconds << std::endl;

	std::cout << "Making the Random forest classifier object and loading the model" << std::endl;
	LoadRFClassifier MyForest(modelfile);
	MyForest.prepare_forest();
	now = std::chrono::system_clock::now();
	duration = now.time_since_epoch();
	milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
	std::cout << "Done making classifier " << milliseconds << std::endl;
	
	size_t truepositive_count = 0;
	for(size_t ii=0; ii<pulses_dataset.size(); ++ii){
		if(MyForest.predict_label(pulses_dataset[ii]) == 1){
			truepositive_count += 1;
		}
	}
        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Predicted number of instances instances " << pulses_dataset.size() << " in time: " << milliseconds << std::endl;
	std::cout << "Correct classification instances on astrophysical signal: " << truepositive_count << std::endl;

        size_t truenegative_count = 0;
        for(size_t ii=0; ii<rfi_dataset.size(); ++ii){
                if(MyForest.predict_label(rfi_dataset[ii]) == 0){
                        truenegative_count += 1;
                }
        }
        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Predicted number of instances " << rfi_dataset.size() << " in time: " << milliseconds << std::endl;
        std::cout << "Correct classification instances on RFI signal: " << truenegative_count << std::endl;
}
