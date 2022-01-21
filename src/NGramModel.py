from decimal import Decimal
from typing import List
from src.TokenCountModel import TokenCountModel


class NGramModel:

    def __init__(self, token_count_model: TokenCountModel,
                 gram_size: int, max_sequence_length: int,
                 reporting_size: int, split_sequences: bool
                 ) -> None:
        self.token_count_model = token_count_model
        self.gram_size = gram_size
        self.max_sequence_length = max_sequence_length
        self.reporting_size = reporting_size
        self.split_sequences = split_sequences
    

    def build(self):
        """
        Builds the n gram language model and calculates the probabilities for all sequences
        """
        split_sequences: List = self._split_sequences()
        pass

    def _split_sequences(self) -> List:
        sequences: List = self.token_count_model.get_sequence_list_without_module_info()
        max: int = self.max_sequence_length
        split_sequences: List = []

        for sequence in iter(sequences):
            if len(sequence) > max:
                
                if self.split_sequences:
                    self._hard_split_sequence(sequence, split_sequences)
                else:
                    self._split_sequence_with_sliding_window(sequence, split_sequences)

            else:
                split_sequences.append(sequence)

        return split_sequences

    def _hard_split_sequence(self, sequence: List, sequence_list: List) -> None:
        for i in range(0, len(sequence), max):
            sequence_list.append(sequence[i:i + max])
    
    def _split_sequence_with_sliding_window(self, sequence, sequence_list: List) -> None:
        for i in range(0, len(sequence) - self.max_sequence_length):
            sequence_list.append(sequence[i:i + self.max_sequence_length])

    
    def _calculate_relative_frequency(self, token, prefix) -> Decimal:
        combined: str = prefix + token
        combined_count = self.token_count_model.get_token_count(combined)
        prefix_count = self.token_count_model.get_token_count(prefix)
        relative_frequency: Decimal = Decimal(str(combined_count /  prefix_count)).quantize(Decimal('1e-4'))
        return relative_frequency
    
    def _calculate_sequence_probability(self):
        pass
        

    
