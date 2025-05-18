#ifndef RFDECISION_TREE_H
#define RFDECISION_TREE_H

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

class RFDecisionTree{
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

		RFDecisionTree(std::vector<std::pair<std::vector<float>, int>> data, size_t max_depth, size_t min_split, size_t nfeatures_split, int random_seed=0, float relative_weight=1.0);        // Declaring the constructor
		std::unique_ptr<node> Tree;                                                               // Root node of the Trre
		void write_model(const std::unique_ptr<node>& tree, size_t idx);                                     // Function to write out the trianed model parameters
		void predict_class(std::vector<float>& feature_vector, const std::unique_ptr<node>& Tree);           // Function to predict the class of a single feature sample
		std::unique_ptr<node> build_tree(std::vector<std::pair<std::vector<float>, int>>& data, int depth);     // Function to build the tree (training)
		void test_tree();                                                   // Function to test the tree
		std::vector<float> feature_weights();                               // Function to return the weightage of different features
		void train_and_test_model();
		void train_model();

	private:
		size_t _nfeatures_split = 5, _nfeatures;
		std::random_device rd;
		std::mt19937 gen;
		std::uniform_int_distribution<int> distrib;
		std::vector<std::pair<std::vector<float>, int>> _dataset;
		size_t _max_depth=10, _min_split=5;
		int predicted_label;
		std::ofstream outfile;
		void _get_train_test_data(std::vector<std::pair<std::vector<float>, int>>& data, float train_test_ratio);    // Function to return train and test data
		std::vector<std::pair<std::vector<float>, int>> _training_dataset, _testing_dataset;		// vectors to store train and test dataset
		float _gini_impurity(std::vector<int>& labels);                                                    // Function to compute Gini impurity
		void _find_best_feature(std::vector<std::pair<std::vector<float>, int>>& data);      // Function to find the best feature, threshold, and best gini for a tree node
		size_t _best_feature_idx, _dataset_size;                                   
		float _best_feature_threshold, _best_feature_gini, _current_best_gini, _relative_weight;
		void _split_dataset(std::vector<std::pair<std::vector<float>, int>>& data, size_t feature_idx, float feature_threshold);  // Function to split the data for a given feature index and threshold
		std::vector<std::pair<std::vector<float>, int>> _split_dataset_left, _split_dataset_right;                      // vectors to store the split data for a tree node
};

#endif

