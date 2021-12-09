import ast
import _ast
import os

from tokens import Tokens

class Tokenizer:

    def __init__(self, filepath, consider_type=False):
        self._filepath = filepath
        self._syntax_tree = None
        self._module_name = ""
        self.token_dict = {
            "function_defs": {},
            "class_defs": {},
            "module_code": []
        }
        self.variable_type_dict = {

        }

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
                if isinstance(node, _ast.FunctionDef) or isinstance(node, _ast.AsyncFunctionDef):
                    result = self._process_function_def(node)
                    self.token_dict["function_defs"][result[0]] = result[1]

                elif isinstance(node, _ast.ClassDef):
                    class_name = node.name
                    class_functions = {}
                    class_tokens = []

                    for child in node.body:
                        if isinstance(node, _ast.FunctionDef) or isinstance(node, _ast.AsyncFunctionDef):
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
        tokens = []
        method_name = node.name

        if isinstance(node, _ast.AsyncFunctionDef):
            tokens.append(Tokens.ASYNC.value)
        
        tokens.append(Tokens.DEF.value)
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_DEF.value)
        return (method_name, tokens)


    def _search_node_body(self, node_body, tokens=None):
        if tokens is None:
            tokens = []

        for child in node_body:
            self._search_tokens(child, tokens)
        return tokens


    def _search_tokens(self, node, tokens):
        if isinstance(node, _ast.If):
            self._process_if_block(node, tokens)

        elif isinstance(node, _ast.For):
            tokens.append(Tokens.FOR.value)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.END_FOR.value)

        elif isinstance(node, _ast.While):
            tokens.append(Tokens.WHILE.value)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.END_WHILE.value)

        elif isinstance(node, _ast.Return):
            tokens.append(Tokens.RETURN.value)

        elif isinstance(node, _ast.Raise):
            tokens.append(Tokens.RAISE.value)
            if isinstance(node.exc, _ast.Call):
                self._process_call(node.exc, tokens)

        elif isinstance(node, _ast.Try):
            self._process_try_block(node, tokens)

        elif (isinstance(node, _ast.With)):
            self._process_with_block(node, tokens)

        elif isinstance(node, _ast.Assert):
            tokens.append(Tokens.ASSERT.value)
            if node.test and isinstance(node.test, _ast.Call):
                self._process_call(node.test, tokens)

        elif isinstance(node, _ast.Break):
            tokens.append(Tokens.BREAK.value)

        elif isinstance(node, _ast.Pass):
            tokens.append(Tokens.PASS.value)

        elif (isinstance(node, _ast.Assign) or isinstance(node, _ast.AugAssign)):
            if isinstance(node.value, _ast.Call):
                self._process_call(node.value, tokens)
        
        elif isinstance(node, _ast.AnnAssign):
            self._retrieve_type_information(node)
            if isinstance(node.value, _ast.Call):
                self._process_call(node.value, tokens)

        elif isinstance(node, _ast.Expr):
            if isinstance(node.value, _ast.Call):
                self._process_call(node.value, tokens)
            elif isinstance(node.value, _ast.Await):
                tokens.append(Tokens.AWAIT.value)
                if isinstance(node.value.value, _ast.Call):
                    self._process_call(node.value.value, tokens)

  

    def _process_try_block(self, try_node: _ast.Try, tokens):
        tokens.append(Tokens.TRY.value)
        self._search_node_body(try_node.body, tokens)

        for handler in try_node.handlers:
            tokens.append(Tokens.EXCEPT.value)
            if handler.type is not None:
                if hasattr(handler.type, "id"):
                    tokens.append(handler.type.id + "()")
                elif hasattr(handler.type, "attr"):
                    tokens.append(handler.type.attr + "()")
            self._search_node_body(handler.body, tokens)
            tokens.append(Tokens.END_EXCEPT.value)
        
        if len(try_node.finalbody):
            tokens.append(Tokens.FINALLY.value)
            self._search_node_body(try_node.finalbody, tokens)
            tokens.append(Tokens.END_FINALLY.value)
    
    def _process_if_block(self, if_node: _ast.If, tokens):
            tokens.append(Tokens.IF.value)
            if if_node.test and isinstance(if_node.test, _ast.Call):
                self._process_call(if_node.test, tokens)

            self._search_node_body(if_node.body, tokens)

            if if_node.orelse:
                tokens.append(Tokens.ELSE.value)
                self._search_node_body(if_node.orelse, tokens)
            tokens.append(Tokens.END_IF.value)
    
    def _process_with_block(self, with_node: _ast.With, tokens):
            tokens.append(Tokens.WITH.value)
            if len(with_node.items):
                for item in with_node.items:
                    if isinstance(item, _ast.withitem) and isinstance(item.context_expr, _ast.Call):
                        self._process_call(item.context_expr, tokens)
            self._search_node_body(with_node.body, tokens)
            tokens.append(Tokens.END_WITH.value)
    
    def _process_call(self, call_node: _ast.Call, tokens):
        token = "<UNKNOWN>"
        type_info = ""
        try:
            func = call_node.func
            arguments = call_node.args

            if len(arguments):
                for argument in arguments:
                    if isinstance(argument, _ast.Call):
                        self._process_call(argument, tokens)

            if hasattr(func, "value") and isinstance(func.value, _ast.Call):
                self._process_call(func.value, tokens)

            if hasattr(func, "id"):
                token = func.id +"()"
            elif hasattr(func, "attr"):
                token = func.attr + "()"
                if hasattr(func, "value") and hasattr(func.value, "id"):
                    variable_instance = func.value.id
                    type_info = self.variable_type_dict.get(variable_instance, None)
                    if type_info is not None:
                        token = type_info + "." + token
            
        except AttributeError:
            print("Unknown attribute")
        finally:
            tokens.append(token)

    def _retrieve_type_information(self, assign_node: _ast.AnnAssign):
        if assign_node is not None:
            target_variable = assign_node.target.id
            type = assign_node.annotation.id
            self.variable_type_dict[target_variable] = type


