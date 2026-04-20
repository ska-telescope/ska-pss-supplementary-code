#include "source/RFDecisionTree.h"
#include "source/MakeRFClassifier.h"
#include <vector>
#include <string>
#include <filesystem>
#include <iostream>
#include <algorithm>
#include <random>
namespace fs = std::filesystem;

void GetFilenames(std::string foldername, std::vector<std::string> &FileNames)
{
	for (const auto &file : fs::recursive_directory_iterator(foldername)){
		if (fs::is_regular_file(file)){
			FileNames.push_back(file.path().filename().string());
		}
	}
}

std::vector<std::string> string_split(std::string line){
        std::vector<std::string> v;
        std::string s="";
        line=line+'\n';
        size_t i,j;
        j=1;
        for(i=0;i<line.size();++i){
                if(line[i] == ',' || line[i] == '\n'){
                        if(j == 1){
                                v.push_back(s);
                                s="";
                                j=0;
                        }
                        else{
                                j=0;
                        }
                }
                else{
                        j=1;
                }
                if(j == 1){
                        s=s+line[i];
                }
        }
        return v;
}


int main(int argc, char* argv[]){
// A vector to store the training dataset
	std::vector<std::pair<std::vector<float>, int>> full_dataset;
// Get the commandline arguments
	if(argc < 9)
	{ 
		std::cout << "./executable <astrophysical_signal_features> <rfi_features> <sifting_threshold> <max_depth> <min_split> <nfeatures_at_split> <number_fo_trees> <number_of_samples_to_train>" << std::endl;
		exit(0);
	}

	std::string filename_signal=std::string(argv[1]);
	std::string filename_RFI=std::string(argv[2]);
	float sifting_th = std::stof(argv[3]);
	std::size_t maxdepth = std::stoul(argv[4]);
	std::size_t minsplit = std::stoul(argv[5]);
	std::size_t nfeaturessplit = std::stoul(argv[6]);
	std::size_t nestimators = std::stoul(argv[7]);
	std::size_t instances=std::stoul(argv[8]);
// Read the training dataset for astorphysical cases
	std::cout << "Reading the astrophysical dataset ..." << std::endl;
	std::vector<std::pair<std::vector<float>, int>> pulses_dataset;
	std::string line;
	int label = 1;	
	int k=0;
	std::ifstream input_pulse_stream;
	input_pulse_stream.open(filename_signal);
	while(getline(input_pulse_stream,line)){
		if(k != 0){
			std::vector<std::string> v = string_split(line);
			std::vector<float> features;
			if(v.size() == 10){
				for(size_t jj=0; jj<v.size(); ++jj){
					features.push_back(std::stof(v[jj]));
				}
			}
			if(features.size() == 10){
				if(features[0] > sifting_th){
				std::pair<std::vector<float>, int> datapoint;
				datapoint.first = features;
				datapoint.second = label;
				pulses_dataset.push_back(datapoint);
				}
			}
		}
		k=k+1;
	}
// Shuffle the pulses dataset
	std::cout << "Shuffiling the dataset and extracting required number of data points ..." << std::endl;
	
	std::random_device rd;
	std::default_random_engine engine(rd());
	std::shuffle(pulses_dataset.begin(), pulses_dataset.end(), engine);
	std::cout << "Storing " << instances << " pulse instances out of " << pulses_dataset.size() << std::endl;
	for(std::size_t ii=0; ii<instances; ++ii)
	{
		full_dataset.push_back(pulses_dataset[ii]);
	}

// Read the training dataset for RFI cases
        std::cout << "Reading the astrophysical dataset ..." << std::endl;
        std::vector<std::pair<std::vector<float>, int>> rfi_dataset;
        label = 0;
        k=0;
	std::ifstream input_rfi_stream;
	input_rfi_stream.open(filename_RFI);
        while(getline(input_rfi_stream, line)){
                if(k != 0){
                        std::vector<std::string> v = string_split(line);
                        std::vector<float> features;
                        if(v.size() == 10){
                                for(size_t jj=0; jj<v.size(); ++jj){
                                        features.push_back(std::stof(v[jj]));
                                }
                        }
                        if(features.size() == 10){
                                if(features[0] > sifting_th){
                                std::pair<std::vector<float>, int> datapoint;
                                datapoint.first = features;
                                datapoint.second = label;
                                rfi_dataset.push_back(datapoint);
                                }
                        }
                }
                k=k+1;
        }
// Shuffle the RFI dataset
        std::cout << "Shuffiling the dataset and extracting required number of data points ..." << std::endl;

        std::shuffle(rfi_dataset.begin(), rfi_dataset.end(), engine);
        std::cout << "Storing " << instances << " RFI instances out of " << rfi_dataset.size() << std::endl;
        for(std::size_t ii=0; ii<instances; ++ii)
        {
                full_dataset.push_back(rfi_dataset[ii]);
        }



	std::cout << "Started training and testing." << std::endl;
	MakeRFClassifier MyForest(full_dataset, maxdepth, minsplit, nfeaturessplit, nestimators, 1.0, 0, 1.0); // MakeRFClassifier(data, max_depth, min_split, nfeatures_split, Nestimators, subset_frac, random_seed, relative_weight)
	MyForest._train_and_test_model();

}
