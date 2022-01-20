
import json
from typing import Dict

class TokenCountModel():
    
    def __init__(self, token_sequences={}, name="", count_model={}, shortest_sequence_length=0, longest_sequence_length=0):
        self.token_sequences: Dict = token_sequences
        self.count_model: Dict = count_model
        self.name: str = name
        self.shortest_sequence_length: int = shortest_sequence_length
        self.longest_sequence_length: int = longest_sequence_length

    @staticmethod
    def load_from_file(path):
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
    

    def save_to_file(self, path):
        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "shortest_sequence_length": self.shortest_sequence_length,
            "longest_sequence_length": self.longest_sequence_length,
            "token_sequences": self.token_sequences,
            "count_model": self.count_model 
            }, outfile)

    
    def build(self):
        for value in self.token_sequences: 
            for sequence in self.token_sequences[value]:
                self._update_sequence_metrics(sequence)
                for (index, token) in enumerate(sequence):
                    # add initial token
                    self._count_token(token)
                    token_sub_sequence = token
                    for count in range(index + 1, len(sequence)):
                        token_sub_sequence += sequence[count]
                        self._count_token(token_sub_sequence)

    
    def _count_token(self, token_sub_sequence):
        if token_sub_sequence in self.count_model:
            self.count_model[token_sub_sequence] += 1
        else:
            self.count_model[token_sub_sequence] = 1
    
    def _update_sequence_metrics(self, sequence):
        sequence_length: int = len(sequence)

        if self.shortest_sequence_length == 0 or self.shortest_sequence_length > sequence_length:
            self.shortest_sequence_length = sequence_length
        
        if self.longest_sequence_length == 0 or self.longest_sequence_length < sequence_length:
            self.longest_sequence_length = sequence_length