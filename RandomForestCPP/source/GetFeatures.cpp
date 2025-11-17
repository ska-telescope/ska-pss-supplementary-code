#include "GetFeatures.h"

GetFeatures::GetFeatures(std::vector<float>& time, std::vector<float>& dm, std::vector<float>& width, std::vector<float>& snr, float& Threshold)
    : _time_axis(time), _dm_axis(dm), _width_axis(width), _snr_axis(snr), _threshold(Threshold)
{
}

std::vector<float> GetFeatures::compute_features()
{
    _simple_features();
    _ds_features();
    _td_features();
    return features();
}

void GetFeatures::_simple_features()
{
    size_t max_idx;
    max_idx = std::max_element(_snr_axis.begin(), _snr_axis.end()) - _snr_axis.begin();
    _best_snr = _snr_axis[max_idx];
    _best_width = _width_axis[max_idx];
    _best_dm = _dm_axis[max_idx];
    _dm_width = *std::max_element(_dm_axis.begin(), _dm_axis.end()) - *std::min_element(_dm_axis.begin(), _dm_axis.end());
    _time_width = *std::max_element(_time_axis.begin(), _time_axis.end()) - *std::min_element(_time_axis.begin(), _time_axis.end());
    _cluster_size = _snr_axis.size();
}

void GetFeatures::_ds_features()
{
    float max_snr, median_snr, left_dm, mid_dm, right_dm, left_extent, right_extent;
    size_t max_idx;
    std::vector<float> snr_points, dm_points, sorted_snr;
    max_snr = *std::max_element(_snr_axis.begin(), _snr_axis.end());
    sorted_snr = _snr_axis;
    std::sort(sorted_snr.begin(), sorted_snr.end());
    size_t mid_idx = sorted_snr.size()/2.0;
    median_snr = sorted_snr[mid_idx];
    _ds_flatness = (max_snr - _threshold)/(median_snr - _threshold);           // Flatness of DM vs SNR plot

    float threshold_at_30percent_height = _threshold + 0.3*(max_snr - _threshold);       // Introducing untuned parameter, considers points above 30% of the peak snr to compute symmetry
    auto itry = _dm_axis.begin();
    for(auto itrx = _snr_axis.begin(); itrx != _snr_axis.end(); ++itrx, ++itry)
    {
        if(*itrx > threshold_at_30percent_height)
	{
	    snr_points.push_back(*itrx);
	    dm_points.push_back(*itry);
	}
    }

    max_idx = std::max_element(snr_points.begin(), snr_points.end()) - snr_points.begin();
    std::pair<std::vector<float>::iterator, std::vector<float>::iterator> mnmx = std::minmax_element(dm_points.begin(), dm_points.end());
    left_dm = *mnmx.first;
    mid_dm = dm_points[max_idx];
    right_dm = *mnmx.second;
    left_extent = mid_dm - left_dm;
    right_extent = right_dm - mid_dm;
    _ds_symmetry = left_extent/right_extent;                                // Symmetry of DM vs SNR plot
}


void GetFeatures::_td_features()
{
    std::vector<float> _time_vector;
    float first_TOA = *std::min_element(_time_axis.begin(), _time_axis.end());
    for(size_t i=0; i < _time_axis.size(); ++i)
    {
	_time_vector.push_back(_time_axis[i] - first_TOA);
    }
    _linear_fitting(_time_vector, _dm_axis);
    _td_slope = _slope;
    _td_scatter = _scatter;
}

void GetFeatures::_linear_fitting(const std::vector<float>& axisX, const std::vector<float>& axisY)
{
    size_t n=axisX.size();
    float sumX = std::reduce(axisX.begin(), axisX.end(), 0.0);
    float sumY = std::reduce(axisY.begin(), axisY.end(), 0.0);
    float sumXX = std::transform_reduce(axisX.begin(), axisX.end(), 0.0, std::plus{}, [](auto x) { return x * x; });
    float sumXY = std::inner_product(axisX.begin(), axisX.end(), axisY.begin(), 0.0);
    if((sumX*sumX - n*sumXX) == 0){throw std::runtime_error( "Instance of dividing by zero happening in fitting within GetFeature class" );exit(1);}
    _slope = (sumX*sumY - n*sumXY)/(sumX*sumX - n*sumXX);
    _offset = (sumY - _slope*sumX)/float(n);
    float deviation = std::transform_reduce(axisX.begin(), axisX.end(), axisY.begin(), 0.0, std::plus{}, [&](auto x, auto y) { return (y- (_slope*x+_offset))*(y- (_slope*x+_offset));});
    _scatter = deviation/float(n);
}

std::vector<float> GetFeatures::features(){
    std::vector<float> output_vector;
    output_vector.push_back(_best_snr);
    output_vector.push_back(_best_dm);
    output_vector.push_back(_best_width);
    output_vector.push_back(_dm_width);
    output_vector.push_back(_time_width);
    output_vector.push_back(_cluster_size);
    output_vector.push_back(_ds_symmetry);
    output_vector.push_back(_ds_flatness);
    output_vector.push_back(_td_slope);
    output_vector.push_back(_td_scatter);

    return output_vector;
}
