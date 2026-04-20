#include "LoadRFClassifier.h"

LoadRFClassifier::LoadRFClassifier(std::string ModelFileName){
	_modelfilename = ModelFileName;
	_modelstream.open(_modelfilename);
}

void LoadRFClassifier::prepare_forest(){
	std::cout << " Calling read_RFmodel for file: " << _modelfilename << std::endl;
	_read_RFmodel();
	_load_forest();
}

int LoadRFClassifier::predict_label(std::vector<float>& featureset){
	return _predict_RFclass(featureset);
}

std::vector<std::string> LoadRFClassifier::_string_split(std::string& line, char delimiter){
        std::vector<std::string> v;
        std::stringstream stream(line);
        std::string element;
        while(std::getline(stream, element, delimiter)){
                v.push_back(element);
        }
        return v;
}

void LoadRFClassifier::_read_RFmodel(){
	size_t ii=0;
        std::string line;
        std::vector<std::string> features_vector;
	std::unordered_map<size_t, std::vector<std::string>> tree_map;
        size_t node_idx;
        while(getline(_modelstream,line)){
		if(line == "Starting next Tree"){
			if(ii != 0){
				_forest_map.push_back(tree_map);
				std::cout << "Loaded the tree number " << ii << " , total number of nodes: " << tree_map.size() << std::endl;
				tree_map.clear();
			}
			ii = ii + 1;
		}
		else if(line == "End of Random Forest"){
			_forest_map.push_back(tree_map);
			std::cout << "End of model, total trees: " << ii << std::endl;
		}

		else{
                	std::vector<std::string> v = _string_split(line, ',');
                	node_idx = stoi(v[0]);
                	v.erase(v.begin());
                	features_vector = v;
                	tree_map.insert(std::make_pair(node_idx, features_vector));
		}
	}

}

std::unique_ptr<LoadRFClassifier::node> LoadRFClassifier::_load_tree(size_t node_idx, std::unordered_map<size_t, std::vector<std::string>>& tree_map){
        std::vector<std::string> tree_params;
        auto node_map = tree_map.find(node_idx);
        if(node_map == tree_map.end()){
                std::cout << "Node " << node_idx << " is not present in the map" << std::endl;
                exit(1);
        }
        else{
                tree_params = node_map->second;
        }

        if(tree_params.size() != 7){
                std::cout << "The parameters set is not complete" << std::endl;
                exit(1);
        }
        std::unique_ptr<node> tree(new node);
        if(tree_params[4] == "false"){
                size_t left_idx = node_idx*2+0;
                size_t right_idx = node_idx*2+1;
                tree->feature_idx = stoi(tree_params[0]);
                tree->level = stoi(tree_params[1]);
                tree->label = -1;
                tree->threshold = stof(tree_params[3]);
                tree->leaf = false;
                tree->left = std::unique_ptr<node>(_load_tree(left_idx, tree_map));
                tree->right = std::unique_ptr<node>(_load_tree(right_idx, tree_map));
        }
        else{
                tree->feature_idx = -1;
                tree->level = stoi(tree_params[1]);
                tree->label = stoi(tree_params[2]);
                tree->threshold = -1;
                tree->leaf = true;
                tree->left = nullptr;
                tree->right = nullptr;
        }
        return tree;
}


void LoadRFClassifier::_load_forest(){
	for(size_t ii=0; ii<_forest_map.size(); ++ii){
		_forest.push_back(std::move(_load_tree(1, _forest_map[ii])));
	}
}


void LoadRFClassifier::_predict_DTclass(std::vector<float>& feature_vector, const std::unique_ptr<LoadRFClassifier::node>& tree){
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


int LoadRFClassifier::_predict_RFclass(std::vector<float>& feature){
	std::vector<int> predicted_labels;
	size_t numtrees = _forest.size();
	for(size_t ii=0; ii<numtrees; ++ii){
		_predict_DTclass(feature, _forest[ii]);
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


