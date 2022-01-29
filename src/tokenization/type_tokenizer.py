import logging
import ast
import _ast
import os
from tokenizer import Tokenizer

logger = logging.getLogger("main")

class TypeTokenizer(Tokenizer):

    def __init__(self, filepath) -> None:
        super().__init__(filepath)
    
    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read(), type_comments=True)
                return tree
        return None