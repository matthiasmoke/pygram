import logging
import ast
import os
from _ast import ClassDef, FunctionDef, AsyncFunctionDef, Name, Attribute, AnnAssign, Assign, AugAssign, Await, With, withitem, Pass, Expr, Return, For, While, If, Call, Raise, Try, Assert, Pass, Yield, Break, Tuple
from typing import List
from .tokens import Tokens


logger = logging.getLogger("main")


class Tokenizer:

    def __init__(self, filepath) -> None:
        self._filepath: str = filepath
        self._syntax_tree = None
        self.sequence_stream: List[str] = []

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

    def process_file(self) -> List[List[str]]:
        """
        Gets all tokens from a source file and retruns a list logical dependent token sequences
        """
        if self._syntax_tree is None:
            logger.warning("Syntax tree is None, abort processing file {}"
                           .format(os.path.basename(self._filepath)))
            return None
        self._ast_depth_search()
        return self.sequence_stream

    def _load_syntax_tree(self):
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
                    result = self._process_class_def(node)

                    if len(result):
                        self.sequence_stream += result

                else:
                    self._classify_and_process_node(node, module_tokens)
            if len(module_tokens):
                self.sequence_stream.append(module_tokens)

    def _search_node_body(self, node_body, tokens=None) -> List[str]:
        if tokens is None:
            tokens = []

        for child in node_body:
            self._classify_and_process_node(child, tokens)
        return tokens
    
    def _classify_and_process_node(self, node, token_list: List[str]) -> List[str]:
        logger.debug("Processing node {} in line {}".format(node, node.lineno))
        if isinstance(node, If):
            self._process_if_block(node, token_list)
        elif isinstance(node, For):
            self._process_for_block(node, token_list)
        elif isinstance(node, While):
            self._process_while_block(node, token_list)
        elif isinstance(node, Try):
            self._process_try_block(node, token_list)
        elif isinstance(node, Raise):
            self._process_raise(node, token_list)
        elif (isinstance(node, With)):
            self._process_with_block(node, token_list)
        elif isinstance(node, Assert):
            self._process_assert(node, token_list)
        elif (isinstance(node, Assign) or isinstance(node, AugAssign)):
            self._process_assign(node, token_list)
        elif isinstance(node, Await):
            self._process_await(node, token_list)
        elif isinstance(node, Expr):
            self._process_expression(node, token_list)
        elif isinstance(node, Call):
            self._process_call(node, token_list)
        elif isinstance(node, Tuple):
            self._process_tuple(node, token_list)
        elif isinstance(node, Pass):
            token_list.append(Tokens.PASS.value)
        elif isinstance(node, Break):
            token_list.append(Tokens.BREAK.value)
        elif isinstance(node, Return):
            token_list.append(Tokens.RETURN.value)
        elif isinstance(node, AnnAssign):
            # The type annotation node is included here, so the whole method 
            # does not need an override in the typed tokenizer
            self._process_ann_assign(node, token_list)
    
    def _process_if_block(self, node: If, tokens):
        tokens.append(Tokens.IF.value)
        if node.test and isinstance(node.test, Call):
            self._process_call(node.test, tokens)

        self._search_node_body(node.body, tokens)

        if node.orelse:
            tokens.append(Tokens.ELSE.value)
            self._search_node_body(node.orelse, tokens)
        tokens.append(Tokens.END_IF.value)
    
    def _process_while_block(self, node: While, tokens: List[str]):
            tokens.append(Tokens.WHILE.value)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.END_WHILE.value)
    
    def _process_raise(self, node: Raise, tokens: List[str]):
            tokens.append(Tokens.RAISE.value)
            if isinstance(node.exc, Call):
                self._process_call(node.exc, tokens)
    
    def _process_try_block(self, node: Try, tokens: List[str]):
        tokens.append(Tokens.TRY.value)
        self._search_node_body(node.body, tokens)

        for handler in node.handlers:
            tokens.append(Tokens.EXCEPT.value)
            if handler.type is not None:
                if hasattr(handler.type, "id"):
                    tokens.append(handler.type.id + "()")
                elif hasattr(handler.type, "attr"):
                    tokens.append(handler.type.attr + "()")
            self._search_node_body(handler.body, tokens)
            tokens.append(Tokens.END_EXCEPT.value)
        
        if len(node.finalbody):
            tokens.append(Tokens.FINALLY.value)
            self._search_node_body(node.finalbody, tokens)
            tokens.append(Tokens.END_FINALLY.value)
    
    def _process_with_block(self, node: With, tokens: List[str]):
            tokens.append(Tokens.WITH.value)
            if len(node.items):
                for item in node.items:
                    if isinstance(item, withitem) and isinstance(item.context_expr, Call):
                        self._process_call(item.context_expr, tokens)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.END_WITH.value)
    
    def _process_assert(self, node: Assert, tokens: List[str]):
            tokens.append(Tokens.ASSERT.value)
            if node.test and isinstance(node.test, Call):
                self._process_call(node.test, tokens)
    
    def _process_assign(self, node, tokens: List[str]):
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)
    
    def _process_await(self, node: Await, tokens: List[str]):
        tokens.append(Tokens.AWAIT.value)
        if isinstance(node.value, Call):
            self._process_call(node.value, tokens)

    def _process_expression(self, node: Expr, tokens: List[str]):
        self._classify_and_process_node(node.value, tokens)

    #### Functions to override in typed tokenization

    def _process_class_def(self, node: ClassDef) -> List[str]:
        class_tokens = []

        for child in node.body:
            if isinstance(child, FunctionDef) or isinstance(child, AsyncFunctionDef):
                result = self._process_function_def(child)
                class_tokens.append(result)
            else:
                self._classify_and_process_node(child, class_tokens)

        return class_tokens
    
    def _process_function_def(self, node) -> List[str]:
        tokens = []

        if isinstance(node, AsyncFunctionDef):
            tokens.append(Tokens.ASYNC.value)
        
        tokens.append(Tokens.DEF.value)
        self._search_node_body(node.body, tokens)
        tokens.append(Tokens.END_DEF.value)
        return tokens

    def _process_call(self, node: Call, tokens: List[str]):
        if len(node.args):
            self._search_node_body(node.args, tokens)
        
        token = "UNKNOWN"
        if (isinstance(node.func, Name)):
            token = node.func.id + "()"
        elif isinstance(node.func, Attribute):
            attribute: Attribute = node.func
            token = attribute.attr + "()"
            if isinstance(attribute.value, Call):
                self._process_call(attribute.value, tokens)
                token = attribute.attr + "()"
        else:
            logger.error("Unable to determine method name in module {}".format(self._filepath))
        
        tokens.append(token)
    
    def _process_tuple(self, node: Tuple, tokens: List[str]):
        self._search_node_body(node.elts, tokens)

    def _process_for_block(self, node: For, tokens: List[str]):
            tokens.append(Tokens.FOR.value)
            self._classify_and_process_node(node.iter, tokens)
            self._search_node_body(node.body, tokens)
            tokens.append(Tokens.END_FOR.value)
    
    def _process_ann_assign(self, node: ast.AnnAssign, tokens: List[str]):
        pass
