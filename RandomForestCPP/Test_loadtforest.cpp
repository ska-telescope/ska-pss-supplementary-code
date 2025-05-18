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

	std::vector<std::vector<float>> astro_dataset;
	std::vector<std::vector<float>> rfi_dataset;
	std::string foldername_signal=std::string(argv[1]);
	std::string foldername_RFI=std::string(argv[2]);

	std::vector<std::string> filenames;
	GetFilenames(foldername_signal, filenames);
	for(size_t ii=0; ii<10000; ++ii){
		std::ifstream cluster_file;
		cluster_file.open(foldername_signal+'/'+filenames[ii]);
		std::string line;
		std::vector<float> features;
		int label = 1;
		int k=0;
		while(getline(cluster_file,line)){
			if(k==1){
				std::vector<std::string> v = string_split(line, ',');
				if(v.size() == 10){
					for(size_t jj=0; jj<v.size(); ++jj){
						features.push_back(std::stof(v[jj]));
					}
				}
			}
			k += 1;
		}
		if(features.size() == 10){
			if(features[0] >= 8.0){
				astro_dataset.push_back(features);
			}
		}

	}
        filenames.clear();
        GetFilenames(foldername_RFI, filenames);
        for(size_t ii=0; ii<10000; ++ii){
                std::ifstream cluster_file;
                cluster_file.open(foldername_RFI+'/'+filenames[ii]);
                std::string line;
                std::vector<float> features;
                int label = 0;
                int k=0;
                while(getline(cluster_file,line)){
                        if(k==1){
                                std::vector<std::string> v = string_split(line, ',');
				if(v.size() == 10){
                                	for(size_t jj=0; jj<v.size(); ++jj){
                                        	features.push_back(std::stof(v[jj]));
                                	}
				}
                        }
                        k += 1;
                }
		if(features.size() == 10){
			if(features[0] >= 8.0){
                		rfi_dataset.push_back(features);
			}
		}

        }

        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Done reading file " << milliseconds << std::endl;

	std::cout << "Making the Random forest classifier object and loading the model" << std::endl;
	LoadRFClassifier MyForest("TrainedRandomForest_200trees_20000instances.txt");
	MyForest.prepare_forest();
	now = std::chrono::system_clock::now();
	duration = now.time_since_epoch();
	milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
	std::cout << "Done making classifier " << milliseconds << std::endl;
	
	size_t truepositive_count = 0;
	for(size_t ii=0; ii<astro_dataset.size(); ++ii){
		if(MyForest.predict_label(astro_dataset[ii]) == 1){
			truepositive_count += 1;
		}
	}
        now = std::chrono::system_clock::now();
        duration = now.time_since_epoch();
        milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
        std::cout << "Predicted number of instances instances " << astro_dataset.size() << " in time: " << milliseconds << std::endl;
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
