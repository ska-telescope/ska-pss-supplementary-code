#ifndef LOAD_RF_CLASSIFIER_H
#define LOAD_RF_CLASSIFIER_H

#include <iostream>
#include <fstream>
#include <vector>
#include <math.h>
#include <cfloat>
#include <bits/stdc++.h>
#include <algorithm>
#include <unordered_map>
#include <chrono>
#include <memory>
#include <random>
#include <ctime>

class LoadRFClassifier{
	public:
                struct node{
                        int feature_idx;
                        size_t level;
                        int label = -1;    // Valid labels can be either 0 or 1, label '-1' means that label is not decided at this level, lebel will only be valid if leaf == true
                        float threshold;
                        bool leaf = false;
                        std::unique_ptr<node> left;
                        std::unique_ptr<node> right;
                };

		LoadRFClassifier(std::string ModelFileName);
		void prepare_forest();
		int predict_label(std::vector<float>& featureset);

	private:

		std::ifstream _modelstream;
		std::string _modelfilename;
		std::vector<std::string> _string_split(std::string& line, char delimiter);
		int _predicted_DT, _predicted_RF;
		std::unique_ptr<node> _tree;
		std::unordered_map<size_t, std::vector<std::string>> _tree_map;
		std::vector<std::unique_ptr<node>> _forest;
		std::vector<std::unordered_map<size_t, std::vector<std::string>>> _forest_map;
		void _read_RFmodel();
		void _load_forest();
		std::unique_ptr<node> _load_tree(size_t node_idx, std::unordered_map<size_t, std::vector<std::string>>& tree_map);
		int _predict_RFclass(std::vector<float>& feature_vector);
		void _predict_DTclass(std::vector<float>& feature_vector, const std::unique_ptr<node>& DT);

};

#endif
