import argparse
import os
import sys
from .config import Config
from .analysis.token_count_model import TokenCountModel
from .analysis.n_gram_model import NGramModel
from .analysis.reporting import ReportingService
from .analysis.runner import AnalysisRunner

class Pygram:

    def __init__(self) -> None:
        self.config: Config = Config()
        self.count_model_path: str = None
        self.token_count_model: TokenCountModel = None
        self.project_path: str = None

    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = argparse.ArgumentParser(prog="pygram",
                                        description="N-Gram code analysis for Python projects")
        parser.add_argument("-d", help="Analyse directory")
        parser.add_argument("-t", action="store_true", help="This flag enables processing of type annotations. The type information added to the tokens")
        parser.add_argument("-o", help="Set a minimum token occurrence. Standard value is 2")
        parser.add_argument("-c", help="Specify a config file for Pygram")
        parser.add_argument("--load-model", help="Load model from file (.json)")
        parser.add_argument("--save-model", nargs=2, help="Save the intermediate token count model to a file")
        parser.add_argument("--gram-size", help="Set gram size to perform analysis with. Standard value is 3")
        parser.add_argument("--sequence-length", help="Set sequence length for the sequences used in the n-gram model. Standard value is 6")
        parser.add_argument("--reporting-size", help="Set reporting size. Standard value is 10")
        parser.add_argument("--deactivate-token-line-numbers", help="Removes the line numbers for the tokens. Also in the saved token count model. This option makes the count model invalid for the analysis", action="store_true")

        return parser
    
    @staticmethod
    def _load_token_count_model_from_file(path) -> TokenCountModel:
        file_path: str = os.path.abspath(path)
        loaded_model: TokenCountModel = None

        print("Attempting to load token model...")
        if os.path.isfile(file_path) and file_path.endswith(".json"):
            model: TokenCountModel = TokenCountModel.load_from_file(file_path)
            if model is None:
                print("Could not load file")
            else:
                loaded_model = model
                print("Successfully loaded model!")
        else:
            print("Not a .json file!")
        
        return loaded_model
    
    def _set_token_model_save_parameters(self, path, name) -> bool:

        if not os.path.exists(path):
            print("The path for saving the token count model does not exist!")
            return False
        
        if name is None:
            print("No name for the model is specified!")
            return False

        if self.token_count_model is not None:
            print("Save model cannot be performed when a model was just loaded.")
            return False
        
        self.count_model_path = os.path.join(path, name + ".json")
        return True
    
    def _analyze_project(self):
        if self.project_path is not None:
            project_name, sequence_list = AnalysisRunner.tokenize_project(self.project_path, self.config.use_type_info)
            self.token_count_model = AnalysisRunner.create_and_save_count_model(project_name, sequence_list, self.count_model_path)
        
        if self.token_count_model is not None:
            ngram_model: NGramModel = AnalysisRunner.build_n_gram_model(
                token_count_model=self.token_count_model,
                gram_size=self.config.gram_size,
                min_token_count=self.config.minimum_token_occurrence,
                sequence_length=self.config.sequence_length
                )
            report: ReportingService = AnalysisRunner.create_report(self.token_count_model, ngram_model, self.config.reporting_size)
            print(str(report))


    def start(self):
        if not len(sys.argv[1:]):
            print("For usage information use the -h parameter")
        else:
            arguments = self._create_parser().parse_args()

            if arguments.t:
                self.config.use_type_info = True
            
            if arguments.o is not None:
                self.config.minimum_token_occurrence = int(arguments.o)
            
            if arguments.gram_size is not None:
                self.config.gram_size = int(arguments.gram_size)
            
            if arguments.sequence_length is not None:
                self.config.sequence_length = arguments.sequence_length
            
            if arguments.reporting_size is not None:
                self.config.reporting_size = arguments.reporting_size
            
            if arguments.load_model is not None:
                self.token_count_model = Pygram._load_token_count_model_from_file(arguments.load_model)
                if self.token_count_model is None:
                    return

            if arguments.save_model is not None:
                path, name = arguments.save_model
                if not self._set_token_model_save_parameters(path, name):
                    return

            if arguments.deactivate_token_line_numbers:
                self.config.save_token_line_numbers = False

            if arguments.d is not None:
                if self.token_count_model is not None:
                    print("There already is a token count model loaded. Skipping processing of given project directory step!")
                else:
                    self.project_path = arguments.d
            
            if arguments.c is not None:
                self.config = Config.load_from_file(arguments.c)
            
            if self.config.do_analysis_run:
                analysis_runner: AnalysisRunner = AnalysisRunner(
                    self.token_count_model,
                    self.config.analysis_run,
                    self.config.reporting_size,
                    self.project_path
                    )
                analysis_runner.start()
            else:
                self._analyze_project()
