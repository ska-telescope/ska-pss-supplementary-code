#include "source/RFDecisionTree.h"
#include "source/MakeRFClassifier.h"
#include <vector>
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
	std::vector<std::pair<std::vector<float>, int>> full_dataset;
	std::string foldername_signal=std::string(argv[1]);
	std::string foldername_RFI=std::string(argv[2]);

	std::vector<std::string> filenames;
	GetFilenames(foldername_signal, filenames);
	std::cout << "Getting signal features" << std::endl;
	for(size_t ii=0; ii<1000; ++ii){
		std::ifstream cluster_file;
		cluster_file.open(foldername_signal+'/'+filenames[ii]);
		std::string line;
		std::vector<float> features;
		int label = 1;
		int k=0;
		while(getline(cluster_file,line)){
			if(k==1){
				std::vector<std::string> v = string_split(line);
				if(v.size() == 10){
					for(size_t jj=0; jj<v.size(); ++jj){
						features.push_back(std::stof(v[jj]));
					}
				}
			}
			k += 1;
		}
		if(features.size() == 10){
			if(features[0] > 8.0){
			std::pair<std::vector<float>, int> datapoint;
			datapoint.first = features;
			datapoint.second = label;
			full_dataset.push_back(datapoint);
			}
		}

	}
	std::cout << "Getting RFI features" << std::endl;
        filenames.clear();
        GetFilenames(foldername_RFI, filenames);
        for(size_t ii=0; ii<1000; ++ii){
                std::ifstream cluster_file;
                cluster_file.open(foldername_RFI+'/'+filenames[ii]);
                std::string line;
                std::vector<float> features;
                int label = 0;
                int k=0;
                while(getline(cluster_file,line)){
                        if(k==1){
                                std::vector<std::string> v = string_split(line);
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
                	std::pair<std::vector<float>, int> datapoint;
                	datapoint.first = features;
                	datapoint.second = label;
                	full_dataset.push_back(datapoint);
			}
		}

        }

	std::cout << full_dataset.size() << std::endl;
	MakeRFClassifier MyForest(full_dataset, 20, 2, 3, 10, 1.0, 0, 1.0);
	MyForest._train_and_test_model();

}
