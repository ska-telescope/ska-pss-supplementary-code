#ifndef MAKE_RF_CLASSIFIER_H
#define MAKE_RF_CLASSIFIER_H

#include "RFDecisionTree.h"
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

class MakeRFClassifier{
	public:
		MakeRFClassifier(std::vector<std::pair<std::vector<float>, int>> data, size_t max_depth, size_t min_split, size_t nfeatures_split, size_t Nestimators = 200, float subset_frac = 1.0, int random_seed=0, float relative_weight = 1.3);
		void _train_and_test_model();
		void _train_model();
	private:
		std::ofstream outfile;
		std::random_device rd;
		std::mt19937 gen;
		std::vector<std::pair<std::vector<float>, int>> _dataset;
		size_t _max_depth, _min_split, _nfeatures_split, _nestimators, _full_size, _subset_size;
		float _subset_frac, _relative_weight;
		int _predicted_DT, _predicted_RF;
		std::unique_ptr<RFDecisionTree::node> Tree;
		std::vector<std::unique_ptr<RFDecisionTree::node>> _forest;
		std::vector<std::pair<std::vector<float>, int>> _bootstrap(std::vector<std::pair<std::vector<float>, int>> dataset);
		std::vector<std::unique_ptr<RFDecisionTree::node>> _build_forest(std::vector<std::pair<std::vector<float>, int>> data);
		void  _write_DT(const std::unique_ptr<RFDecisionTree::node>& tree, size_t index);
		void _write_RF(std::vector<std::unique_ptr<RFDecisionTree::node>>& _forest);
		int _predict_RFclass(std::vector<float>& feature_vector, const std::vector<std::unique_ptr<RFDecisionTree::node>>& RF);
		void _predict_DTclass(std::vector<float>& feature_vector, const std::unique_ptr<RFDecisionTree::node>& DT);
		void _get_train_test_data(std::vector<std::pair<std::vector<float>, int>>& data, float train_test_ratio);
		std::vector<std::pair<std::vector<float>, int>> _training_dataset, _testing_dataset;
};

#endif
