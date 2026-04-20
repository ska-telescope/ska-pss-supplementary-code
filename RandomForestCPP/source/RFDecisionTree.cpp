#include "RFDecisionTree.h"

RFDecisionTree::RFDecisionTree(std::vector<std::pair<std::vector<float>, int>> data, size_t max_depth, size_t min_split, size_t nfeatures_split, int random_seed, float relative_weight):gen(random_seed == 0 ? std::random_device{}() : random_seed), distrib(0, data[0].first.size() - 1){
	_dataset = data;
	_max_depth = max_depth;
	_min_split = min_split;
	_dataset_size = data.size();
	outfile.open("TrainedDecisionTree.txt");
	_nfeatures = _dataset[0].first.size();
	_nfeatures_split = nfeatures_split;
	_relative_weight = relative_weight;
}



void RFDecisionTree::predict_class(std::vector<float>& feature_vector, const std::unique_ptr<node>& Tree){
	if(Tree->leaf == true){
		predicted_label = Tree->label;
	}
	else{
		float _threshold = Tree->threshold;
		size_t _feature_index=Tree->feature_idx;
		if(feature_vector[_feature_index] <= _threshold){
			predict_class(feature_vector, Tree->left);
		}
		else{
			predict_class(feature_vector, Tree->right);
		}
	}
}



float RFDecisionTree::_gini_impurity(std::vector<int>& labels){
	std::unordered_map<int, size_t> frequencymap;
	for(int member : labels){
		frequencymap[member]++;
	}
	float full_size = static_cast<float>(labels.size());
	float Gini = 1.0;
	for(std::pair<int, size_t> map : frequencymap){
		float factor = 1.0;
		if(map.first == 1){
			factor = _relative_weight;
		}
		else{
			factor = 1.0/_relative_weight;
		}
		float fraction = static_cast<float>(map.second)/full_size;
		Gini -= factor*fraction*fraction;
	}
	return Gini;
}




