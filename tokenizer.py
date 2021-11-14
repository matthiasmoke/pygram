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
        "function_defs": {},
        "class_defs": {},
        "module_code": []
    }

    def __init__(self, filepath):
        self._filepath = filepath
        self._syntax_tree = None
        self._module_name = ""

        self._syntax_tree = self._load_syntax_tree()
        self._ast_depth_search()


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
            module_tokens = []
            for node in tree.body:
                if isinstance(node, _ast.FunctionDef):
                    result = self._process_function_def(node)
                    self.token_dict["function_defs"][result[0]] = result[1]

                elif isinstance(node, _ast.ClassDef):
                    class_name = node.name
                    class_functions = {}
                    class_tokens = []

                    for child in node.body:
                        if isinstance(node, _ast.FunctionDef):
                            result = self._process_function_def(node)
                            class_functions[result[0]] = result[1]
                        else:
                            self._search_tokens(child, class_tokens)
                    
                    self.token_dict[class_name] = {
                        "functions_defs": class_functions,
                        "class_code": class_tokens
                    }

                else:
                    self._search_tokens(node, module_tokens)
                
            
            self.token_dict["module_code"] = module_tokens

    
    def _process_function_def(self, node):
        method_name = node.name
        tokens = self._search_node_body(node.body)
        return (method_name, tokens)


    def _search_node_body(self, node_body, tokens=None):
        if tokens is None:
            tokens = []

        for child in node_body:
            self._search_tokens(child, tokens)
        return tokens


    def _search_tokens(self, node, tokens):
        if isinstance(node, _ast.If):
            tokens.append(TOKEN_EXPRESSIONS["if"])
            self._search_node_body(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endIf"])

        elif isinstance(node, _ast.For):
            tokens.append(TOKEN_EXPRESSIONS["for"])
            self._search_node_body(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endFor"])

        elif isinstance(node, _ast.While):
            tokens.append(TOKEN_EXPRESSIONS["while"])
            self._search_node_body(node.body, tokens)
            tokens.append(TOKEN_EXPRESSIONS["endWhile"])

        elif isinstance(node, _ast.Return):
            tokens.append(TOKEN_EXPRESSIONS["return"])

        elif isinstance(node, _ast.Raise):
            tokens.append(TOKEN_EXPRESSIONS["raise"])

        elif isinstance(node, _ast.Try):
            tokens.append(TOKEN_EXPRESSIONS["try"])
            self._search_node_body(node.body, tokens)

        elif isinstance(node, _ast.ExceptHandler):
            tokens.append(TOKEN_EXPRESSIONS["except"])

        elif (isinstance(node, _ast.Assign) or isinstance(node, _ast.AugAssign)):
            if isinstance(node.value, _ast.Call):
                tokens.append(Tokenizer._process_call(node))

        elif isinstance(node, _ast.Expr):
            if isinstance(node.value, _ast.Call):
                tokens.append(Tokenizer._process_call(node))
  
    
    @staticmethod
    def _process_call(call_node):
        output = "<UNKNOWN>"
        try:
            func = call_node.value.func
            output = "<UNKNOWN>"
            if hasattr(func, "id"):
                output = func.id
            elif hasattr(func, "attr"):
                output = func.attr
        except AttributeError:
            return output
        
        return output



