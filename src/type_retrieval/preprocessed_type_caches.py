from typing import Dict, List, Tuple

from .import_cache import ImportCache
from .type_info import TypeInfo
from ..utils import Utils
import logging
import sys

logger = logging.getLogger("main")
utils: Utils = Utils()

class TypeCache: 

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._smallest_module_level = sys.maxsize
        self._currently_processed_module: str = None
        self.modules: Dict[str, FileCache] = {}
    
    def add_file_cache(self, module_path: str, cache: "FileCache") -> None:
        self.modules[module_path] = cache
        module_level: int = len(module_path.split("."))
        if module_level < self._smallest_module_level:
            self._smallest_module_level = module_level
    
    def set_current_module(self, module_path: str) -> None:
        self._currently_processed_module = module_path
    
    def get_return_type(self, function_name: str, class_name: str = None, module: str = None) -> TypeInfo:
        """
        Retrieves the return type of a given function. 
        If class name is not specified, the method only searches for functions outside of classes
        """
        if class_name is not None:
            return self._get_return_type_of_class_function(function_name, class_name)
        elif module is not None:
            return self._get_return_type_of_function_by_module(function_name, module)
        else:
            return self._get_return_type_of_function(function_name)
    
    def find_module_for_type_with_function(self, type_name: str, function_name: str) -> str:
        """
        Returns a module that contains the given type with given function name
        """
        potential_modules: List[str] = self._get_modules_for_name(type_name)

        for module in potential_modules:
            cache: FileCache = self.modules.get(module, None)
            if cache is not None:
                if cache.contains_class_function(type_name, function_name):
                    return module
        return None
    
    def find_module_for_function(self, function_name):
        """
        Retruns the module that contains the given function name
        """
        potential_modules: List[str] = self._get_modules_for_name(function_name)

        module_path: str = ""
        if len(potential_modules) == 1:
            module_path = potential_modules[0]
        elif len(potential_modules) > 1:
            logger.error("Unable to uniquely map module to function {} in {}"
            .format(function_name, self._currently_processed_module))
        elif len(potential_modules) == 0:
            if utils.is_not_a_builtin_function(function_name):
                logger.warning("Could not find matching modules for funcion {} in {}"
                .format(function_name, self._currently_processed_module))

        return module_path

    def module_contains_type(self, module_path: str, type: str) -> bool:
        module: FileCache = self.modules.get(module_path, None)

        if module is not None:
            return module.contains_type(type)
        return False
    
    def module_contains_function(self, module_path: str, function_name: str) -> bool:
        module: FileCache = self.modules.get(module_path, None)

        if module is not None:
            return module.contains_function(function_name)
        return False
    
    def populate_type_info_with_module(self, type_info: TypeInfo) -> None:
        if type_info is None or type_info.fully_qualified_name != "":
            return
        
        type_name: str = type_info.label
        contained_types: List[TypeInfo] = type_info.get_contained_types()
        for type in contained_types:
            self.populate_type_info_with_module(type)

        if type_name is not None and type_name != "":
            potential_modules = self._get_modules_for_name(type_name)
            module_path: str = ""
            if len(potential_modules) == 1:
                module_path = "{}.".format(potential_modules[0])
            elif len(potential_modules) > 1:
                logger.error("Unable to uniquely map module to type {} in {}"
                .format(type_name, self._currently_processed_module))
            elif len(potential_modules) == 0:
                if type_name != "str" and type_name != "bool" and type_name != "int":
                    logger.warning("Could not find matching modules for type {} in {}"
                    .format(type_name, self._currently_processed_module))
            type_info.set_fully_qualified_name("{}{}".format(module_path, type_name))
        else:
            logger.error("Can not determine module for empty type")
    
    def _get_existing_module_in_cache(self, module_path: str) -> Tuple[str, str]:
        """
        Checks if a given module exists in the cache. If the it is not found,
        the function always removes the last part of the path and checks again as long as 
        the split path level is bigger than the smallest path level in the cache.
        Returns the found module and the split part
        """
        module: FileCache = self.modules.get(module_path, None)
        module_path_parts: int = len(module_path.split("."))
        number_of_splits: int = module_path_parts - self._smallest_module_level
        class_name: str = ""
        if module is None:
            for index in range(0, number_of_splits):
                split_path = module_path.rsplit(".", 1)
                module_path = split_path[0]
                class_name = "{}.{}".format(split_path[1], class_name)
                module = self.modules.get(module_path, None)

                if module is not None:
                    return (module, class_name[:-1])

        return (module, class_name)
    
    def _get_return_type_of_class_function(self, function_name: str, class_name: str) -> TypeInfo:
        caches: List[FileCache] = self._get_file_caches_for_name(class_name)
        for cache in caches:
            return_type = cache.get_class_function_type(function_name, class_name)
            if return_type is not None:
                return return_type
        
        logger.error("Could not find function {} for class {} in module {} in type cache"
        .format(function_name, class_name, self._currently_processed_module))
        return None

    def _get_return_type_of_function(self, function_name: str) -> TypeInfo:
        """
        Retrieves the return type of a function by its name. The search is only applied to functions outside of classes
        """
        caches: List[FileCache] = self._get_file_caches_for_name(function_name)
        for cache in caches:
            return_type = cache.get_function_return_type(function_name)
            if return_type is not None:
                return return_type
        logger.error("Could not find function {} for module {} in type cache"
        .format(function_name, self._currently_processed_module))
        return None
    
    def _get_return_type_of_function_by_module(self, function_name: str, module: str):
        """
        Retrieves the return type of a function by searching in the given module. 
        Includes class and standalone functions.
        """
        module, class_name = self._get_existing_module_in_cache(module)
        if module is not None:
            info: TypeInfo = self._get_return_type_of_function(function_name)
            
            if info is None:
                info = self._get_return_type_of_class_function(function_name, class_name)
                self.populate_type_info_with_module(info)
                return info
        
        logger.debug("Could not find function \"{}\" in module {}".format(function_name, module))        
        return None
    
    def _get_current_import_cache(self) -> ImportCache:
        module_path: str = self._currently_processed_module
        if "__init__" in module_path:
            path_parts: List[str] = module_path.rsplit(".", 1)

            if path_parts[1] == "__init__":
                module_path = path_parts[0]
        return self.modules[module_path].import_cache
    
    def _get_modules_for_name(self, name: str) -> str:
        """
        Retruns the modules that contain the given class/function name.
        """
        current_import_cache: ImportCache = self._get_current_import_cache()
        potential_modules: List[str] = []
        imported_modules: List[str] = current_import_cache.get_module_imports_for_name(name)
        modules: List[str] = []
        modules += imported_modules
        modules.append(self._currently_processed_module)

        # check if a project internal module contains the name
        for module in modules:
            if self.module_contains_type(module, name):
                potential_modules.append(module)
            elif self.module_contains_function(module, name):
                # only append module that contains a function with that name if there are no other modules yet
                if len(potential_modules) < 1:
                    potential_modules.append(module)
        
        return potential_modules

    def _get_file_caches_for_name(self, name: str) -> List["FileCache"]:
        """
        Returns the file caches for a given name
        """
        potential_modules: List[str] = self._get_modules_for_name(name)
        output: List[FileCache] = []
        for module in potential_modules:
            cache: FileCache = self.modules.get(module, None)
            if cache is not None:
                output.append(cache)
        return output


