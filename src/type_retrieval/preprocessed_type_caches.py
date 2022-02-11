from typing import Dict, List
from .type_info import TypeInfo
import logging

logger = logging.getLogger("main")

class TypeCache: 

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.modules: Dict[str, FileCache] = {}
    
    def add_file_cache(self, module_path: str, cache: "FileCache") -> None:
        self.modules[module_path] = cache
    
    def get_return_type_of_function(self, function_name: str, potential_modules: List[str]) -> TypeInfo:
        return_type: TypeInfo = None
        for module in potential_modules:
            if module in potential_modules:
                file_cache: FileCache = self.modules[module]
                return_type = file_cache.get_function_type(function_name)
        return return_type
    
    def get_return_type_of_class_function(self, function_name: str, class_name: str, potential_modules: List[str]) -> TypeInfo:
        return_type: TypeInfo = None
        for module in potential_modules:
            if module in potential_modules:
                file_cache: FileCache = self.modules[module]
                return_type = file_cache.get_class_function_type(function_name, class_name)
        return return_type
    
                


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

class ClassCache:

    def __init__(self, class_name: str) -> None:
        self.type: str = class_name
        self.functions: Dict[str, TypeInfo] = {}
        self.sub_classes: Dict[str, ClassCache] = {}
    
    def add_function(self, function_name: str, type: TypeInfo):
        self.functions[function_name] = type
    
    def add_sub_class(self, class_name: str, cache: "ClassCache"):
        self.sub_classes[class_name] = cache
    
    def get_function_type(self, function_name: str) -> TypeInfo:
        type: TypeInfo = self.functions.get(function_name, None)
        if type is None:
            logger.error("Could not find function {} in class {}".format(function_name, self.type))
        return type