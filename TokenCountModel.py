
import json
from os import name
from typing import Dict, List

class TokenCountModel():
    
    def __init__(self, gram_size=3, tokenstream=[], name=""):
        self.tokenstream: List = tokenstream
        self.count_dict: Dict = {}
        self.gram_size: int = gram_size
        self.name = name

        self.model = {
            "project": self.name,
            "tokenstream": self.tokenstream,
            "count_model": self.count_dict 
        }

    def load_from_file(path):
        with open(path, 'r') as inputfile:
            model = json.loads(inputfile)


    def save_to_file(self, path):
        with open(path, 'w') as outfile:
            json.dump(self.model, outfile, sort_keys=True)