import os
import logging
from typing import List
from typing import Dict
from typing import Tuple
from datetime import datetime

from .reporting import ReportingService
from .n_gram_model import NGramModel
from .token_count_model import TokenCountModel
from ..config import RunnerConfig
from ..utils import Utils
from ..type_retrieval.preprocessed_type_caches import TypeCache
from ..type_retrieval.project_preprocessor import TypePreprocessor
from ..tokenization.tokenizer import Tokenizer
from ..tokenization.type_tokenizer import TypeTokenizer

logger = logging.getLogger("main")


class AnalysisRunner():

    def __init__(
        self,
        token_count_model: TokenCountModel,
        config: RunnerConfig,
        reporting_size: int,
        project_path: str
    ) -> None:
        self.token_count_model: TokenCountModel = token_count_model
        self.reporting_size: int = reporting_size
        self.config: RunnerConfig = config
        self.project_path: str = project_path

        if not os.path.isdir(config.analysis_result_folder):
            config.analysis_result_folder = os.path.join(os.getcwd(), "..", "..")

        self._typed_count_model: TokenCountModel = None
        self._untyped_count_model: TokenCountModel = None
        self._current_saving_folder: str = None
    
    def start(self):
        """
        Starts the analysis run. Creates a folder that contains the different reports
        """
        result_folder: str = self._generate_result_folder_path()
        self._current_saving_folder = result_folder
        os.mkdir(self._current_saving_folder)

        if self._maybe_create_count_models():
            if self.config.untyped:
                print("Starting untyped analysis run...")
                self._current_saving_folder = os.path.join(result_folder, "untyped")
                os.mkdir(self._current_saving_folder)
                self.do_analysis_run(self._untyped_count_model)

            if self.config.typed:
                print("Starting typed analysis run...")
                self._current_saving_folder = os.path.join(result_folder, "typed")
                os.mkdir(self._current_saving_folder)
                self.do_analysis_run(self._typed_count_model)
        else:
            print("Starting typed analysis run...")
            self.do_analysis_run(self.token_count_model)

    def do_analysis_run(self, token_count_model: TokenCountModel) -> None:
        """
        Runs the analysis for a specified token count model by creating n-gram models for every combination of the specified parameters
        """
        gram_sizes: List[int] = self.config.gram_sizes
        sequence_lengths: List[int] = self.config.sequence_lengths
        min_token_counts: List[int] = self.config.minimum_token_occurrences

        for min_token_count in min_token_counts:
            for gram_size in gram_sizes:
                for sequence_length in sequence_lengths:
                    
                    if sequence_length >= gram_size:
                        gram_model: NGramModel = AnalysisRunner.build_n_gram_model(
                            token_count_model,
                            gram_size, 
                            sequence_length,
                            min_token_count
                        )
                        report: ReportingService = AnalysisRunner.create_report(token_count_model, gram_model, self.reporting_size)
                        self.save_report(report)

    def save_report(self, report: ReportingService):
        prefix = self.config.report_name_prefix

        if prefix is None or prefix == "":
            prefix = "pygram_report"

        file_name: str = "{}_n-{}_sl-{}_toc-{}".format(
            prefix,
            report.language_model.gram_size,
            report.language_model.max_sequence_length,
            report.language_model.minimum_token_occurrence
        )
        report.save_to_file(self._current_saving_folder, file_name)
        print("Saved report as {}.txt".format(file_name))

    def _generate_result_folder_path(self, index=0) -> str:
        result_folder_name: str = "Pygram Analysis - {}".format(datetime.now().strftime("%d.%m %H:%M"))

        if index > 0:
            result_folder_name += " ({})".format(str(index))

        result_folder: str = os.path.join(self.config.analysis_result_folder, result_folder_name)
        if os.path.exists(result_folder):
            index += 1
            return self._generate_result_folder_path(index=index)
        return result_folder

    def _maybe_create_count_models(self) -> bool:
        """
        Creates un-/typed token count models for the specified project
        """
        if self.token_count_model is not None:
            return False
        
        if self.config.untyped:
            project_name, sequences = AnalysisRunner.tokenize_project(self.project_path, False)
            file_name: str = "{}_count_model_untyped.json".format(project_name)
            save_path: str = os.path.join(self._current_saving_folder, file_name)
            self._untyped_count_model = AnalysisRunner.create_and_save_count_model(project_name, sequences, save_path)
        
        if self.config.typed:
            project_name, sequences = AnalysisRunner.tokenize_project(self.project_path, True)
            file_name: str = "{}_count_model_typed.json".format(project_name)
            save_path: str = os.path.join(self._current_saving_folder, file_name)
            self._typed_count_model = AnalysisRunner.create_and_save_count_model(project_name, sequences, save_path)
        
        return True
            
    @staticmethod
    def tokenize_project(directory: str, typed: bool) -> Tuple[str, Dict]:
        """
        Tokenises a specified project 
        """
        sequence_list: Dict[str, List[Tuple[str, int]]] = {}
        python_files = Utils.get_all_python_files_in_directory(directory)
        counter: int = len(python_files)
        directory_name = os.path.basename(directory)
        type_cache: TypeCache = None

        total_number_of_call_tokens: int = 0
        number_of_type_inferred_call_tokens: int = 0

        total_number_of_assigns: int = 0
        number_of_annotated_assigns: int = 0
        print("Starting to tokenize project...\nDetected {} Python files".format(counter))

        if typed:
            print("Preprocessing the project for types...")
            preprocessor: TypePreprocessor = TypePreprocessor(directory)
            type_cache: TypeCache = preprocessor.process_project()

        for (index, file) in enumerate(python_files):
            print("[{}/{}] Processing \"{}\"".format(index + 1, counter, file))
            path: os.path = os.path.abspath(file)

            if os.path.isfile(path):
                path_within_project: str = Utils.get_only_project_path(directory, path)
                module_path: str = Utils.generate_dotted_module_path(path_within_project)

                if typed:
                    tokenizer: TypeTokenizer = TypeTokenizer(path, module_path, type_cache)
                else:
                    tokenizer: Tokenizer = Tokenizer(path, module_path)
                file_tokens: List[List[Tuple[str, int]]] = tokenizer.process_file()

                if typed:
                    number_of_type_inferred_call_tokens += tokenizer.number_of_type_inferred_call_tokens
                    total_number_of_call_tokens += tokenizer.number_of_call_tokens
                    number_of_annotated_assigns += tokenizer.number_of_ann_assigns
                    total_number_of_assigns += tokenizer.number_of_assigns

                sequence_list[path_within_project] = file_tokens

        if typed:
            print("Total number of call tokens: {}".format(total_number_of_call_tokens))
            print("Number of type inferred call tokens: {}".format(number_of_type_inferred_call_tokens))
            print("Type inference success: {}\n".format(
                str(number_of_type_inferred_call_tokens / total_number_of_call_tokens)))

            print("Total number of assigns: {}".format(total_number_of_assigns))
            print("Number of annotated assigns: {}".format(number_of_annotated_assigns))
            print("Percentage of annotated variable assignments: {}".format(
                str(number_of_annotated_assigns / total_number_of_assigns)))
        print("Finished tokenization process")
        return directory_name, sequence_list
    
    @staticmethod
    def create_and_save_count_model(project_name: str, sequences: Dict, save_path: str=None) -> TokenCountModel:
        print("Building token count model...")
        count_model: TokenCountModel = TokenCountModel(sequences, name=project_name)
        count_model.build()
        
        if save_path is not None:
            count_model.save_to_file(save_path)
            print("Finished. Saved it to {}".format(save_path))
        return count_model
    
    @staticmethod
    def build_n_gram_model(token_count_model: TokenCountModel, gram_size: int, sequence_length: int, min_token_count: int) -> NGramModel:
        print("Building n-gram model. Gram-size: {}, Sequence length: {}, Min. token count: {}"
        .format(gram_size, sequence_length, min_token_count))

        model: NGramModel = NGramModel(
            token_count_model,
            gram_size,
            sequence_length,
            min_token_count,
        )
        model.build()
        print("Done.")
        return model

    @staticmethod
    def create_report(token_count_model: TokenCountModel, gram_model: NGramModel, reporting_size: int) -> ReportingService:
        print("Generating Report...")
        report: ReportingService = ReportingService(gram_model, token_count_model.get_sequence_dict(), reporting_size)
        report.generate_report()
        print("Finished")
        return report

