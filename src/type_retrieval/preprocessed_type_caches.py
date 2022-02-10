from typing import Dict, List
from .type_info import TypeInfo

class TypeCache: 

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.modules: Dict[str, FileCache] = {}
    
    def add_file_cache(self, module_path: str, cache: "FileCache") -> None:
        self.modules[module_path] = cache

class FileCache:

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self._class_cache: List[ClassCache] = []
        self.function_cache: Dict[str, TypeInfo] = {}
    
    def add_class(self, class_cache: "ClassCache") -> None:
        self._class_cache.append(class_cache)
    
    def add_function(self, function_name: str, type: TypeInfo):
        self.function_cache[function_name] = type


class ClassCache:

    def __init__(self, class_name: str) -> None:
        self.type: str = class_name
        self.functions: Dict[str, TypeInfo] = {}
        self.sub_classes: Dict[str, ClassCache] = {}
    
    def add_function(self, function_name: str, type: TypeInfo):
        self.functions[function_name] = type
    
    def add_sub_class(self, class_name: str, cache: "ClassCache"):
        self.sub_classes[class_name] = cache