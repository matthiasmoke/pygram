import os
from typing import List, Tuple
import logging
import difflib
from _ast import ClassDef, FunctionDef, AsyncFunctionDef, Import, ImportFrom

from .import_cache import ImportCache
from .preprocessed_type_caches import ClassCache, FileCache, TypeCache
from .type_info import TypeInfo
from ..utils import Utils

logger = logging.getLogger("main")

class TypePreprocessor():

    def __init__(self, projectpath: str) -> None:
        self._projectpath: str = projectpath
        self._project_name: str = ""
        self._current_module_path: str = ""
        self._available_modules: List[str] = []
        self._type_cache: TypeCache = None
        self._current_file_cache: FileCache = None
    
    def process_project(self):
        path: str = self._projectpath
        if os.path.isdir(self._projectpath):
            self._project_name = Utils.get_last_element_of_path(path)
            self._type_cache = TypeCache(self._project_name)
            available_files: List[str] = Utils.get_all_python_files_in_directory(path)
            self._available_modules = self._get_available_modules(available_files)
            for file in available_files:
                self._process_file(file)
        return self._type_cache
        
    def _process_file(self, path: str) -> FileCache:
        print("Preprocessing {}".format(path))
        syntax_tree = Utils.load_syntax_tree(path, True)
        file_cache: FileCache = None
        if syntax_tree is not None:
            path_within_project: str = Utils.get_only_project_path(self._projectpath, path)
            self._current_module_path = Utils.generate_dotted_module_path(path_within_project)
            file_name: str = Utils.get_last_element_of_path(path)
            file_cache = FileCache(file_name)
            import_cache: ImportCache = ImportCache()
            file_cache.set_import_cache(import_cache)
            self._current_file_cache = file_cache
            self._search_ast(syntax_tree, self._current_file_cache)

            if file_name == "__init__.py":
                self._current_module_path = self._current_module_path.rsplit(".", 1)[0]

            self._type_cache.add_file_cache(self._current_module_path, self._current_file_cache)
        else:
            logger.error("Could not preprocess file {}".format(path))
        return file_cache

    def _search_ast(self, tree, cache: FileCache):
        for node in tree.body:
            if isinstance(node, ClassDef):
                self._process_class(node, cache)
            elif self._is_function_node(node):
                name, return_type = self._process_function(node)
                cache.add_function(name, return_type)
            elif isinstance(node, Import):
                self._process_import
            elif isinstance(node, ImportFrom):
                self._process_import_from(node)
    
    def _process_import(self, node: Import):
        for module in node.names:
            name: str = module.name
            self._current_file_cache.import_cache.add_import(name, [name])

            if module.asname:
                self._current_file_cache.import_cache.add_import_alias(module.asname, name)

    def _process_import_from(self, node: ImportFrom):
        module: str = node.module
        level: int = node.level

        complete_path = self._generate_complete_import_path(module, level, node)
        classes: List[str] = []
        for name in node.names:
            classes.append(name.name)
            if name.asname is not None and name.asname != "None":
                self._current_file_cache.import_cache.add_import_alias(name.asname, name.name)
        
        self._current_file_cache.import_cache.add_import(complete_path, classes)

    def _generate_complete_import_path(self, import_path: str, level: int, node) -> str:
        module_path_parts = self._current_module_path.split(".")
        module_level = len(module_path_parts) - 1

        if level == 0:
            return self._generate_complete_absolute_import_path(import_path, node)
        if level == 1:
            level = module_level

        prefix: str = ""
        complete_path: str = ""
        for i in range (0, level):
            prefix += "{}.".format(module_path_parts[i])
        complete_path = "{}{}".format(prefix, import_path)

        if complete_path not in self._available_modules:
            # if the generated path is not present in the available modules, it is a native import
            return import_path
        return complete_path

    def _generate_complete_absolute_import_path(self, import_path: str, node) -> str:
        """
        Retrieves the possible full module path for a absolute import by comparing it to all available module paths
        """
        possible_modules_for_import: List[str] = []
        for path in self._available_modules:
            if import_path in path:
                possible_modules_for_import.append(path)
        
        if len(possible_modules_for_import) > 1:
            logger.debug("Could not uniquely assign absolute import {} to imported module.\n Current Module {}, line no: {}"
            .format(import_path, self._current_module_path, node.lineno))
            return self._find_highest_matching_module(import_path, possible_modules_for_import)

        # if no possible modules are found, the imported module is not part of the project
        if len(possible_modules_for_import) == 0:
            return import_path
        
        return possible_modules_for_import[0]
    
    def _find_highest_matching_module(self, import_path: str, modules: List[str]) -> str:
        """
        Finds a module in the given available module with matches the given import path the most
        """
        matches: List[str] = difflib.get_close_matches(import_path, modules, 3)
        logger.debug("Found {} best matches for import {}".format(len(matches), import_path))
        if len(matches) == 0:
            logger.debug("Could not find best matches for import {}".format(import_path))
            return import_path
        return matches[0]

    def _get_available_modules(self, files: List[str]) -> List[str]:
        """
        Retruns a list of all available (dotted) module paths in the project. 
        """
        output: List[str] = []
        for file in files:
            path_within_project: str = Utils.get_only_project_path(self._projectpath, file)
            file_name: str = Utils.get_last_element_of_path(file)
            module_path: str = Utils.generate_dotted_module_path(path_within_project)

            if file_name == "__init__.py":
                module_path = module_path.rsplit(".", 1)[0]
            
            output.append(module_path)
        
        return output


    def _process_class(self, class_node: ClassDef, file_cache: FileCache, class_stack: List[str] = []) -> ClassCache:
        class_name: str = class_node.name
        class_stack.append(class_name)
        class_name = Utils.create_full_class_name(class_stack)
        cache: ClassCache = ClassCache(class_name)

        for node in class_node.body:
            if self._is_function_node(node):
                name, return_type = self._process_function(node)
                cache.add_function(name, return_type)
            if isinstance(node, ClassDef):
                self._process_class(node, file_cache, class_stack=class_stack)
                cache.add_function(node.name, None)
        file_cache.add_class(cache)
        class_stack.pop()
        

    def _process_function(self, node: FunctionDef) -> Tuple[str, TypeInfo]:
        name: str = node.name
        return_info = node.returns

        if return_info is None or return_info == "None":
            return (name, None)
        type_info: TypeInfo = TypeInfo(annotation_node=node.returns)
        return (name, type_info)

    def _is_function_node(self, node) -> bool:
        return isinstance(node, FunctionDef) or isinstance(node, AsyncFunctionDef)
