from re import T
from typing import List
from .token_count_model import TokenCountModel
from ..config import RunnerConfig


class AnalysisRunner():

    def __init__(self, token_count_model: TokenCountModel, config: RunnerConfig) -> None:
        self.token_count_model: TokenCountModel = token_count_model
        self.config: RunnerConfig = config

