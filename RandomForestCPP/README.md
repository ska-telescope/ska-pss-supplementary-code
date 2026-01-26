This repositiory provides Cpp implementation of the Random Forest classifier for the spsift module. 
The trained model generated from this repository can be directly used in the rfsift sub-module of the spsift module. <br>  
Source directory contains header and cpp files for MakeRFClassifier (to train, test, and write out a RF model), LoadRFClassifer (to load a trained model written by MakeRFClassifer and use it for classification),
 and RFDecisionTree (class to make decision tree for the MakeRFClassifier).
 These utilities from the source directory are used in the main cpp code Test_RandomForest.cpp. This code can be used to train, test, and write out models. <br>
 
 **Syntax to compile:** g++ Test_RandomForest.cpp -o Test_RandomForest source/MakeRFClassifier.cpp source/RFDecisionTree.cpp <br>
 **Syntax to use:** ./Test_RandomForest <astrophysical_signal_features> <rfi_features> <sifting_threshold> <max_depth> <min_split> <nfeatures_at_split> <number_fo_trees> <number_of_samples_to_train>  <br>

 This will write a txt file called "TrainedRandomForest.txt" with the trained model in it. <br>

 The other main cpp file Test_loadforest.cpp is used to load the trained model and use it to classify feature instances. <br>

 **Syntax to compile:** g++ Test_loadforest.cpp -o Test_loadforest source/LoadRFClassifier.cpp   <br>
 **Syntax to use:** ./Test_loadforest  <astrophysical_signal_features> <rfi_features> <sifting_threshold> <input_model_file> <instaces> <br>

 The script get_features_spccls.py can be used to compute the features of spccl files obtained from PSS-Cheetah. This needs the folder with spccl files are kept along with detection and sifting threshold to compute features. 