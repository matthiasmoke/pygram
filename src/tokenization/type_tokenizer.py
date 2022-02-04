import logging
import ast
import os
from _ast import Call, For, AnnAssign, Constant, Attribute, Name, Subscript
from typing import List
from .tokenizer import Tokenizer
from .type_utils import TypeInfo

logger = logging.getLogger("main")

class TypeTokenizer(Tokenizer):

    def __init__(self, filepath) -> None:
        super().__init__(filepath)
        self.variable_type_dict = {}
    
    def _load_syntax_tree(self):
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read(), type_comments=True)
                return tree
        return None
    
    def _process_call(self, node: Call, tokens):
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token = "UNKNOWN"
        if (isinstance(node.func, Name)):
            method_name = node.func.id
            # TODO get origin of function for fully classified name
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func
            method_name = attribute.attr
            object_name = ""
            if isinstance(attribute.value, Subscript):
                object_name = self._get_origin_of_subscript(attribute.value)
            elif isinstance(attribute.value, Name):
                object_name = attribute.value.id
            elif isinstance(attribute.value, Call):
                self._process_call(attribute.value, tokens)
                # TODO get return type of previous method
            else:
                logger.error("Unable to determine Attribute type on Call in module {}"
                .format(self._filepath))
            # TODO get type of object
        else:
            logger.error("Unable to determine method name in module {}".format(self._filepath))
        
        tokens.append(token)
    
    def _get_origin_of_subscript(self, node: Subscript) -> str:
        value = node.value
        origin_name = ""
        if isinstance(value, Subscript):
            origin_name = self._get_origin_of_subscript(value)
        elif isinstance(value, Name):
            origin_name = value.id
        else:
            logger.error("Unable to determine origin name of Subscript in module {}"
            .format(self._filepath))
        return origin_name
    
    def _process_for_block(self, node: For, tokens):
        return super()._process_for_block(node, tokens)

    def _get_variable_name_for_assignment(self, node) -> str:
        target_variable: str = ""

        if isinstance(node, AnnAssign) or isinstance(node, ast.Assign):
            variable_is_class_field: bool = False
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
        return target_variable

    def _process_assign(self, node, tokens: List[str]):
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)
        elif isinstance(node.value, Constant):
            variable_name: str = self._get_variable_name_for_assignment(node)
            logger.warning("Un-annotated assignment for variable [{}] with constant value in module {}"
            .format(variable_name, self._filepath))


    def _process_ann_assign(self, node: AnnAssign, tokens: List[str]):
        try:
            info = TypeInfo(node.annotation)
            pass
        except AttributeError:
            logger.error("Failed processing AnnAssign in module {}".format(self._filepath))
