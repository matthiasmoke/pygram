
import json
from typing import Dict

class TokenCountModel():
    
    def __init__(self, token_sequences={}, name="", count_model={}):
        self.token_sequences: Dict = token_sequences
        self.count_model: Dict = count_model
        self.name: str = name

    @staticmethod
    def load_from_file(path):
        with open(path, 'r') as inputfile:
            model = json.load(inputfile)
            if model is not None:
                if "count_model" in model and "project" in model and "token_sequences" in model:
                    return TokenCountModel(token_sequences=model["token_sequences"], name=model["project"], count_model=model["count_model"])
        return None
    

    def save_to_file(self, path):
        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "token_sequences": self.token_sequences,
            "count_model": self.count_model 
        }, outfile, sort_keys=True)

    def count_tokens(self):
        self._create_tokencount_model()
    
    def build(self):
        for value in self.token_sequences: 
            for sequence in self.token_sequences[value]:
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