import ast
import _ast
import os

from tokens import Tokens

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
    
    def __str__(self):
        output = str(self._filepath) + "\n\n"
        functions_defs = self.token_dict["function_defs"]
        class_defs = self.token_dict["class_defs"]
        module_code = self.token_dict["module_code"]


        if bool(functions_defs):
            output += "[function definitions]\n"

            for key, tokens in functions_defs.items():
                output += "\t{}()\n".format(key)
                for token in tokens:
                    output += "\t\t{}\n".format(token)


        if bool(class_defs):
            output += "[class definitions]\n"
            for key, value in class_defs.items():
                output += "\t{}\n".format(key)
                class_functions = value["function_defs"]
                class_code = value["class_code"]

                if bool(class_functions):
                    output += "\t\t[function definitions]\n"

                    for key, tokens in functions_defs.items():
                        output += "\t\t\t{}()\n".format(key)
                        for token in tokens:
                            output += "\t\t\t\t{}\n".format(token)
                
                if len(class_code):
                    output += "\tclass code:\n"
                    for token in class_code:
                        output += "\t\t{}\n".format(token)
        
        if len(module_code):
            output += "[module code]\n"
            for token in module_code:
                output += "\t{}\n".format(token)
        
        return output
        

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
                        "function_defs": class_functions,
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
            tokens.append(Tokens.IF.value)
            self._search_node_body(node.body, tokens)

            if node.orelse:
                tokens.append(Tokens.ELSE.value)
                self._search_node_body(node.orelse, tokens)

            tokens.append(Tokens.ENDIF.value)

        elif isinstance(node, _ast.For):
            tokens.append(Tokens.FOR.value)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.ENDFOR.value)

        elif isinstance(node, _ast.While):
            tokens.append(Tokens.WHILE.value)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.ENDWHILE.value)

        elif isinstance(node, _ast.Return):
            tokens.append(Tokens.RETURN.value)

        elif isinstance(node, _ast.Raise):
            tokens.append(Tokens.RAISE.value)

        elif isinstance(node, _ast.Try):
            tokens.append(Tokens.TRY.value)
            self._search_node_body(node.body, tokens)

        elif isinstance(node, _ast.ExceptHandler):
            tokens.append(Tokens.EXCEPT.value)

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



