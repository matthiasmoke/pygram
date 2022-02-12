from typing import Dict, List

from .import_cache import ImportCache
from .type_info import TypeInfo
import logging

logger = logging.getLogger("main")

class TypeCache: 

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.modules: Dict[str, FileCache] = {}
    
    def add_file_cache(self, module_path: str, cache: "FileCache") -> None:
        self.modules[module_path] = cache
    
    def get_return_type_of_function(self, function_name: str, import_cache: ImportCache) -> TypeInfo:
        caches: List[FileCache] = self._get_file_caches_for_name(function_name, import_cache)
        for cache in caches:
            return_type = cache.get_function_type(function_name)

            if return_type is not None:
                return return_type
        logger.error("Could not find function {} for module {} in type cache"
        .format(function_name, import_cache.get_module))
        return None
    
    def get_return_type_of_class_function(self, function_name: str, class_name: str, import_cache: ImportCache) -> TypeInfo:
        caches: List[FileCache] = self._get_file_caches_for_name(class_name, import_cache)
        for cache in caches:
            return_type = cache.get_class_function_type(function_name, class_name)
            if return_type is not None:
                return return_type
        
        logger.error("Could not find function {} for class {} in module {} in type cache"
        .format(function_name, class_name, import_cache.get_module()))
        return None
    
    def find_module_for_type_with_function(self, type_name: str, function_name: str, import_cache: ImportCache) -> str:
        potential_modules: List[str] = import_cache.get_modules_for_name(type_name)

        for module in potential_modules:
            cache: FileCache = self.modules[module]
            if cache.contains_class_function(type_name, function_name):
                return module
        return None
            
    def _get_file_caches_for_name(self, name: str, import_cache: ImportCache) -> List["FileCache"]:
        potential_modules: List[str] = import_cache.get_modules_for_name(name)
        output: List[FileCache] = []
        for module in potential_modules:
                output.append(self.modules[module])
        return output


class FileCache:

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self._class_cache: Dict[str, ClassCache] = {}
        self.function_cache: Dict[str, TypeInfo] = {}
    
    def add_class(self, class_cache: "ClassCache") -> None:
        self._class_cache[class_cache.type] = class_cache
    
    def add_function(self, function_name: str, type: TypeInfo):
        self.function_cache[function_name] = type
    
    def get_function_type(self, function_name) -> TypeInfo:
        function_return_type: TypeInfo = self.function_cache.get(function_name, None)

        if function_return_type is None:
            logger.error("Could not find function {} in {}".format(function_name, self.file_name))
        return function_return_type
    
    def get_class_function_type(self, function_name, class_name) -> TypeInfo:
        class_cache: ClassCache = self._class_cache.get(class_name, None)

        if class_cache is None:
            logger.error("Could not find class {} in {}".format(class_name, self.file_name))

        return class_cache.get_function_type(function_name)
    
    def contains_class_function(self, class_name: str, function_name: str) -> bool:
        class_cache: ClassCache = self._class_cache.get(class_name, None)

        if class_cache is not None:
            return class_cache.contains_function(function_name)
        return False

class ClassCache:

    def __init__(self, class_name: str) -> None:
        self.type: str = class_name
        self.functions: Dict[str, TypeInfo] = {}
        self.sub_classes: Dict[str, ClassCache] = {}
    
    def add_function(self, function_name: str, type: TypeInfo):
        self.functions[function_name] = type
    
    def add_sub_class(self, class_name: str, cache: "ClassCache"):
        self.sub_classes[class_name] = cache
    
    def contains_function(self, function_name) -> bool:
        return function_name in self.functions
    
    def get_function_type(self, function_name: str) -> TypeInfo:
        type: TypeInfo = self.functions.get(function_name, None)
        if type is None:
            logger.error("Could not find function {} in class {}".format(function_name, self.type))
        return type