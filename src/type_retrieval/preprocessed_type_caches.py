from typing import Dict, List

from .import_cache import ImportCache
from .type_info import TypeInfo
import logging

logger = logging.getLogger("main")

class TypeCache: 

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._current_import_cache: ImportCache = None
        self.modules: Dict[str, FileCache] = {}
    
    def add_file_cache(self, module_path: str, cache: "FileCache") -> None:
        self.modules[module_path] = cache
    
    def set_current_import_cache(self, import_cache: ImportCache) -> None:
        self._current_import_cache = import_cache
    
    def get_return_type_of_function(self, function_name: str) -> TypeInfo:
        """
        Gets the return type of a given function 
        """
        caches: List[FileCache] = self._get_file_caches_for_name(function_name)
        for cache in caches:
            return_type = cache.get_function_type(function_name)

            if return_type is not None:
                return return_type
        logger.error("Could not find function {} for module {} in type cache"
        .format(function_name, self._current_import_cache.get_module))
        return None
    
    def get_return_type(self, function_name: str, class_name: str = None) -> TypeInfo:
        if class_name is not None:
            return self._get_return_type_of_class_function(function_name, class_name)
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
            .format(function_name, self._current_import_cache.get_module()))
        elif len(potential_modules) == 0:
            logger.error("Could not find matching modules for funcion {} in {}"
            .format(function_name, self._current_import_cache.get_module()))

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
        type_name: str = type_info.get_label()
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
                .format(type_name, self._current_import_cache.get_module()))
            elif len(potential_modules) == 0:
                logger.error("Could not find matching modules for type {} in {}"
                .format(type_name, self._current_import_cache.get_module()))
            type_info.set_fully_qualified_name("{}{}".format(module_path, type_name))
        logger.error("Can not determine module for empty type")
    
    def _get_return_type_of_class_function(self, function_name: str, class_name: str) -> TypeInfo:
        caches: List[FileCache] = self._get_file_caches_for_name(class_name)
        for cache in caches:
            return_type = cache.get_class_function_type(function_name, class_name)
            if return_type is not None:
                return return_type
        
        logger.error("Could not find function {} for class {} in module {} in type cache"
        .format(function_name, class_name, self._current_import_cache.get_module()))
        return None

    def _get_return_type_of_function(self, function_name: str) -> TypeInfo:
        caches: List[FileCache] = self._get_file_caches_for_name(function_name)
        for cache in caches:
            return_type = cache.get_function_type(function_name)
            if return_type is not None:
                return return_type
        logger.error("Could not find function {} for module {} in type cache"
        .format(function_name, self._current_import_cache.get_module()))
        return None

    
    def _get_modules_for_name(self, name: str) -> str:
        """
        Retruns the modules that contain the given class/function name
        """
        imported_modules: List[str] = self._current_import_cache.get_module_imports_for_name(name)
        modules: List[str] = []
        modules += imported_modules

        current_module: str = self._current_import_cache.get_module()
        if self.module_contains_type(current_module, name):
            modules.append(current_module)
        elif self.module_contains_function(current_module, name):
            modules.append(current_module)
        
        return modules

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
    
    def contains_type(self, type_name: str) -> bool:
        for key, value in self._class_cache.items():
            contains_type: bool = value.contains_type(type_name)
            if contains_type is True:
                return True
        return False
    
    def contains_function(self, function_name: str) -> bool:
        for key in self.function_cache:
            if key == function_name:
                return True

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
    
    def contains_type(self, type_name: str) -> bool:
        if self.type == type_name:
            return True
        else:
            for key in self.sub_classes:
                if key == type_name:
                    return True
        return False

    def get_function_type(self, function_name: str) -> TypeInfo:
        type: TypeInfo = self.functions.get(function_name, None)
        if type is None:
            logger.error("Could not find function {} in class {}".format(function_name, self.type))
        return type
    