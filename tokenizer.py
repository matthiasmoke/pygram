import ast
import _ast
import os

TOKEN_EXPRESSIONS = {
    "if": "<IF>",
    "endIf": "<ENDIF>",
    "for": "<FOR>",
    "endFor": "<ENDFOR>",
    "while": "<WHILE>",
    "endWhile": "<ENDWHILE>",
    "return": "<RETURN>",
    "raise": "<RAISE>",
    "try": "<TRY>",
    "except": "<EXCEPT>"
}

class Tokenizer:

    token_dict = {
        "function_def": {},
        "class_def": {},
        "module_code": {}
    }

    def __init__(self, filepath):
        self._filepath = filepath
        self._syntax_tree = None
        self._module_name = ""


    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                tree = ast.parse(source.read())
                return tree
        return None
    

    def _ast_depth_search(self):
        tree = self._syntax_tree
        if tree is None:
            return
        
        if tree.body is not None:
            for node in tree.body:
                pass
    

    def _search_tokens(self, node, tokens):
        if isinstance(node, _ast.If):
            tokens.append(TOKEN_EXPRESSIONS["if"])
            self._search_tokens(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endIf"])
        elif isinstance(node, _ast.For):
            tokens.append(TOKEN_EXPRESSIONS["for"])
            self._search_tokens(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endFor"])
        elif isinstance(node, _ast.While):
            tokens.append(TOKEN_EXPRESSIONS["while"])
            self._search_tokens(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endWhile"])
        elif isinstance(node, _ast.Return):
            tokens.append(TOKEN_EXPRESSIONS["return"])
        elif isinstance(node, _ast.Raise):
            tokens.append(TOKEN_EXPRESSIONS["raise"])
        elif isinstance(node, _ast.Try):
            tokens.append(TOKEN_EXPRESSIONS["try"])
        elif isinstance(node, _ast.ExceptHandler):
            tokens.append(TOKEN_EXPRESSIONS["except"])
        elif isinstance(node, _ast.Assign) or isinstance(node, _ast.AugAssign):
            if isinstance(node.value, _ast.Call):
                tokens.append(self._extract_method_name(node.value))
        elif isinstance(node, _ast.expr):
            if isinstance(node.value, _ast.Call):
                tokens.append(self._extract_method_name(node.value))
        
    
    def _extract_method_name(call_node):
        return call_node.value.func.id
    
