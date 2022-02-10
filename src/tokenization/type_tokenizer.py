import logging
import ast
import os
from _ast import Call, For, AnnAssign, Constant, Attribute, Name, Subscript, FunctionDef, ClassDef, AsyncFunctionDef, Index
from typing import List, Tuple
from .tokenizer import Tokenizer
from .type_info import TypeInfo
from .variable_type_cache import VariableTypeCache
from .tokens import Tokens

logger = logging.getLogger("main")

class TypeTokenizer(Tokenizer):

    def __init__(self, filepath) -> None:
        super().__init__(filepath)
        self.variable_cache: VariableTypeCache = VariableTypeCache(filepath) 
    
    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read(), type_comments=True)
                return tree
        return None
    
    def _process_class_def(self, node: ClassDef) -> List[str]:
        class_tokens = []
        self.variable_cache.set_class_scope(node.name)
        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                self.variable_cache.set_class_function_scope(child.name)
                result = self._process_function_def(child)
                class_tokens.append(result)
                self.variable_cache.leave_class_function_scope()
            else:
                self._classify_and_process_node(child, class_tokens)
        self.variable_cache.leave_class_scope()
        return class_tokens
    
    def _process_function_def(self, node) -> List[str]:
        tokens = []
        self.variable_cache.set_function_scope(node.name)
        if isinstance(node, AsyncFunctionDef):
            tokens.append(Tokens.ASYNC.value)
        
        tokens.append(Tokens.DEF.value)
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_DEF.value)
        self.variable_cache.leave_function_scope()
        return tokens
    
    def _process_call(self, node: Call, tokens):
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token = "UNKNOWN"
        if (isinstance(node.func, Name)):
            method_name = node.func.id
            token = self._construct_call_token(method_name, None)
            # TODO get origin of function for fully classified name
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func

            if isinstance(attribute.value, Subscript) or isinstance(attribute.value, Name):
                token = self._process_call_on_object(attribute)

            elif isinstance(attribute.value, Call):
                self._process_call(attribute.value, tokens)
                token = self._construct_call_token(attribute.attr, None)
                # TODO get return type of previous method
            else:
                logger.error("Unable to determine Attribute type on Call in module {}"
                .format(self._filepath))
            # TODO get type of object
        else:
            logger.error("Unable to determine method name in module {}".format(self._filepath))
        
        tokens.append(token)
    
    def _process_call_on_object(self, node: Attribute) -> str:
        """
        Processes a method call which happens on an object
        """
        method_name: str = node.attr
        subscript_depth: int = 0
        subscript_index: int = 0
        if isinstance(node.value, Subscript):
            object_name, subscript_depth = self._get_origin_of_subscript(node.value, 0)
            subscript_index = self._get_index_of_subscript(node.value)
        elif isinstance(node.value, Name):
            object_name = node.value.id

        variable_type: TypeInfo = self.variable_cache.get_variable_type(object_name, subscript_depth, subscript_index)
        token = self._construct_call_token(method_name, variable_type)
        
        return token
    
    def _process_subsequent_call(self):
        pass
    
    def _construct_call_token(self, method_name: str, object_type: TypeInfo) -> str:
        output: str = ""
        if object_type is not None:
            output += "{}.".format(object_type.get_label())
        output += "{}()".format(method_name)
        return output
    
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
        else:
            logger.error("Unable to determine origin name of Subscript in module {}"
            .format(self._filepath))
        return origin_name, depth
    
    def _get_index_of_subscript(self, node: Subscript) -> int:
        """
        Returns the index of the Dict / Tuple object on which the method call happens
        """
        index = None
        try:
            if isinstance(node.slice, Index):
                index_str = node.slice.value.value
                index = int(index_str)
        except ValueError:
            return 1
        return index
            
    
    def _process_for_block(self, node: For, tokens: List[str]):
        tokens.append(Tokens.FOR.value)

        if isinstance(node.iter, Name) or isinstance(node.iter, Subscript):
            self._cache_variables_in_for_block(node)
        elif isinstance(node.iter, Call):
            self._process_call(node.iter, tokens)
        else:
            logger.error("Error, unknown iter type of For node in module {}".format(self._filepath))
        
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_FOR.value)
    
    def _cache_variables_in_for_block(self, node: For):
        """
        Caches variables and their respective types which are used in a for block
        """
        for_target_name: str = ""
        if isinstance(node.target, Name):
            for_target_name = node.target.id
        else:
            logger.warning("Unprocessable For loop target")

        iter_name: str = ""
        subscript_depth: int = 1
        subscript_index: int = 0
        if isinstance(node.iter, Name):
            iter_name = node.iter.id
        elif isinstance(node.iter, Subscript):
            iter_name, subscript_depth = self._get_origin_of_subscript(node.iter, subscript_depth)
            subscript_index = self._get_index_of_subscript(node.iter)
        
        variable_type: TypeInfo = self.variable_cache.get_variable_type(iter_name, subscript_depth, subscript_index)
        self.variable_cache.add_variable(for_target_name, variable_type)

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
                        .format(self._filepath))
                        target_variable = node.target.attr
                else:
                    target_variable = "UNKNOWN"
                    logger.error("Error, could not retrieve variable name for Ann/Assign node in {}"
                    .format(self._filepath))
            else: 
                target_variable = "List Object"
        return target_variable

    def _process_assign(self, node, tokens: List[str]):
        variable_name: str = self._get_variable_name_for_assignment(node)
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)
            logger.warning("Un-annotated assignment for variable [{}] in module {}"
            .format(variable_name, self._filepath))
        elif isinstance(node.value, Constant):
            logger.warning("Un-annotated assignment for variable [{}] with constant value in module {}"
            .format(variable_name, self._filepath))


    def _process_ann_assign(self, node: AnnAssign, tokens: List[str]):
        try:
            info = TypeInfo(node=node.annotation)
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
            self.variable_cache.add_variable(complete_name, info)

        except AttributeError:
            logger.error("Failed processing AnnAssign in module {}".format(self._filepath))
