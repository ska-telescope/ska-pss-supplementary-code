#ifndef RFDECISION_TREE_H
#define RFDECISION_TREE_H

#include <vector>
#include <bits/stdc++.h>

class GetFeatures
{
    public:
        GetFeatures(std::vector<float>& time, std::vector<float>& dm, std::vector<float>& width, std::vector<float>& snr, float& Threshold);     // Constructor, currently takes ascii filename as input, but later it will directly take the four axes as input
        GetFeatures() = default;
	std::vector<float> compute_features();               // Main member function that computes the features [_best_snr, _best_dm, _best_width, _dm_width, _time_width, _cluster_size, _ds_symmetry, _ds_flatness, _td_slope, _td_scatter]
    private:
    // Vectors to store the four axes
        std::vector<float> _time_axis;
        std::vector<float> _dm_axis;
        std::vector<float> _width_axis;
        std::vector<float> _snr_axis;
	// Variables to store features

	float _best_snr, _best_dm, _best_width, _dm_width, _time_width, _cluster_size, _ds_symmetry, _ds_flatness, _td_slope, _td_scatter; //variables to store the features
	float _threshold;             // variable to store detection threshold, to be used in DM-SNR features


	// Functions to compute features related to DM-SNR plot (ds_features()) and Time-DM plot (td_features())
	void _simple_features();                // Simple features (_best_snr, _best_dm, _best_width, _dm_width, _time_width, _cluster_size)
	void _ds_features();                    // Features in DM-SNR plane (_ds_symmetry, _ds_flatness)
	void _td_features();                    // Features in Time DM plane (_td_slope, _td_scatter)
	std::vector<float> features();          // Compiles all the individual features in a std::vector and returns it

	// Function for linear fitting on TD plane

	float _offset, _slope, _scatter;
	void _linear_fitting(const std::vector<float>& , const std::vector<float>& );


};
#endif
