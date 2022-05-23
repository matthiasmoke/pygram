import logging
import ast
import os
import _ast
from _ast import arg
from _ast import arguments
from _ast import AugAssign
from _ast import Call
from _ast import For
from _ast import AnnAssign
from _ast import Constant
from _ast import Attribute
from _ast import Name
from _ast import Subscript
from _ast import FunctionDef
from _ast import ClassDef
from _ast import AsyncFunctionDef

from typing import Tuple
from typing import List

from ..type_retrieval.preprocessed_type_caches import TypeCache
from ..type_retrieval.type_info import TypeInfo
from ..type_retrieval.variable_type_cache import VariableTypeCache
from ..utils import Utils
from .tokens import Tokens
from .tokenizer import Tokenizer

logger = logging.getLogger("main")

class TypeTokenizer(Tokenizer):

    def __init__(self, filepath, module_name, type_cache: TypeCache) -> None:
        super().__init__(filepath, module_name)
        self._type_cache: TypeCache = type_cache
        self._variable_cache: VariableTypeCache = VariableTypeCache(self.module_path)
        self._type_cache.set_current_module(self.module_path)
        self.number_of_type_inferred_call_tokens: int = 0
        self.number_of_call_tokens: int = 0
        self.number_of_ann_assigns: int = 0
        self.number_of_assigns: int = 0

    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read(), type_comments=True)
                return tree
        return None

    def _process_class_def(self, node: ClassDef, module_tokens: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        Creates sequences for every function definition inside a class definition. 
        Nodes which are not contained inside a function def are added to the module sequence.
        Changes the current variable cache scope to the currently processed class
        """
        class_tokens: List[Tuple[str, int]] = []
        # create cache for class and add self type
        self._variable_cache.set_class_scope(node.name)
        class_type: TypeInfo = TypeInfo(label=node.name)
        self._type_cache.populate_type_info_with_module(class_type)
        self._variable_cache.add_variable("self", class_type)

        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                result = self._process_function_def(child)
                class_tokens.append(result)
            elif isinstance(child, ClassDef):
                result = self._process_class_def(child, module_tokens)
                class_tokens += result
            else:
                self._classify_and_process_node(child, module_tokens)
        self._variable_cache.leave_class_scope()
        return class_tokens
    
    def _process_function_def(self, node) -> List[Tuple[str, int]]:
        tokens: List[str, int] = []
        self._variable_cache.set_function_scope(node.name)
        if isinstance(node, AsyncFunctionDef):
            self._add_token(tokens, Tokens.ASYNC.value, node)
        
        # save function arguments to variable cache
        self._process_arguments(node.args)
        self._add_token(tokens, Tokens.DEF.value, node)
        self._search_node_body(node.body, tokens)
        self._add_token(tokens, Tokens.END_DEF.value, node)
        self._variable_cache.leave_function_scope()
        return tokens
    
    def _process_call(self, node: Call, tokens: List[Tuple[str, int]]) -> None:
        
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token: str = "UNKNOWN"
        function_name: str = ""

        if isinstance(node.func, Name):
            function_name = node.func.id
            self._process_standalone_function(function_name, tokens, node)
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func
            if isinstance(attribute.value, Subscript) or isinstance(attribute.value, Name) or isinstance(attribute.value, Attribute):
                self._process_call_on_object(attribute, tokens)
            elif isinstance(attribute.value, Constant):
                function_name = attribute.attr
                token = self._construct_call_token(function_name)
                self._add_token(tokens, token, node)
            elif isinstance(attribute.value, Call):
                self._process_subsequent_call(attribute, tokens)
            else:
                logger.error("Unable to determine Attribute type on Call in module {}, line {}"
                .format(self.module_path, attribute.lineno))
        elif isinstance(node.func, Call):
            self._process_call(node.func, tokens)
        elif isinstance(node.func, Subscript):
            if hasattr(node.func.value, "id"):
                function_name = node.func.value.id
            elif hasattr(node.func.value, "attr"):
                function_name = node.func.value.attr
            self._process_standalone_function(function_name, tokens, node)
        else:
            logger.error("Unable to determine method name in module {} in line {}"
            .format(self.module_path, node.lineno))   
    
    def _process_standalone_function(self, function_name: str, tokens: List[Tuple[str, int]], node: Call) -> None:
        module: str = self._type_cache.find_module_for_function(function_name)
        token: str = self._construct_call_token(function_name, module=module)
        self._add_token(tokens, token, node)

    def _process_call_on_object(self, node: Attribute, tokens: List[Tuple[str, int]]) -> None: 
        """
        Processes a function call which happens on an object
        """
        function_name: str = node.attr
        subscript_depth: int = 0
        subscript_index: int = 0
        token: str = "UNKNOWN"
        if isinstance(node.value, Subscript):
            object_name, subscript_depth = self._get_origin_of_subscript(node.value, 0)
            subscript_index: int = self._get_index_of_subscript(node.value)
        elif isinstance(node.value, Name):
            object_name = node.value.id
        elif isinstance(node.value, Attribute):
            object_name = Utils.get_full_name_from_attribute_node(node.value)
        
        variable_type: TypeInfo = self._variable_cache.get_variable_type(object_name, subscript_depth, subscript_index)
        # if variable type is not found, check if the method is called on a class directly
        if variable_type is None:
            module: str = self._type_cache.find_module_for_type_with_function(object_name, function_name)
            token: str = self._construct_call_token(function_name, module=module, object_name=object_name)
            #TODO if module is not found, it means that the object, on which the function is called, 
            # belongs to an imported type which is not contained in the type cache.
        else:
            token: str = self._construct_call_token(function_name, type=variable_type)
        self._add_token(tokens, token, node)
    
    def _process_subsequent_call(self, node: Attribute, tokens: List[Tuple[str, int]]) -> None:
        """
        Processes a subsequent call, meaning a function call which happens on the return type of another function call
        """
        function_name: str = node.attr
        self._process_call(node.value, tokens)
        prev_function_name, prev_module =  self._retrieve_module_and_function_from_token(tokens[-1][0])
        return_type: TypeInfo = self._type_cache.get_return_type(prev_function_name, module=prev_module)
        token: str = self._construct_call_token(function_name, type=return_type)
        self._add_token(tokens, token, node)

    def _process_arguments(self, node: arguments) -> None:
            """
            Adds annotated function arguments to variable cache
            """
            for child in node.args:
                if isinstance(child, arg):
                    if child.annotation is not None:
                        info: TypeInfo = TypeInfo(child.annotation)
                        self._type_cache.populate_type_info_with_module(info)
                        name: str = child.arg
                        self._variable_cache.add_variable(name, info)
                else:
                    logger.error("Unknown argument node type in line {}".format(node.lineno))

    
    def _retrieve_module_and_function_from_token(self, token_string: str) -> Tuple[str, str]:
        """
        Returns a tuple which contains (function name, module)
        """
        token_parts: List[str] = token_string.split(".")
        # split function name from module and remove brackets in the end
        function_name: str = token_parts[-1][0:-2]
        module_path: str = None

        if len(token_parts) > 1:
            module_path = token_string[0:len(token_string) - len(function_name) - 3]

        return (function_name, module_path)

    def _construct_call_token(self, function_name: str, module: str = None, object_name: str = None, type: TypeInfo = None) -> str:
        """
        Builds the call token out of the function name, and either the module and optionally the object name or just the type information
        """
        token: str = "{}()".format(function_name)
        type_inferred: bool = False

        if module is not None and module != "":
            if object_name is not None and object_name != "":
                module = "{}.{}".format(module, object_name)
            token = "{}.{}".format(module, token)
            type_inferred = True
        # elif module is None and object_name is not None:
        #     token = "{}.{}".format(str(object_name), token)
        elif type is not None:
            type_inferred = True
            token = "{}.{}".format(str(type), token)

        self.number_of_call_tokens += 1
        if type_inferred:
            self.number_of_type_inferred_call_tokens += 1

        return token
    
    def _get_origin_of_subscript(self, node: Subscript, depth: int) -> Tuple[str, int]:
        """
        Returns the name of the List/Dict/Tuple/etc that contains the object on which the method call happens.
        Additionally, it returns how deep the subscript tree goes
        """
        value = node.value
        origin_name: str = ""
        depth += 1
        if isinstance(value, Subscript):
            origin_name, depth = self._get_origin_of_subscript(value, depth)
        elif isinstance(value, Name):
            origin_name = value.id
        elif isinstance(value, Attribute):
            origin_name = Utils.get_full_name_from_attribute_node(value)
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
            
    
    def _process_for_block(self, node: For, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.FOR.value, node)

        if isinstance(node.iter, Name) or isinstance(node.iter, Subscript) or isinstance(node.iter, Attribute):
            self._cache_variables_in_for_block(node)
        elif isinstance(node.iter, Call):
            self._process_call(node.iter, tokens)
        else:
            logger.error("Error, unknown iter type of For node in module {}".format(self.module_path))
        
        self._search_node_body(node.body, tokens)
        if len(node.orelse):
            self._add_token(tokens, Tokens.ELSE.value, node)
            self._search_node_body(node.orelse, tokens)
        self._add_token(tokens, Tokens.END_FOR.value, node)
    
    def _cache_variables_in_for_block(self, node: For) -> None:
        """
        Caches variables and their respective types which are used in a for block
        """
        for_target_names: List[str] = []
        if isinstance(node.target, Name):
            for_target_names.append(node.target.id)
        elif isinstance(node.target, Attribute):
            for_target_names.append(Utils.get_full_name_from_attribute_node(node.target))
        elif isinstance(node.target, _ast.Tuple):
            Utils.get_names_from_tuple(node.target, for_target_names)
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
        variable_name: str = ""
        if isinstance(node, Name):
            variable_name = node.id
        elif isinstance(node, Attribute):
            variable_name = Utils.get_full_name_from_attribute_node(node)
        else:
            variable_name = "UNKNOWN"
            logger.error("Error, could not retrieve variable name for Ann/Assign node in {}"
            .format(self.module_path))
        return variable_name

    def _process_assign(self, node: _ast.Assign, tokens: List[Tuple[str, int]]):
        if hasattr(node, "target"):
            variable_name: str = self._get_variable_name_for_assignment(node.target)
        elif hasattr(node, "targets"):
            variable_name: str = self._get_variable_name_for_assignment(node.targets[0])

        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)
            logger.warning("Un-annotated assignment for a variable in module {}"
            .format(variable_name, self.module_path))
        elif isinstance(node.value, Constant):
            logger.warning("Un-annotated assignment for variable [{}] with constant value in module {}, lineno: {}"
            .format(variable_name, self.module_path, node.lineno))

        if not isinstance(node, AugAssign):
            self.number_of_assigns += 1


    def _process_ann_assign(self, node: AnnAssign, tokens: List[Tuple[str, int]]):
        try:
            complete_name: str = self._get_variable_name_for_assignment(node.target)
            info: TypeInfo = TypeInfo(annotation_node=node.annotation)
            self._type_cache.populate_type_info_with_module(info)
            self._classify_and_process_node(node.value, tokens)
            self._variable_cache.add_variable(complete_name, info)

        except AttributeError:
            logger.error("Failed processing AnnAssign in module {}".format(self.module_path))
        finally:
            self.number_of_assigns += 1
            self.number_of_ann_assigns += 1
