
import os
import logging
import json
from typing import List

logger = logging.getLogger("main")

CONFIG_OPTS: List[str] = [
    "use_type_info",
    "gram_size",
    "sequence_length",
    "minimum_token_occurrence",
    "reporting_size",
    "save_token_line_numbers",
    "do_analysis_run"
]

RUNNER_CONFIG_OPTS: List[str] = [
    "analysis_result_folder",
    "report_name_prefix",
    "gram_sizes",
    "sequence_lengths",
    "minimum_token_occurrences",
    "typed",
    "untyped"
]

class RunnerConfig():

    def __init__(self, 
    sequence_lengths: List[int], 
    gram_sizes: List[int],
    minimum_token_occurrences: List[int],
    report_name_prefix: str,
    typed: bool,
    untyped: bool,
    analysis_result_folder: str,
    ) -> None:
        self.sequence_lengths: List[int] = sequence_lengths
        self.gram_sizes: List[int] = gram_sizes
        self.minimum_token_occurrences: List[int] = minimum_token_occurrences
        self.report_name_prefix: str = report_name_prefix
        self.typed: bool = typed
        self.untyped: bool = untyped
        self.analysis_result_folder: str = analysis_result_folder
    

    @staticmethod
    def config_file_is_valid(json_config):
        for option in RUNNER_CONFIG_OPTS:
             if option not in json_config:
                 return False
        return True
    
    @staticmethod
    def from_json(json_config) -> "RunnerConfig":
        if RunnerConfig.config_file_is_valid(json_config):
            new_config: RunnerConfig = RunnerConfig(
                sequence_lengths=json_config["sequence_lengths"],
                gram_sizes=json_config["gram_sizes"],
                report_name_prefix=json_config["report_name_prefix"],
                typed=json_config["typed"],
                untyped=json_config["untyped"],
                minimum_token_occurrences=json_config["minimum_token_occurrences"],
                analysis_result_folder=json_config["analysis_result_folder"]
            )
            return new_config

class Config:

    def __init__(self, 
    use_type_info: bool = False,
    gram_size: int = 3,
    sequence_length: int = 4,
    minimum_token_occurrence: int = 3,
    reporting_size: int = 10,
    save_token_line_numbers: bool = True,
    do_analysis_run: bool = False,
    analysis_run: RunnerConfig = None
    ) -> None:
        self.use_type_info: bool = use_type_info
        self.gram_size: int = gram_size
        self.sequence_length: int = sequence_length
        self.minimum_token_occurrence: int = minimum_token_occurrence
        self.reporting_size: int = reporting_size
        self.save_token_line_numbers: bool = save_token_line_numbers
        self.do_analysis_run: bool = do_analysis_run
        self.analysis_run: RunnerConfig = analysis_run
    
    @staticmethod
    def load_from_file(file_path: str) -> "Config":
        if os.path.isfile(file_path):
            with open(file_path, "r") as configfile:
                config = json.load(configfile)

                if Config.config_file_is_valid(config):
                    runner_config: RunnerConfig = None
                    if "analysis_run" in config:
                        runner_config = RunnerConfig.from_json(config["analysis_run"]) 
                    new_config = Config(
                        use_type_info=config["use_type_info"],
                        gram_size=config["gram_size"],
                        sequence_length=config["sequence_length"],
                        minimum_token_occurrence=config["minimum_token_occurrence"],
                        reporting_size=config["reporting_size"],
                        do_analysis_run=config["do_analysis_run"],
                        analysis_run=runner_config
                    )
                    print("Successfully loaded config file")
                    return new_config
                else:
                    logger.error("Specified config file has invalid format!")
                    raise RuntimeError()
        else:
            logger.error("Specified config ist not a file")
            raise FileNotFoundError()
                    
    
    @staticmethod
    def config_file_is_valid(json_config):
        for option in CONFIG_OPTS:
             if option not in json_config:
                 return False
        return True

    