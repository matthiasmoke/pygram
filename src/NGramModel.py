from decimal import Decimal
from sys import prefix
from typing import Dict, List
from src.TokenCountModel import TokenCountModel


class NGramModel:

    def __init__(self, token_count_model: TokenCountModel,
                 gram_size: int, max_sequence_length: int, split_sequences: bool
                 ) -> None:
        self.token_count_model: TokenCountModel = token_count_model
        self.gram_size: int = gram_size
        self.max_sequence_length: int = max_sequence_length
        self.split_sequences: int = split_sequences
        self.model: Dict = {}
    

    def build(self):
        """
        Builds the n gram language model and calculates the probabilities for all sequences
        """
        split_sequences: List = self._split_sequences()
        for sequence in split_sequences:
            if sequence not in self.model:
                probability: Decimal = self._calculate_sequence_probability(sequence)
                sequence_string: str = self._get_sequence_string(sequence)
                self.model[sequence_string] = probability

    def _split_sequences(self) -> List:
        sequences: List[List[str]] = self.token_count_model.get_sequence_list_without_module_info()
        max: int = self.max_sequence_length
        split_sequences: List[List[str]] = []

        for sequence in iter(sequences):
            if len(sequence) > max:
                
                if self.split_sequences:
                    self._hard_split_sequence(sequence, split_sequences)
                else:
                    self._split_sequence_with_sliding_window(sequence, split_sequences)

            else:
                split_sequences.append(sequence)

        return split_sequences

    def _hard_split_sequence(self, sequence: List[str], sequence_list: List[List[str]]) -> None:
        for i in range(0, len(sequence), max):
            sequence_list.append(sequence[i:i + max])
    
    def _split_sequence_with_sliding_window(self, sequence: List[str], sequence_list: List[List[str]]) -> None:
        for i in range(0, len(sequence) - self.max_sequence_length):
            sequence_list.append(sequence[i:i + self.max_sequence_length])

    def _get_sequence_string(self, sequence) -> str:
        output: str = ""
        for token in sequence:
            output += token
        return output

    def _calculate_relative_frequency(self, token: str, prefix: str) -> Decimal:
        combined: str = prefix + token
        combined_count = self.token_count_model.get_token_count(combined)
        prefix_count = self.token_count_model.get_token_count(prefix)
        relative_frequency: Decimal = Decimal(str(combined_count /  prefix_count)).quantize(Decimal('1e-4'))
        return relative_frequency
    
    def _calculate_single_probability(self, token: str) -> Decimal:
        all_token_count: int = self.token_count_model.get_number_of_distinct_single_tokens()
        token_count: int = self.token_count_model.get_token_count(token)
        probability: Decimal = Decimal(str(token_count/all_token_count)).quantize(Decimal('1e-4'))
        return probability
    
    def _calculate_sequence_probability(self, sequence: List[str]) -> Decimal:
        current_token: str = sequence[0]
        current_prefix: str = sequence[0]
        index_of_prefix_to_remove: str = 0
        number_of_prefixes: int = 1

        if __debug__:
            probabilities: List[Decimal] = []

        probability: Decimal = self._calculate_single_probability(current_token)

        if __debug__:
            probabilities += probability

        for i in range(1, len(sequence)):
            current_token = sequence[i]
            prob: Decimal = self._calculate_relative_frequency(current_token, current_prefix)
            probability = probability * prob

            if __debug__:
                probabilities += prob

            # if the prefix does not have the length of n - 1 of the n-gram, just append the next token to it
            if number_of_prefixes < self.gram_size - 1:
                current_prefix += current_token
                number_of_prefixes += 1
            else:
                # cut the first token of the prefix
                current_prefix = current_prefix[0:len(sequence[index_of_prefix_to_remove])]
                # set the new prefix to remove to the token which comes next in the sequence
                index_of_prefix_to_remove += 1
                # append the current token to the prefix
                current_prefix += current_token
        
        return probability
                
        

    