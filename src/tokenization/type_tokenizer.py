import logging
import ast
import os
from _ast import arg, arguments ,Constant, Call, For, AnnAssign, Constant, Attribute, Name, Subscript, FunctionDef, ClassDef, AsyncFunctionDef
import _ast
from typing import List, Tuple

from ..type_retrieval.import_cache import ImportCache

from ..type_retrieval.preprocessed_type_caches import TypeCache
from .tokenizer import Tokenizer
from ..type_retrieval.type_info import TypeInfo
from ..type_retrieval.variable_type_cache import VariableTypeCache
from .tokens import Tokens

logger = logging.getLogger("main")

class TypeTokenizer(Tokenizer):

    def __init__(self, filepath, module_name, type_cache: TypeCache) -> None:
        super().__init__(filepath, module_name)
        self._type_cache: TypeCache = type_cache
        self._import_cache = ImportCache(self.module_path, type_cache.module_list)
        self._variable_cache: VariableTypeCache = VariableTypeCache(self.module_path, type_cache)
        self._type_cache.set_current_import_cache(self._import_cache)
    
    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read(), type_comments=True)
                return tree
        return None
    
    def _process_import(self, node):
        self._import_cache.add_import(node)

    def _process_class_def(self, node: ClassDef) -> List[str]:
        class_tokens = []
        self._variable_cache.set_class_scope(node.name)
        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                result = self._process_function_def(child)
                class_tokens.append(result)
            elif isinstance(child, ClassDef):
                result = self._process_class_def(child)
                class_tokens += result
            else:
                self._classify_and_process_node(child, class_tokens)
        self._variable_cache.leave_class_scope()
        return class_tokens
    
    def _process_function_def(self, node) -> List[str]:
        tokens = []
        self._variable_cache.set_function_scope(node.name)
        if isinstance(node, AsyncFunctionDef):
            tokens.append(Tokens.ASYNC.value)
        
        # save function arguments to variable cache
        self._process_arguments(node.args)
        tokens.append(Tokens.DEF.value)
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_DEF.value)
        self._variable_cache.leave_function_scope()
        return tokens
    
    def _process_call(self, node: Call, tokens: List[str]) -> None:
        
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token: str = "UNKNOWN"
        function_name: str = ""

        if isinstance(node.func, Name):
            function_name = node.func.id
            module: str = self._type_cache.find_module_for_function(function_name)
            token = self._construct_call_token(function_name, module=module)
            tokens.append(token)
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func
            if isinstance(attribute.value, Subscript) or isinstance(attribute.value, Name) or isinstance(attribute.value, Attribute):
                self._process_call_on_object(attribute, tokens)
            elif isinstance(attribute.value, Constant):
                function_name = attribute.attr
                token = self._construct_call_token(function_name)
                tokens.append(token)
            elif isinstance(attribute.value, Call):
                self._process_subsequent_call(attribute, tokens)
            else:
                logger.error("Unable to determine Attribute type on Call in module {}, line {}"
                .format(self.module_path, attribute.lineno))
        else:
            logger.error("Unable to determine method name in module {} in line {}"
            .format(self.module_path, node.lineno))   
    
    def _get_path_from_attribute(self, node: Attribute) -> str:
        """
        Constructs the complete variable or function path from an attribute node.
        Is used for nested calls, e.g. for cases like os.path.abspath or self.SomeInnerClass
        """
        name: str = node.attr
        prefix: str = ""
        if isinstance(node.value, Name):
            prefix = node.value.id
        elif isinstance(node.value, Attribute):
            prefix = self._get_path_from_attribute(node.value)
        
        if prefix == "":
            return name
        else:
            return "{}.{}".format(prefix, name)

    def _process_call_on_object(self, node: Attribute, tokens: List[str]) -> None: 
        """
        Processes a function call which happens on an object
        """
        function_name: str = node.attr
        subscript_depth: int = 0
        subscript_index: int = 0
        token: str = "UNKNOWN"
        if isinstance(node.value, Subscript):
            object_name, subscript_depth = self._get_origin_of_subscript(node.value, 0)
            subscript_index = self._get_index_of_subscript(node.value)
        elif isinstance(node.value, Name):
            object_name = node.value.id
        elif isinstance(node.value, Attribute):
            object_name = self._get_path_from_attribute(node.value)
        
        variable_type: TypeInfo = self._variable_cache.get_variable_type(object_name, subscript_depth, subscript_index)
        # if variable type is not found, check if the method is called on a class directly
        if variable_type is None:
            module: str = self._type_cache.find_module_for_type_with_function(object_name, function_name)
            token = self._construct_call_token(function_name, module=module, object_name=object_name)
            #TODO if module is not found, it means that the object, on which the function is called, 
            # belongs to an imported type which is not contained in the type cache. Find out where it comes from
        else:
            token = self._construct_call_token(function_name, type=variable_type)
        tokens.append(token)
    
    def _process_subsequent_call(self, node: Attribute, tokens: List[str]) -> None:
        """
        Processes a subsequent call, meaning a function call which happens on the return type of another function call
        """
        function_name: str = node.attr
        self._process_call(node.value, tokens)
        prev_function_name, prev_module =  self._retrieve_module_and_function_name_from_token(tokens[-1])
        return_type: TypeInfo = self._type_cache.get_return_type(prev_function_name, module=prev_module)
        tokens.append(self._construct_call_token(function_name, type=return_type))
    
    def _retrieve_module_and_function_name_from_token(self, token: str) -> Tuple[str, str]:
        """
        Returns a tuple which contains (function name, module)
        """
        token_parts: List[str] = token.split(".")
        # split function name from module and remove brackets in the end
        function_name: str = token_parts[-1][0:-2]
        module_path: str = None

        if len(token_parts) > 1:
            module_path = token[0:len(token) - len(function_name) - 3]

        return (function_name, module_path)

    def _construct_call_token(self, function_name: str, module: str = None, object_name: str = None, type: TypeInfo = None) -> str:
        """
        Builds the call token out of the function name, and either the module and optionally the object name or just the type information
        """
        token: str = "{}()".format(function_name)

        if module is not None and module != "":
            if object_name is not None and object_name != "":
                module = "{}.{}".format(module, object_name)
            token = "{}.{}".format(module, token) 
        # elif module is None and object_name is not None:
        #     token = "{}.{}".format(str(object_name), token)
        elif type is not None:
            token = "{}.{}".format(str(type), token)
        return token
    
    def _get_origin_of_subscript(self, node: Subscript, depth: int) -> Tuple[str, int]:
        """
        Returns the name of the List/Dict/Tuple/etc which contains the object on which the method call happens
        """
        value = node.value
        origin_name = ""
        depth += 1
        if isinstance(value, Subscript):
            origin_name, depth = self._get_origin_of_subscript(value, depth)
        elif isinstance(value, Name):
            origin_name = value.id
        elif isinstance(value, Attribute):
            origin_name = self._get_path_from_attribute(value)
        else:
            logger.error("Unable to determine origin name of Subscript in module {}"
            .format(self.module_path))
        return origin_name, depth
    
    def _get_index_of_subscript(self, node: Subscript) -> int:
        """
        Returns the index of the Dict / Tuple object on which the method call happens
        """
        index = None
        try:
            if isinstance(node.slice, Constant):
                index_str = node.slice.value
                index = int(index_str)
        except ValueError:
            return 1
        except AttributeError:
            return 1
        except TypeError:
            return 1
        return index
            
    
    def _process_for_block(self, node: For, tokens: List[str]):
        tokens.append(Tokens.FOR.value)

        if isinstance(node.iter, Name) or isinstance(node.iter, Subscript) or isinstance(node.iter, Attribute):
            self._cache_variables_in_for_block(node)
        elif isinstance(node.iter, Call):
            self._process_call(node.iter, tokens)
        else:
            logger.error("Error, unknown iter type of For node in module {}".format(self.module_path))
        
        self._search_node_body(node.body, tokens)
        if len(node.orelse):
            tokens.append(Tokens.ELSE.value)
            self._search_node_body(node.orelse, tokens)
        tokens.append(Tokens.END_FOR.value)
    
    def _cache_variables_in_for_block(self, node: For):
        """
        Caches variables and their respective types which are used in a for block
        """
        for_target_names: List[str] = []
        if isinstance(node.target, Name):
            for_target_names.append(node.target.id)
        elif isinstance(node.target, Attribute):
            for_target_names.append(Utils.get_full_name_from_attribute_node(node.target))
        elif isinstance(node.target, _ast.Tuple):
            for child in node.target.elts:
                for_target_names.append(child.id)
        else:
            logger.warning("Unprocessable For loop target in line {}".format(node.lineno))

        target_index: int = 0
        for target_name in for_target_names:
            iter_name: str = ""
            # depth is one, as the type on depth 0 is the type that contains the iterated objects (e.g. List)
            subscript_depth: int = 1
            subscript_index: int = 0
            if isinstance(node.iter, Name):
                iter_name = node.iter.id
                subscript_index = target_index
                target_index += 1
            elif isinstance(node.iter, Subscript):
                iter_name, subscript_depth = self._get_origin_of_subscript(node.iter, subscript_depth)
                subscript_index = self._get_index_of_subscript(node.iter)
            
            variable_type: TypeInfo = self._variable_cache.get_variable_type(iter_name, subscript_depth, subscript_index)
            self._variable_cache.add_variable(target_name, variable_type)

    def _get_variable_name_for_assignment(self, node) -> str:
        target_variable: str = ""

        if isinstance(node, AnnAssign) or isinstance(node, ast.Assign):
            variable_is_class_field: bool = False
            if hasattr(node, "target"): 
                if hasattr(node.target, "id"):
                    target_variable = node.target.id
                    if target_variable == "self":
                        variable_is_class_field = True

                elif hasattr(node.target, "attr"):
                    if variable_is_class_field:
                        target_variable += ".{}".format(node.target.attr)
                    else:
                        logger.debug("Assign node with attr that is not part of class variable assignment in module {}"
                        .format(self.module_path))
                        target_variable = node.target.attr
                else:
                    target_variable = "UNKNOWN"
                    logger.error("Error, could not retrieve variable name for Ann/Assign node in {}"
                    .format(self.module_path))
            else: 
                target_variable = "List Object"
        return target_variable

    def _process_assign(self, node, tokens: List[str]):
        variable_name: str = self._get_variable_name_for_assignment(node)
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)
            logger.warning("Un-annotated assignment for a variable in module {}"
            .format(variable_name, self.module_path))
        elif isinstance(node.value, Constant):
            logger.warning("Un-annotated assignment for variable [{}] with constant value in module {}"
            .format(variable_name, self.module_path))


    def _process_ann_assign(self, node: AnnAssign, tokens: List[str]):
        try:
            info: TypeInfo = TypeInfo(annotation_node=node.annotation)
            self._type_cache.populate_type_info_with_module(info)
            complete_name: str = ""

            if isinstance(node.target, Attribute):
                prefix = node.target.value.id
                name = node.target.attr
                complete_name = "{}.{}".format(prefix, name)
            elif isinstance(node.target, Name):
                complete_name = node.target.id
            else:
                logger.error("Could not retrieve variable name from AnnAssign")
            
            self._classify_and_process_node(node.value, tokens)
            self._variable_cache.add_variable(complete_name, info)

        except AttributeError:
            logger.error("Failed processing AnnAssign in module {}".format(self.module_path))
    
    def _process_arguments(self, node: arguments) -> None:
        for child in node.args:
            if isinstance(child, arg):
                if child.annotation is not None:
                    info: TypeInfo = TypeInfo(child.annotation)
                    self._type_cache.populate_type_info_with_module(info)
                    name: str = child.arg
                    self._variable_cache.add_variable(name, info)
            else:
                logger.error("Unknown argument node type in line {}".format(node.lineno))
