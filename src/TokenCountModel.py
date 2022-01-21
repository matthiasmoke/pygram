
import json
from typing import Dict, List

class TokenCountModel():
    
    def __init__(self, token_sequences={}, name="", count_model={}, shortest_sequence_length=0, longest_sequence_length=0, number_single_tokens=0):
        self.token_sequences: Dict = token_sequences
        self.count_model: Dict = count_model
        self.name: str = name
        self.shortest_sequence_length: int = shortest_sequence_length
        self.longest_sequence_length: int = longest_sequence_length
        self.number_single_tokens: int = number_single_tokens

    @staticmethod
    def load_from_file(path) -> "TokenCountModel":
        with open(path, 'r') as inputfile:
            model = json.load(inputfile)
            if model is not None:
                if "count_model" in model and "project" in model and "token_sequences" in model:
                    return TokenCountModel(
                        token_sequences=model["token_sequences"],
                        name=model["project"],
                        count_model=model["count_model"],
                        shortest_sequence_length=model["shortest_sequence_length"],
                        longest_sequence_length=model["longest_sequence_length"]
                        )
        return None
    

    def save_to_file(self, path) -> None:
        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "shortest_sequence_length": self.shortest_sequence_length,
            "longest_sequence_length": self.longest_sequence_length,
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
                for (index, token) in enumerate(sequence):
                    # add initial token
                    self._count_token(token)
                    token_sub_sequence = token
                    # build subsequences of the whole sequence
                    for count in range(index + 1, len(sequence)):
                        token_sub_sequence += sequence[count]
                        self._count_token(token_sub_sequence)
    

    def get_sequence_list_without_module_info(self) -> List:
        output: List = []

        for value in self.token_sequences:
            output += self.token_sequences[value]

        return output

    def get_sequence_dict(self) -> Dict:
        return self.token_sequences
    
    def get_token_count(self, token) -> int:
        """
        Get the count of a token or subsequence
        """
        return self.count_model[token]
    
    def get_number_single_tokens(self):
        return self.number_single_tokens

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
        
        self.number_single_tokens += 1
    
    def _update_sequence_metrics(self, sequence) -> None:
        sequence_length: int = len(sequence)

        if self.shortest_sequence_length == 0 or self.shortest_sequence_length > sequence_length:
            self.shortest_sequence_length = sequence_length
        
        if self.longest_sequence_length == 0 or self.longest_sequence_length < sequence_length:
            self.longest_sequence_length = sequence_length