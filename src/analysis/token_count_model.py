
import json
from typing import Dict
from typing import List
from typing import Tuple

class TokenCountModel():
    
    def __init__(self, 
        token_sequences={},
        name="",
        count_model={},
        single_tokens={},
        shortest_sequence_length=0,
        longest_sequence_length=0,
        save_line_numbers: bool = True
    ):
        self.token_sequences: Dict[str, List[Tuple[str, int]]] = token_sequences
        self.count_model: Dict[str, int] = count_model
        self.single_tokens: Dict[str, int] = single_tokens
        self.name: str = name
        self.shortest_sequence_length: int = shortest_sequence_length
        self.longest_sequence_length: int = longest_sequence_length
        self._number_of_single_tokens_cache: int = None
        self.save_line_numbers: bool = save_line_numbers

    @staticmethod
    def load_from_file(path) -> "TokenCountModel":
        with open(path, 'r') as inputfile:
            model = json.load(inputfile)
            if model is not None:
                if TokenCountModel._loaded_model_is_valid(model):
                    saved_line_numbers: bool = model["saved_line_numbers"] == "true"

                    if not saved_line_numbers:
                        raise RuntimeError("A tokencount model without line numbers serves on ly debug purposes and cannot be imported again.")

                    loaded_token_sequences: Dict = model["token_sequences"]
                    token_sequences: Dict[str, List[Tuple[str, int]]] = {}
                    for key, sequences in loaded_token_sequences.items():
                        token_sequences[key] = []
                        for sequence in sequences:
                            converted_sequence: List[str, int] = []
                            for token in sequence:
                                converted_sequence.append((token[0], token[1]))
                            token_sequences[key].append(converted_sequence)


                    return TokenCountModel(
                        token_sequences=token_sequences,
                        name=model["project"],
                        count_model=model["count_model"],
                        shortest_sequence_length=model["shortest_sequence_length"],
                        longest_sequence_length=model["longest_sequence_length"],
                        single_tokens=model["single_tokens"],
                        save_line_numbers=saved_line_numbers
                        )
        return None
    

    def save_to_file(self, path: str) -> None:
        saved_sequences = self.token_sequences
        if not self.save_line_numbers:
            converted_token_sequences: Dict[str, List[List[str]]] = {}
            for key, value in self.token_sequences.items():
                converted_token_sequences[key] = []
                for sequence in value:
                    converted_sequence: List[str] = []
                    for token in sequence:
                        converted_sequence.append(token[0])
                    converted_token_sequences[key].append(converted_sequence)
            saved_sequences = converted_token_sequences


        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "saved_line_numbers": self.save_line_numbers,
            "shortest_sequence_length": self.shortest_sequence_length,
            "longest_sequence_length": self.longest_sequence_length,
            "single_tokens": self.single_tokens,
            "token_sequences": saved_sequences,
            "count_model": self.count_model
            }, outfile)

    
    def build(self) -> None:
        """
        Builds the intermediate token count model. 
        This means creating all respective subsequences of a token sequence and counting them.
        """
        for value in self.token_sequences: 
            for sequence in self.token_sequences[value]:
                self._update_sequence_metrics(sequence)
                for (index, token_and_line_no) in enumerate(sequence):
                    # add initial token
                    self._count_single_token(token_and_line_no[0])
                    token_sub_sequence = token_and_line_no[0]
                    # build subsequences of the whole sequence
                    for count in range(index + 1, len(sequence)):
                        token_sub_sequence += sequence[count][0]
                        self._count_token(token_sub_sequence)

    def get_sequence_list_without_meta_data(self) -> List[List[str]]:
        """
        Returns sequence list without any module or line number information
        """
        output: List = []

        for value in self.token_sequences:
            converted_sequences: List[List[str]] = []
            for sequence in self.token_sequences[value]:
                converted_sequence: List[str] = []
                for token in sequence:
                    converted_sequence.append(token[0])
                converted_sequences.append(converted_sequence)

            output += converted_sequences

        return output

    def get_sequence_dict(self) -> Dict[str, List[Tuple[str, int]]]:
        return self.token_sequences
    
    def get_token_count(self, token) -> int:
        """
        Get the count of a token or subsequence
        """
        return self.count_model[token]
    
    def get_number_of_single_tokens(self, minimum_token_count: int) -> int:
        if self._number_of_single_tokens_cache is not None:
            return self._number_of_single_tokens_cache
        
        number_of_single_tokens: int = 0
        for token, count in self.single_tokens.items():
            if count >= minimum_token_count:
                number_of_single_tokens += count
        
        self._number_of_single_tokens_cache = number_of_single_tokens
        return number_of_single_tokens

    def _count_token(self, token_sub_sequence) -> None:
        if token_sub_sequence in self.count_model:
            self.count_model[token_sub_sequence] += 1
        else:
            self.count_model[token_sub_sequence] = 1
    
    def _count_single_token(self, token) -> None:
        if token in self.count_model:
            self.count_model[token] += 1
        else:
            self.count_model[token] = 1

        if token in self.single_tokens:
            self.single_tokens[token] += 1
        else:
            self.single_tokens[token] = 1 
    
    def _update_sequence_metrics(self, sequence) -> None:
        sequence_length: int = len(sequence)

        if self.shortest_sequence_length == 0 or self.shortest_sequence_length > sequence_length:
            self.shortest_sequence_length = sequence_length
        
        if self.longest_sequence_length == 0 or self.longest_sequence_length < sequence_length:
            self.longest_sequence_length = sequence_length

    @staticmethod
    def _loaded_model_is_valid(model) -> bool:
        return "count_model" in model and "project" in model and "token_sequences" in model and "saved_line_numbers" in model and "single_tokens" in model