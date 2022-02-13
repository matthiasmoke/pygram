import logging
import ast
import os
from _ast import ImportFrom, Import, Call, For, AnnAssign, Constant, Attribute, Name, Subscript, FunctionDef, ClassDef, AsyncFunctionDef, Index
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
        self._import_cache = ImportCache(self.module_path)
        self._variable_cache: VariableTypeCache = VariableTypeCache(filepath)
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
        class_name = node.name
        self._variable_cache.set_class_scope(node.name)
        class_type = TypeInfo(label=class_name)
        self._type_cache.populate_type_info_with_module(class_type)
        self._variable_cache.add_variable("self", class_type)
        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                result = self._process_function_def(child)
                class_tokens.append(result)
            else:
                self._classify_and_process_node(child, class_tokens)
        self._variable_cache.leave_class_scope()
        return class_tokens
    
    def _process_function_def(self, node) -> List[str]:
        tokens = []
        self._variable_cache.set_function_scope(node.name)
        if isinstance(node, AsyncFunctionDef):
            tokens.append(Tokens.ASYNC.value)
        
        tokens.append(Tokens.DEF.value)
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_DEF.value)
        self._variable_cache.leave_function_scope()
        return tokens
    
    def _process_call(self, node: Call, tokens) -> Tuple[str, TypeInfo]:
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token: str = "UNKNOWN"
        method_name: str = ""
        variable_type: TypeInfo = None
        if (isinstance(node.func, Name)):
            method_name = node.func.id
            module: str = self._type_cache.find_module_for_function(method_name)
            if module != "":
                token = "{}.{}()".format(module, method_name)
            else:
                token = "{}()".format(method_name)
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func

            if isinstance(attribute.value, Subscript) or isinstance(attribute.value, Name):
                token, method_name, variable_type = self._process_call_on_object(attribute)

            elif isinstance(attribute.value, Call):
                prev_method_name, prev_type = self._process_call(attribute.value, tokens)
                prev_type_label = None

                if prev_type is not None:
                    prev_type_label = prev_type.get_label()

                method_name = attribute.attr
                type: TypeInfo = self._type_cache.get_return_type(prev_method_name, class_name=prev_type_label)
                variable_type = type
                token = self._construct_call_token(attribute.attr, type)
            else:
                logger.error("Unable to determine Attribute type on Call in module {}"
                .format(self.module_path))
        else:
            logger.error("Unable to determine method name in module {}".format(self.module_path))
        
        tokens.append(token)
        return (method_name, variable_type)

    def _process_call_on_object(self, node: Attribute) -> Tuple[str, str, TypeInfo]:
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

        variable_type: TypeInfo = self._variable_cache.get_variable_type(object_name, subscript_depth, subscript_index)
        token = ""
        # if variable type is not found, check if the method is called on a class directly
        if variable_type is None:
            module: str = self._type_cache.find_module_for_type_with_function(object_name, method_name)
            if module is not None and module != "":
                token = "{}.{}.{}()".format(module, object_name, method_name)
            else:
                token = "{}()".format(method_name)
        else:
            token = self._construct_call_token(method_name, variable_type)
        
        return (token, method_name, variable_type)
    
    def _construct_call_token(self, method_name: str, object_type: TypeInfo) -> str:
        output: str = ""
        if object_type is not None:
            output += "{}.".format(str(object_type))
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
            .format(self.module_path))
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
        except AttributeError:
            return 1
        return index
            
    
    def _process_for_block(self, node: For, tokens: List[str]):
        tokens.append(Tokens.FOR.value)

        if isinstance(node.iter, Name) or isinstance(node.iter, Subscript):
            self._cache_variables_in_for_block(node)
        elif isinstance(node.iter, Call):
            self._process_call(node.iter, tokens)
        elif isinstance(node.iter, Attribute):
            pass
        else:
            logger.error("Error, unknown iter type of For node in module {}".format(self.module_path))
        
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
        
        variable_type: TypeInfo = self._variable_cache.get_variable_type(iter_name, subscript_depth, subscript_index)
        self._variable_cache.add_variable(for_target_name, variable_type)

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
            info = TypeInfo(annotation_node=node.annotation)
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