class FileCache:

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self.import_cache: ImportCache = None
        self._class_cache: Dict[str, ClassCache] = {}
        self._function_cache: Dict[str, TypeInfo] = {}
    
    def set_import_cache(self, cache: ImportCache) -> None:
        self.import_cache = cache
    
    def add_class(self, class_cache: "ClassCache") -> None:
        self._class_cache[class_cache.type] = class_cache
    
    def add_function(self, function_name: str, type: TypeInfo) -> None:
        self._function_cache[function_name] = type
    
    def get_function_return_type(self, function_name) -> TypeInfo:
        function_return_type: TypeInfo = self._function_cache.get(function_name, None)

        if function_return_type is None:
            logger.error("Could not find function {} in {}".format(function_name, self.file_name))
        return function_return_type
    
    def get_class_function_type(self, function_name, class_name) -> TypeInfo:
        class_cache: ClassCache = self._class_cache.get(class_name, None)

        if class_cache is None:
            logger.error("Could not find class {} in {}".format(class_name, self.file_name))
            return None

        return class_cache.get_function_return_type(function_name)
    
    def contains_class_function(self, class_name: str, function_name: str) -> bool:
        class_cache: ClassCache = self._class_cache.get(class_name, None)

        if class_cache is not None:
            return class_cache.contains_function(function_name)
        return False
    
    def contains_type(self, type_name: str) -> bool:
        for key, value in self._class_cache.items():
            contains_type: bool = value.is_type(type_name)
            if contains_type is True:
                return True
        return False
    
    def contains_function(self, function_name: str) -> bool:
        for key in self._function_cache:
            if key == function_name:
                return True

class ClassCache:

    def __init__(self, class_name: str) -> None:
        self.type: str = class_name
        self._functions: Dict[str, TypeInfo] = {}
    
    def add_function(self, function_name: str, type: TypeInfo) -> None:
        self._functions[function_name] = type
    
    def contains_function(self, function_name) -> bool:
        return function_name in self._functions
    
    def is_type(self, type_name: str) -> bool:
        return self.type == type_name

    def get_function_return_type(self, function_name: str) -> TypeInfo:
        type: TypeInfo = self._functions.get(function_name, None)
        if type is None:
            logger.error("Could not find function {} in class {}".format(function_name, self.type))
        return type
    