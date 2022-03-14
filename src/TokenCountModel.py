
import json
from typing import Dict, List, Tuple

class TokenCountModel():
    
    def __init__(self, token_sequences={}, name="", count_model={}, shortest_sequence_length=0, longest_sequence_length=0, number_single_tokens=0):
        self.token_sequences: Dict = token_sequences
        self.count_model: Dict = count_model
        self.name: str = name
        self.shortest_sequence_length: int = shortest_sequence_length
        self.longest_sequence_length: int = longest_sequence_length
        self.number_of_single_tokens: int = number_single_tokens

    @staticmethod
    def load_from_file(path) -> "TokenCountModel":
        with open(path, 'r') as inputfile:
            model = json.load(inputfile)
            if model is not None:
                if "count_model" in model and "project" in model and "token_sequences" in model:
                    token_sequences: Dict = model["token_sequences"]
                    converted_token_sequences: Dict[List[Tuple[str, int]]] = {}

                    for key, sequences in token_sequences.items():
                        converted_token_sequences[key] = []
                        for sequence in sequences:
                            converted_sequence: List[str, int] = []
                            for token in sequence:
                                converted_sequence.append((token[0], token[1]))
                            converted_token_sequences[key].append(converted_sequence)


                    return TokenCountModel(
                        token_sequences=converted_token_sequences,
                        name=model["project"],
                        count_model=model["count_model"],
                        shortest_sequence_length=model["shortest_sequence_length"],
                        longest_sequence_length=model["longest_sequence_length"],
                        number_single_tokens=model["number_single_tokens"]
                        )
        return None
    

    def save_to_file(self, path) -> None:
        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "shortest_sequence_length": self.shortest_sequence_length,
            "longest_sequence_length": self.longest_sequence_length,
            "number_single_tokens": self.number_of_single_tokens,
            "token_sequences": self.token_sequences,
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
    

    def get_sequence_list_without_meta_data(self) -> List:
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

    def get_sequence_dict(self) -> Dict:
        return self.token_sequences
    
    def get_token_count(self, token) -> int:
        """
        Get the count of a token or subsequence
        """
        return self.count_model[token]
    
    def get_number_of_single_tokens(self):
        return self.number_of_single_tokens

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
        
        self.number_of_single_tokens += 1
    
    def _update_sequence_metrics(self, sequence) -> None:
        sequence_length: int = len(sequence)

        if self.shortest_sequence_length == 0 or self.shortest_sequence_length > sequence_length:
            self.shortest_sequence_length = sequence_length
        
        if self.longest_sequence_length == 0 or self.longest_sequence_length < sequence_length:
            self.longest_sequence_length = sequence_length