void RFDecisionTree::_get_train_test_data(std::vector<std::pair<std::vector<float>, int>>& data_with_labels, float train_test_ratio){
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


void RFDecisionTree::_split_dataset(std::vector<std::pair<std::vector<float>, int>>& data, size_t feature_idx, float feature_threshold){
	_split_dataset_left.clear(); _split_dataset_right.clear();
	for(size_t i=0; i<data.size(); ++i){
		if(data[i].first[feature_idx] < feature_threshold){
			_split_dataset_left.push_back(data[i]);
		}
		else{
			_split_dataset_right.push_back(data[i]);
		}
	}
}


void RFDecisionTree::_find_best_feature(std::vector<std::pair<std::vector<float>, int>>& data){
	std::vector<std::vector<float>> feature_vector;
	std::vector<int> label_vector;
	std::vector<size_t> feature_indices;
	_best_feature_gini = std::numeric_limits<float>::infinity();
	for(size_t i=0; i<data.size(); ++i){
		feature_vector.push_back(data[i].first);
		label_vector.push_back(data[i].second);
	}
//   Get the random set of feature indices for the split
	while(feature_indices.size() < _nfeatures_split){
		int new_index = distrib(gen);
		auto itr = std::find(feature_indices.begin(), feature_indices.end(), new_index);
		if(itr == feature_indices.end()){
			feature_indices.push_back(new_index);
			std::cout << new_index << " ";
		}
	}
	std::cout << std::endl;

//  Loop over the set of selected features

	for(size_t jj = 0; jj < _nfeatures_split; ++jj){
		size_t ftr_idx = feature_indices[jj];
		std::vector<float> sorted_feature;
// Get the vector of feature values for current feature idx
		for(size_t data_idx = 0; data_idx < feature_vector.size(); ++data_idx){
			sorted_feature.push_back(feature_vector[data_idx][ftr_idx]);
		}

		std::sort(sorted_feature.begin(), sorted_feature.end());
		sorted_feature.erase(std::unique(sorted_feature.begin(), sorted_feature.end()), sorted_feature.end());

// Loop over all the data points to get best gini for this feature idx
		for(size_t break_idx = 0; break_idx < sorted_feature.size()-1; ++break_idx){
			float feature_threshold = (sorted_feature[break_idx] + sorted_feature[break_idx+1])/2.0;
			_split_dataset(data, ftr_idx, feature_threshold);
			std::vector<int> child_left_labels, child_right_labels;
			for(size_t child_idx=0; child_idx < _split_dataset_left.size(); ++child_idx){
				child_left_labels.push_back(_split_dataset_left[child_idx].second);
			}
			for(size_t child_idx=0; child_idx < _split_dataset_right.size(); ++child_idx){
				child_right_labels.push_back(_split_dataset_right[child_idx].second);
			}
			float left_gini = _gini_impurity(child_left_labels);
			float right_gini = _gini_impurity(child_right_labels);
			float probability_left = static_cast<float>(child_left_labels.size())/static_cast<float>(data.size());
			float probability_right = static_cast<float>(child_right_labels.size())/static_cast<float>(data.size());
			float weighted_gini = probability_left*left_gini + probability_right*right_gini;
			if(weighted_gini < _best_feature_gini){
				_best_feature_gini = weighted_gini;
				_current_best_gini = _best_feature_gini;
				_best_feature_threshold = feature_threshold;
				_best_feature_idx = ftr_idx;
			}
		}	
	}
}



std::unique_ptr<RFDecisionTree::node> RFDecisionTree::build_tree(std::vector<std::pair<std::vector<float>, int>>& data, int depth){
	std::unique_ptr<node> tree(new node);
	std::vector<int> labels;
	for(size_t i=0; i<data.size(); ++i){
		labels.push_back(data[i].second);

	}
	std::cout << "Labels size is: " << labels.size() << std::endl;
	float _parent_gini = _gini_impurity(labels);
	std::cout << "Parent Gini is: " << _parent_gini << std::endl;
	if(_parent_gini < 0.001){
		std::cout << "Got leaf due to very small Gini at depth: " << depth << std::endl;
		tree->leaf = true;
		tree->label = labels[0];
		tree->left = nullptr;
		tree->right = nullptr;
		tree->feature_idx = -1;
		tree->level = depth;
		tree->threshold = -1;
	}
	else if(depth >= _max_depth){
		std::cout << "Got leaf due to exceeding max_depth at depth: " << depth << std::endl;
		std::vector<int> sorted_labels=labels;
		std::sort(sorted_labels.begin(), sorted_labels.end());
		int approx_label = sorted_labels[static_cast<int>(static_cast<float>(sorted_labels.size())/2.0)];
		tree->leaf = true;
		tree->label = approx_label;
		tree->left = nullptr;
		tree->right = nullptr;
		tree->feature_idx = -1;
		tree->level = depth;
		tree->threshold = -1;
	}
        else if(labels.size() <= _min_split){
		std::cout << "Got leaf due to small size of points at depth: " << depth << std::endl;
                std::vector<int> sorted_labels=labels;
                std::sort(sorted_labels.begin(), sorted_labels.end());
                int approx_label = sorted_labels[static_cast<int>(static_cast<float>(sorted_labels.size())/2.0)];
                tree->leaf = true;
                tree->label = approx_label;
                tree->left = nullptr;
                tree->right = nullptr;
                tree->feature_idx = -1;
                tree->level = depth;
                tree->threshold = -1;
        }

	else{
		std::cout << "Splitting further at depth: " << depth << std::endl;
		_find_best_feature(data);
		tree->feature_idx = _best_feature_idx;
		tree->level = depth;
		tree->label = -1;
		tree->threshold = _best_feature_threshold;
		tree->leaf = false;
		_split_dataset(data, _best_feature_idx, _best_feature_threshold);
		std::vector<std::pair<std::vector<float>, int>> left_dataset = _split_dataset_left;
		std::vector<std::pair<std::vector<float>, int>> right_dataset = _split_dataset_right;
		if(left_dataset.size() != 0 && right_dataset.size() != 0){
			tree->left = std::unique_ptr<node>(build_tree(left_dataset, depth+1));
			tree->right = std::unique_ptr<node>(build_tree(right_dataset, depth+1));
		}
		else{
			tree->left = nullptr;
			tree->right = nullptr;
			tree->leaf = true;
		}
	}
	return tree;
}

void RFDecisionTree:: write_model(const std::unique_ptr<node>& tree, size_t index){
	if(tree->leaf == false){ 
		size_t left_child_idx = index*2+0;
		size_t right_child_idx = index*2+1;
		outfile << index << ',' << tree->feature_idx << ',' << tree->level << ',' << tree->label << ',' << tree->threshold << ',' << "false" << "," << left_child_idx  << "," << right_child_idx << std::endl;
		write_model(tree->left, left_child_idx);
		write_model(tree->right, right_child_idx);
	}
	else{
		outfile << index << ',' << tree->feature_idx << ',' << tree->level << ',' << tree->label << ',' << tree->threshold << ',' << "true" << "," << -1 << ',' << -1 << std::endl;
	}

}

void RFDecisionTree::test_tree(){
	size_t real_class0, real_class1, predicted_class0, predicted_class1;
	size_t true_predicted_class0=0, false_predicted_class1=0, true_predicted_class1=0, false_predicted_class0=0;
	for(size_t i=0; i<_testing_dataset.size(); ++i){
		if(_testing_dataset[i].second == 0){
			real_class0 += 1;
			predict_class(_testing_dataset[i].first, Tree);
			if(predicted_label == 0){
				true_predicted_class0 += 1;
			}
			else{
				false_predicted_class1 += 1;
			}
		}
		else{
			real_class1 += 1;
			predict_class(_testing_dataset[i].first, Tree);
			if(predicted_label == 1){
				true_predicted_class1 += 1;
			}
			else{
				false_predicted_class0 += 1;
			}
		}
	}
	float precision = static_cast<float>(true_predicted_class1 + true_predicted_class0)/static_cast<float>(true_predicted_class0 + false_predicted_class1 + true_predicted_class1 + false_predicted_class0);
	float false_negative = static_cast<float>(false_predicted_class0)/static_cast<float>(false_predicted_class1 + true_predicted_class1);
	std::cout << "Precision: " << precision << "false negative" << false_negative << std::endl;
}

void RFDecisionTree::train_and_test_model(){
	std::cout << "getting train and test dataset" << std::endl;
	_get_train_test_data(_dataset, 0.7);
	std::vector<float> feature_sample = _training_dataset[0].first;
	std::cout << "Feature size for training" << feature_sample.size() << std::endl;
	std::cout << "building tree" << std::endl;
	Tree = build_tree(_training_dataset, 1);
	std::cout << "writing tree" << std::endl;
	write_model(Tree, 1);
	outfile.close();
	std::cout << "testing tree" << std::endl;
	test_tree();
}

void RFDecisionTree::train_model(){
        Tree = build_tree(_dataset, 1);
}
