import os
from typing import Tuple
import logging
from _ast import ClassDef, FunctionDef, AsyncFunctionDef
from .preprocessed_type_caches import ClassCache, FileCache, TypeCache
from .type_info import TypeInfo
from ..utils import Utils

logger = logging.getLogger("main")

class TypePreprocessor():

    def __init__(self, projectpath: str) -> None:
        self._projectpath: str = projectpath
        self._project_name: str = ""
        self._type_cache: TypeCache = None
    
    def process_project(self):
        path: str = self._projectpath
        if os.path.isdir(self._projectpath):
            self._project_name = Utils.get_last_element_of_path(path)
            self._type_cache = TypeCache(self._project_name)
            for file in Utils.get_all_python_files_in_directory(path):
                self._process_file(file)
        
    def _process_file(self, path: str) -> FileCache:
        logger.debug("Preprocessing {}".format(path))
        syntax_tree = Utils.load_syntax_tree(path, True)
        file_cache: FileCache = None
        if syntax_tree is not None:
            file_name: str = Utils.get_last_element_of_path(path)
            file_cache = FileCache(file_name)
            self._search_ast(syntax_tree, file_cache)
            # TODO convert path to dotted module path
            self._type_cache.add_file_cache(path, file_cache)
        else:
            logger.error("Could not preprocess file {}".format(path))
        return file_cache

    def _search_ast(self, tree, cache: FileCache):
        for node in tree.body:
            if isinstance(node, ClassDef):
                class_cache = self._process_class(node)
                cache.add_class(class_cache)
            if self._is_function_node(node):
                name, return_type = self._process_function(node)
                cache.add_function(name, return_type)

    def _process_class(self, class_node: ClassDef) -> ClassCache:
        cache: ClassCache = ClassCache(class_node.name)

        for node in class_node.body:
            if self._is_function_node(node):
                name, return_type = self._process_function(node)
                cache.add_function(name, return_type)
            if isinstance(node, ClassDef):
                sub_class_cache: ClassCache = self._process_class(node)
                cache.add_sub_class(sub_class_cache)
        return cache
        

    def _process_function(self, node: FunctionDef) -> Tuple[str, TypeInfo]:
        name: str = node.name
        return_info = node.returns

        if return_info is None or return_info == "None":
            return (name, None)
        type_info: TypeInfo = TypeInfo(annotation_node=node.returns)
        return (name, type_info)

    def _is_function_node(self, node) -> bool:
        return isinstance(node, FunctionDef) or isinstance(node, AsyncFunctionDef)


    



