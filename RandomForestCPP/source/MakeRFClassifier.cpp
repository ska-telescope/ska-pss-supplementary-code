#include "MakeRFClassifier.h"

MakeRFClassifier::MakeRFClassifier(std::vector<std::pair<std::vector<float>, int>> data, size_t max_depth, size_t min_split, size_t nfeatures_split, size_t Nestimators, float subset_frac, int random_seed, float relative_weight):gen(random_seed == 0 ? std::random_device{}() : random_seed){
	_dataset = data;
	_max_depth = max_depth;
	_min_split = min_split;
	_nfeatures_split = nfeatures_split;
	_nestimators = Nestimators;
	_full_size = _dataset.size();
	_subset_frac = subset_frac;
	_relative_weight = relative_weight;
	outfile.open("TrainedRandomForest.txt");
}

std::vector<std::pair<std::vector<float>, int>>  MakeRFClassifier::_bootstrap(std::vector<std::pair<std::vector<float>, int>> dataset){
	std::vector<std::pair<std::vector<float>, int>> subdataset;
	_subset_size = static_cast<int>(_subset_frac*dataset.size());
	std::uniform_int_distribution<int> distrib(0, dataset.size() - 1);
	for(size_t ii=0; ii<_subset_size; ++ii){
		size_t new_index = distrib(gen);
		subdataset.push_back(dataset[new_index]);
	}
	return subdataset;
}

std::vector<std::unique_ptr<RFDecisionTree::node>> MakeRFClassifier::_build_forest(std::vector<std::pair<std::vector<float>, int>> data){
	std::vector<std::unique_ptr<RFDecisionTree::node>> forest;
	std::vector<std::pair<std::vector<float>, int>> new_dataset;
	for(size_t ii=0; ii<_nestimators; ++ii){
		new_dataset = _bootstrap(data);
		RFDecisionTree Treeobject(new_dataset, _max_depth, _min_split, _nfeatures_split, 0, _relative_weight);
		Treeobject.train_model();
		forest.push_back(std::move(Treeobject.Tree));
	}
	return forest;
}

void MakeRFClassifier::_predict_DTclass(std::vector<float>& feature_vector, const std::unique_ptr<RFDecisionTree::node>& tree){
        if(tree->leaf == true){
                _predicted_DT = tree->label;
        }
        else{
                float _threshold = tree->threshold;
                size_t _feature_index=tree->feature_idx;
                if(feature_vector[_feature_index] <= _threshold){
                        _predict_DTclass(feature_vector, tree->left);
                }
                else{
                        _predict_DTclass(feature_vector, tree->right);
                }
        }
}

int MakeRFClassifier::_predict_RFclass(std::vector<float>& feature, const std::vector<std::unique_ptr<RFDecisionTree::node>>& forest){
	std::vector<int> predicted_labels;
	size_t numtrees = forest.size();
	for(size_t ii=0; ii<numtrees; ++ii){
		_predict_DTclass(feature, forest[ii]);
		predicted_labels.push_back(_predicted_DT);
	}
	int sum = std::accumulate(predicted_labels.begin(), predicted_labels.end(), 0);
	float fraction = static_cast<float>(sum)/static_cast<float>(numtrees);
	if(fraction <= 0.5){
		return 0;
	}
	else{
		return 1;
	}
}

void MakeRFClassifier::_write_DT(const std::unique_ptr<RFDecisionTree::node>& tree, size_t index){
        if(tree->leaf == false){
                size_t left_child_idx = index*2+0;
                size_t right_child_idx = index*2+1;
                outfile << index << ',' << tree->feature_idx << ',' << tree->level << ',' << tree->label << ',' << tree->threshold << ',' << "false" << "," << left_child_idx  << "," << right_child_idx << std::endl;
                _write_DT(tree->left, left_child_idx);
                _write_DT(tree->right, right_child_idx);
        }
        else{
                outfile << index << ',' << tree->feature_idx << ',' << tree->level << ',' << tree->label << ',' << tree->threshold << ',' << "true" << "," << -1 << ',' << -1 << std::endl;
        }

}

void MakeRFClassifier::_write_RF(std::vector<std::unique_ptr<RFDecisionTree::node>>& forest){
	for(size_t ii=0; ii<forest.size(); ++ii){
		outfile << "Starting next Tree" << std::endl;
		_write_DT(forest[ii], 1);
	}
	outfile << "End of Random Forest" << std::endl;
	outfile.close();
}

void MakeRFClassifier::_get_train_test_data(std::vector<std::pair<std::vector<float>, int>>& data_with_labels, float train_test_ratio){
        std::shuffle(data_with_labels.begin(), data_with_labels.end(), std::default_random_engine(123123));
        size_t cut_idx = size_t(data_with_labels.size()*train_test_ratio);
        for(size_t i=0; i<data_with_labels.size(); ++i){
                if(i<cut_idx){
                        _training_dataset.push_back(data_with_labels[i]);

                }
                else{
                        _testing_dataset.push_back(data_with_labels[i]);
                }
        }
}

void MakeRFClassifier::_train_and_test_model(){
	_get_train_test_data(_dataset, 0.7);
	std::cout << "Training dataset size: " << _training_dataset.size() << std::endl;
	_forest = _build_forest(_training_dataset);
	std::cout << "Testing dataset size: " << _testing_dataset.size() << std::endl;
	size_t true_classifications = 0;
	size_t false_negative_numbers = 0, total_positive_candidates = 0;
	for(auto datapoint : _testing_dataset){
		std::vector<float> feature = datapoint.first;
		int true_label = datapoint.second;
		int predicted_label = _predict_RFclass(feature, _forest);
		if(predicted_label == true_label){
			true_classifications += 1;
		}
		if(true_label == 1){
			total_positive_candidates += 1;
			if(predicted_label == 0){
				false_negative_numbers += 1;
			}
		}
		std::cout << "True class: " << true_label << " Predicted label: " << predicted_label << std::endl;
	}
	float false_negative = static_cast<float>(false_negative_numbers)/static_cast<float>(total_positive_candidates);
	float precision = static_cast<float>(true_classifications)/static_cast<float>(_testing_dataset.size());
	std::cout << "Precision of the model is: " << precision << std::endl;
	std::cout << "False negative fraction is: " << false_negative << std::endl;
	_write_RF(_forest);
}

void MakeRFClassifier::_train_model(){
	_forest = _build_forest(_dataset);
	_write_RF(_forest);
}



