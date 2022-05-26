# Pygram

Pygram is a tool that let's you perform an n-gram model analysis on Python projects to find code sequences with potential bugs.
For usage information run ``python main.py -h``

## Command line parameters
Possible command line parameters:

     -d [PATH] Option to specify a directory which contains the project to be analyzed. Is used only if --load-model is not set.
     
     -c [PATH] Option to specify a configuration file that contains analysis parameters.

     -t If this flag is set, typed tokenisation is activated.

     -o [NUMBER] Set the minimum token occurrence. The default value is 3.

     --save-model [PATH] [NAME] Option to save the TokenCountModel.

     --load-model [PATH] Option to load a TokenCountModel.

     --gram-size [NUMBER] Set gram size. The default value is 3.

     --sequence-length [NUMBER] Set sequence length. The default value is 4.

     --reporting-size [NUMBER] Set the reporting size. The default value is 10.
     
     --deactivate-line-numbers If this option is set, the tokens within sequences are saved without line number information. This option exists only for debugging purposes and the resulting TokenCountModel can not be used for analysis.

## Configuration file
Pygram is also configurable via a config file:

    {
        "use_type_info": false,
        "gram_size": 3,
        "sequence_length": 3,
        "minimum_token_occurrence": 3,
        "reporting_size": 10,
        "token_count_model_name": "",
        "save_token_line_numbers": true,
        "do_analysis_run": true,
        "analysis_run": {
            "analysis_result_folder": "",
            "gram_sizes": [ 2, 3, 4, 5, 6 ],
            "sequence_lengths": [4, 5, 6, 7 ],
            "minimum_token_occurrences": [ 3 ],
            "report_name_prefix": "",
            "typed": true,
            "untyped": true
        }
    }