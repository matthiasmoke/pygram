import logging
import ast
import os
from _ast import YieldFrom, UnaryOp, Match, Global, Nonlocal, Delete, ImportFrom, Import, ClassDef, FunctionDef, AsyncFunctionDef, Name, Attribute, AnnAssign, Assign, AugAssign, Continue, Yield, Await, With, withitem, Pass, Expr, Return, For, While, If, BoolOp, Compare, Call, Raise, Try, Assert, Pass, Yield, Break
import _ast
from typing import List, Tuple

from ..utils import Utils
from .tokens import Tokens


logger = logging.getLogger("main")


class Tokenizer:

    def __init__(self, filepath, module_name) -> None:
        self._filepath: str = filepath
        self.module_path: str = Utils.generate_dotted_module_path(filepath, module_name)
        self._syntax_tree = None
        self.sequence_stream: List[List[Tuple[str, int]]] = []

        self._syntax_tree = self._load_syntax_tree()
    
    def __str__(self):
        output = str(self._filepath) + "\n\n"

        for sequence in self.sequence_stream:
            output += "["
            for (index, token) in enumerate(sequence):
                if index < len(sequence) - 1:
                    output += "{}, ".format(token)
                else:
                    output += "{}]".format(token)
            output += "\n"

        return output

    def process_file(self) -> List[List[Tuple[str, int]]]:
        """
        Gets all tokens from a source file and retruns a list logical dependent token sequences
        """
        if self._syntax_tree is None:
            logger.warning("Syntax tree is None, abort processing file {}"
                           .format(os.path.basename(self.module_path)))
            return None
        self._ast_depth_search()
        return self.sequence_stream

    def _load_syntax_tree(self) -> None:
        if os.path.isfile(self._filepath):
            with open(self._filepath, "r") as source:
                logger.debug("Loading syntax tree")
                tree = ast.parse(source.read())
                return tree
        return None

    def _ast_depth_search(self) -> None:
        logger.debug("Starting depth search of syntax tree")
        if self._syntax_tree.body is not None:
            module_tokens = []
            for node in self._syntax_tree.body:
                if isinstance(node, FunctionDef) or isinstance(node, AsyncFunctionDef):
                    result = self._process_function_def(node)
                    self.sequence_stream.append(result)

                elif isinstance(node, ClassDef):
                    result = self._process_class_def(node, module_tokens)

                    if len(result):
                        self.sequence_stream += result

                else:
                    self._classify_and_process_node(node, module_tokens)
            if len(module_tokens):
                self.sequence_stream.append(module_tokens)

    def _search_node_body(self, node_body, tokens=None) -> List[Tuple[str, int]]:
        if tokens is None:
            tokens = []

        for child in node_body:
            self._classify_and_process_node(child, tokens)
        return tokens
    
    def _classify_and_process_node(self, node, token_list: List[Tuple[str, int]]) -> None:
        if node is None:
            return
        logger.debug("Processing node {} in line {}".format(node, node.lineno))
        match node:
            case If():
                self._process_if_block(node, token_list)
            case For():
                self._process_for_block(node, token_list)
            case While():
                self._process_while_block(node, token_list)
            case Match():
                self._process_match(node, token_list)
            case Try():
                self._process_try_block(node, token_list)
            case Raise():
                self._process_raise(node, token_list)
            case With():
                self._process_with_block(node, token_list)
            case Assert():
                self._process_assert(node, token_list)
            case Assign():
                self._process_assign(node, token_list)
            case AugAssign():
                self._process_assign(node, token_list)
            case Await():
                self._process_await(node, token_list)
            case Expr():
                self._process_expression(node, token_list)
            case Call():
                self._process_call(node, token_list)
            case _ast.Tuple():
                self._process_tuple(node, token_list)
            case Return():
                self._process_retrun(node, token_list)
            case Yield():
                self._process_yield(node, token_list)
            case Compare():
                self._process_compare(node, token_list)
            case Pass():
                self._add_token(token_list, Tokens.PASS.value, node)
            case Break():
                self._add_token(token_list, Tokens.BREAK.value, node)
            case Continue():
                self._add_token(token_list, Tokens.CONTINUE.value, node)
            case Global():
                self._add_token(token_list, Tokens.GLOBAL.value, node)
            case Nonlocal():
                self._add_token(token_list, Tokens.NONLOCAL.value, node)
            case Delete():
                self._add_token(token_list, Tokens.DEL.value, node)
            case YieldFrom():
                self._add_token(token_list, Tokens.YIELD_FROM.value, node)
            case FunctionDef():
                tokens: List[Tuple[str, int]] = self._process_function_def(node)
                token_list += tokens
            case AnnAssign():
                # The type annotation node is included here, so the whole method 
                # does not need an override in the typed tokenizer
                self._process_ann_assign(node, token_list)
            case ImportFrom():
                self._process_import(node)
            case Import():
                self._process_import(node)
    
    def _process_match(self, node: Match, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.MATCH.value, node)

        for case in node.cases:
            self._add_token(tokens, Tokens.CASE.value, node)
            self._search_node_body(case.body, tokens)
            self._add_token(tokens, Tokens.END_CASE.value, node)
        self._add_token(tokens, Tokens.END_MATCH.value, node)

    def _process_test_expression(self, test_node, tokens: List[Tuple[str, int]]):
        if test_node is not None:
            if isinstance(test_node, BoolOp):
                self._process_bool_op(test_node, tokens)
            elif isinstance(test_node, UnaryOp):
                self._classify_and_process_node(test_node.operand, tokens)
            else:
                self._classify_and_process_node(test_node, tokens)

    def _process_if_block(self, node: If, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.IF.value, node)
        self._process_test_expression(node.test, tokens)
        self._search_node_body(node.body, tokens)

        if node.orelse:
            self._add_token(tokens, Tokens.ELSE.value, node)
            self._search_node_body(node.orelse, tokens)
        self._add_token(tokens, Tokens.END_IF.value, node)
    
    def _process_compare(self, node: Compare, tokens: List[Tuple[str, int]]):
        self._classify_and_process_node(node.left, tokens)
        self._search_node_body(node.comparators, tokens)
    
    def _process_bool_op(self, node: BoolOp, tokens):     
        for child in node.values:
            if isinstance(child, BoolOp):
                self._process_bool_op(child, tokens)
            else:
                self._classify_and_process_node(child, tokens)
    
    def _process_while_block(self, node: While, tokens: List[Tuple[str, int]]):
            self._add_token(tokens, Tokens.WHILE.value, node)
            self._process_test_expression(node.test, tokens)
            self._search_node_body(node.body, tokens)
            if len(node.orelse):
                self._add_token(tokens, Tokens.ELSE.value, node)
                self._search_node_body(node.orelse, tokens)
            self._add_token(tokens, Tokens.END_WHILE.value, node)
    
    def _process_raise(self, node: Raise, tokens: List[Tuple[str, int]]):
            self._add_token(tokens, Tokens.RAISE.value, node)
            if hasattr(node, "exc"):
                self._classify_and_process_node(node.exc, tokens)
    
    def _process_try_block(self, node: Try, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.TRY.value, node)
        self._search_node_body(node.body, tokens)

        for handler in node.handlers:
            self._add_token(tokens, Tokens.EXCEPT.value, node)
            if handler.type is not None:
                if hasattr(handler.type, "id"):
                    tokens.append(handler.type.id + "()")
                elif hasattr(handler.type, "attr"):
                    tokens.append(handler.type.attr + "()")
            self._search_node_body(handler.body, tokens)
            self._add_token(tokens, Tokens.END_EXCEPT.value, node)
        
        if len(node.finalbody):
            self._add_token(tokens, Tokens.FINALLY.value, node)
            self._search_node_body(node.finalbody, tokens)
            self._add_token(tokens, Tokens.END_FINALLY.value, node)
    
    def _process_with_block(self, node: With, tokens: List[Tuple[str, int]]):
            self._add_token(tokens, Tokens.WITH.value, node)
            if len(node.items):
                for item in node.items:
                    if isinstance(item, withitem) and isinstance(item.context_expr, Call):
                        self._process_call(item.context_expr, tokens)
            self._search_node_body(node.body, tokens)
            self._add_token(tokens, Tokens.END_WITH.value, node)
    
    def _process_assert(self, node: Assert, tokens: List[Tuple[str, int]]):
            self._add_token(tokens, Tokens.ASSERT.value, node)
            if hasattr(node, "test"):
                self._classify_and_process_node(node.test, tokens)
    
    def _process_assign(self, node, tokens: List[Tuple[str, int]]):
        if hasattr(node, "value"):
            self._classify_and_process_node(node.value, tokens)
    
    def _process_await(self, node: Await, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.AWAIT.value, node)
        if hasattr(node, "value"):
            self._classify_and_process_node(node.value, tokens)

    def _process_expression(self, node: Expr, tokens: List[Tuple[str, int]]):
        self._classify_and_process_node(node.value, tokens)
    
    def _process_retrun(self, node: Return, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.RETURN.value, node)
        if hasattr(node, "value"):
            self._classify_and_process_node(node.value, tokens)

    def _process_yield(self, node: Return, tokens: List[Tuple[str, int]]):
        self._add_token(tokens, Tokens.YIELD.value, node)
        if hasattr(node, "value"):
            self._classify_and_process_node(node.value, tokens)

    #### Functions to override in typed tokenization

    def _process_class_def(self, node: ClassDef, module_tokens: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """
        Creates sequences for every function definition inside a class definition. 
        Nodes which are not contained inside a function def are added to the module sequence
        """
        class_tokens = []

        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                result = self._process_function_def(child)
                class_tokens.append(result)
            elif isinstance(child, ClassDef):
                result = self._process_class_def(child, module_tokens)
                class_tokens += result
            else:
                self._classify_and_process_node(child, module_tokens)

        return class_tokens
    
    def _process_function_def(self, node) -> List[Tuple[str, int]]:
        tokens = []

        if isinstance(node, AsyncFunctionDef):
            self._add_token(tokens, Tokens.ASYNC.value, node)
        
        self._add_token(tokens, Tokens.DEF.value, node)
        self._search_node_body(node.body, tokens)
        self._add_token(tokens, Tokens.END_DEF.value, node)
        return tokens

    def _process_call(self, node: Call, tokens: List[Tuple[str, int]]):
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token = "UNKNOWN"
        function_name: str = ""
        if (isinstance(node.func, Name)):
            function_name = node.func.id
            token = self._construct_call_token(function_name)
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func
            function_name = attribute.attr
            token = self._construct_call_token(function_name)
            if isinstance(attribute.value, Call):
                self._process_call(attribute.value, tokens)

        else:
            logger.error("Unable to determine method name in module {}".format(self.module_path))
        
        self._add_token(tokens, token, node)
    
    def _construct_call_token(self, function_name) -> str:
        return "{}()".format(function_name)
    
    def _add_token(self, list: List[Tuple[str, int]], token: str, node) -> None:
        line_no = node.lineno
        list.append((token, line_no))
    
    def _process_tuple(self, node: Tuple, tokens: List[Tuple[str, int]]):
        self._search_node_body(node.elts, tokens)

    def _process_for_block(self, node: For, tokens: List[Tuple[str, int]]):
            self._add_token(tokens, Tokens.FOR.value, node)
            self._classify_and_process_node(node.iter, tokens)
            self._search_node_body(node.body, tokens)
            if len(node.orelse):
                self._add_token(tokens, Tokens.ELSE.value, node)
                self._search_node_body(node.orelse, tokens)
            self._add_token(tokens, Tokens.END_FOR.value, node)
    
    def _process_ann_assign(self, node: ast.AnnAssign, tokens: List[Tuple[str, int]]):
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)

    def _process_import(self, node):
        pass