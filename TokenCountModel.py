
import json
from os import name
from typing import Dict, List

class TokenCountModel():
    
    def __init__(self, gram_size=3, tokenstream=[], name="", count_model={}):
        self.tokenstream: List = tokenstream
        self.count_model: Dict = count_model
        self.gram_size: int = gram_size
        self.name = name

    @staticmethod
    def load_from_file(path):
        with open(path, 'r') as inputfile:
            model = json.load(inputfile)
            if model is not None:
                if "count_model" in model and "project" in model and "tokenstream" in model:
                    return TokenCountModel(tokenstream=model["tokenstream"], name=model["project"], count_model=model["count_model"])
        return None
    

    def save_to_file(self, path):
        with open(path, 'w') as outfile:
            json.dump({
            "project": self.name,
            "tokenstream": self.tokenstream,
            "count_model": self.count_dict 
        }, outfile, sort_keys=True)

    def count_tokens(self):
        self._create_tokencount_model()
    
    def _create_tokencount_model(self):
        for sequence in self.tokenstream:
            for (index, token) in enumerate(sequence):
                # add initial token
                self._count_token(token)
                token_sub_sequence = token
                for count in range(index + 1, len(sequence)):
                    token_sub_sequence += sequence[count]
                    self._count_token(token_sub_sequence)

    
    def _count_token(self, token_sub_sequence):
        if token_sub_sequence in self.count_dict:
            self.count_dict[token_sub_sequence] += 1
        else:
            self.count_dict[token_sub_sequence] = 1