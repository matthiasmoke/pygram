import argparse
import os
import sys
from .type_retrieval.preprocessed_type_caches import TypeCache
from .type_retrieval.project_preprocessor import TypePreprocessor
from .TokenCountModel import TokenCountModel
from .NGramModel import NGramModel
from .utils import Utils
from .tokenization.tokenizer import Tokenizer
from .tokenization.type_tokenizer import TypeTokenizer
from .Reporting import ReportingService

from typing import Dict, Tuple, List

class Pygram:

    def __init__(self) -> None:
        self.use_type_info: bool = False
        self.gram_size: int = 3
        self.sequence_length: int = 6
        self.split_sequences: bool = False
        self.minimum_token_count: int = 3
        self.reporting_size: int = 10
        self.count_model_path: os.path = None
        self.token_count_model: TokenCountModel = None
        self.project_path: str = None

    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="pygram",
                                        description="N-Gram code analysis for Python projects")
        parser.add_argument("-f", help="Analyse single Python file")
        parser.add_argument("-d", help="Analyse directory")
        parser.add_argument("-t", action="store_true", help="This flag enables processing of type annotations. The type information added to the tokens")
        parser.add_argument("-o", help="Set a minimum token occurrence. Standard value is 2")
        parser.add_argument("--split-sequences", action="store_true", help="Split token sequences instead of using a sliding window")
        parser.add_argument("--load-model", help="Load model from file (.json)")
        parser.add_argument("--save-model", nargs=2, help="Save the intermediate token count model to a file")
        parser.add_argument("--gram-size", help="Set gram size to perform analysis with. Standard value is 3")
        parser.add_argument("--sequence-length", help="Set sequence length for the sequences used in the n-gram model. Standard value is 6")
        parser.add_argument("--reporting-size", help="Set reporting size. Standard value is 10")

        return parser
    
    @staticmethod
    def _load_token_count_model_from_file(path) -> TokenCountModel:
        file_path: os.path = os.path.abspath(path)
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
    
    def _tokenize_project(self, directory: str) -> Tuple[str, Dict]:
        sequence_list: Dict[str, List[Tuple[str, int]]] = {}
        python_files = Utils.get_all_python_files_in_directory(directory)
        counter: int = len(python_files)
        directory_name = os.path.basename(directory)
        type_cache: TypeCache = None
        print("Detected {} Python files".format(counter))

        if self.use_type_info:
            print("Preprocessing the project for types...")
            preprocessor: TypePreprocessor = TypePreprocessor(directory)
            type_cache: TypeCache = preprocessor.process_project()

        for (index, file) in enumerate(python_files):
            print("[{}/{}] Processing \"{}\"".format(index + 1, counter, file))
            path: os.path = os.path.abspath(file)

            if os.path.isfile(path):
                path_within_project: str = Utils.get_only_project_path(directory, path)
                module_path: str = Utils.generate_dotted_module_path(path_within_project)

                if (self.use_type_info):
                    tokenizer: TypeTokenizer = TypeTokenizer(path, module_path, type_cache)
                else:
                    tokenizer: Tokenizer = Tokenizer(path, module_path)
                file_tokens: List[Tuple(str, int)] = tokenizer.process_file()
                sequence_list[path_within_project] = file_tokens
        return directory_name, sequence_list
    
    def _analyze_project(self):
        if self.project_path is not None:
            print("Starting to tokenize project...")
            project_name, sequence_list = self._tokenize_project(self.project_path)
            print("Finished")
            print("Building intermediate count model...")
            self.token_count_model = TokenCountModel(sequence_list, name=project_name)
            self.token_count_model.build()
            print("Finished")
            if self.count_model_path:
                self.token_count_model.save_to_file(self.count_model_path)
                print("Saved token count model to: {}".format(self.count_model_path))
        
        if self.token_count_model is not None:
            print("Building n-gram model...")
            ngram_model: NGramModel = NGramModel(
                self.token_count_model,
                self.gram_size,
                self.sequence_length,
                self.minimum_token_count,
                self.split_sequences
            )
            ngram_model.build()
            print("Finished")
            print("Generating Report...")
            report: ReportingService = ReportingService(ngram_model, self.token_count_model.get_sequence_dict(), self.reporting_size)
            report.generate_report()
            print(str(report))


    def start(self):
        if not len(sys.argv[1:]):
            print("For usage information use the -h parameter")
        else:
            arguments = self._create_parser().parse_args()

            if arguments.t:
                self.use_type_info = True
            
            if arguments.o is not None:
                self.minimum_token_count = int(arguments.o)
            
            if arguments.gram_size is not None:
                self.gram_size = int(arguments.gram_size)
            
            if arguments.sequence_length is not None:
                self.sequence_length = arguments.sequence_length
            
            if arguments.reporting_size is not None:
                self.reporting_size = arguments.reporting_size
            
            if arguments.split_sequences:
                self.split_sequences = True
            
            if arguments.load_model is not None:
                self.token_count_model = Pygram._load_token_count_model_from_file(arguments.load_model)
                if self.token_count_model is None:
                    return

            if arguments.save_model is not None:
                path, name = arguments.save_model
                if not self._set_token_model_save_parameters(path, name):
                    return
                    
            if arguments.f is not None:
                path = os.path.abspath(arguments.f)
                if os.path.isfile(path) and path.endswith(".py"):
                    if self.use_type_info:
                        tokenizer: TypeTokenizer = TypeTokenizer(path, "File", None)
                    else:
                        tokenizer: Tokenizer = Tokenizer(path, "File")
                    tokenizer.process_file()
                    print(str(tokenizer))

            if arguments.d is not None:
                if self.token_count_model is not None:
                    print("There already is a token count model loaded. Skipping processing of given project directory step!")
                else:
                    self.project_path = arguments.d
            
            self._analyze_project()
