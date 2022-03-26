from curses import noecho
from re import T
from typing import List

from .reporting import ReportingService
from .n_gram_model import NGramModel
from .token_count_model import TokenCountModel
from ..config import RunnerConfig


class AnalysisRunner():

    def __init__(self, token_count_model: TokenCountModel, config: RunnerConfig, reporting_size: int) -> None:
        self.token_count_model: TokenCountModel = token_count_model
        self.repoting_size: int = reporting_size
        self.config: RunnerConfig = config
    
    def do_analysis_run(self) -> None:
        gram_sizes: List[int] = self.config.gram_sizes
        sequence_lengths: List[int] = self.config.sequence_lengths
        min_token_counts: List[int] = self.config.minimum_token_occurrences

        print("Starting analysis run...")
        for min_token_count in min_token_counts:
            for gram_size in gram_sizes:
                for sequence_length in sequence_lengths:
                    self.analyze_with_parameters(gram_size, sequence_length, min_token_count)


    def analyze_with_parameters(self, gram_size: int, sequence_length: int, min_token_count: int) -> ReportingService:
        print("Building n-gram model. Gram-size: {}, Sequence length: {}, Min. token count: {}"
        .format(gram_size, sequence_length, min_token_count))

        model: NGramModel = NGramModel(
            self.token_count_model,
            gram_size,
            sequence_length,
            min_token_count,
        )
        model.build()
        print("Done.")
        print("Generating Report...")
        report: ReportingService = ReportingService(model, self.token_count_model)
        report.generate_report()
        return report
    
    def save_with_parameters(self, gram_size: int, sequence_length: int, min_token_count: int):
        pass



