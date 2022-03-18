import logging
from enum import Enum
from typing import Dict, List

from .preprocessed_type_caches import TypeCache
from .type_info import TypeInfo
from ..utils import Utils

logger = logging.getLogger("main")

class Scope(Enum):
    MODULE = 1
    CLASS = 2
    FUNCTION = 3

class VariableTypeCache:

    def __init__(self, module_path: str, project_type_cache: TypeCache) -> None:
        self.module_path: str = module_path
        self._project_type_cache: TypeCache = project_type_cache

        self.scope_stack: List[Scope] = []
        self.class_scope_stack: List[str] = []
        self.function_scope_stack: List[str] = []

        self.module_variables: Dict[str, TypeInfo] = {}
        self.class_scopes: Dict[str, Dict[str, TypeInfo]] = {}
        self.function_scopes: Dict[str, Dict[str, TypeInfo]] = {}

    
    def set_class_scope(self, name: str) -> None:
        self.scope_stack.append(Scope.CLASS)
        self.class_scope_stack.append(name)
        
        # create cache for class and add self type
        class_type = TypeInfo(label=name)
        self._project_type_cache.populate_type_info_with_module(class_type)
        self.class_scopes[name] = {}
        self.class_scopes[name]["self"] = class_type

    def leave_class_scope(self):
        left_class: str = self.class_scope_stack[-1]
        del self.class_scopes[left_class]
        self.class_scope_stack.pop()
        self.scope_stack.pop()
    
    def set_function_scope(self, name: str):
        self.scope_stack.append(Scope.FUNCTION)
        if name in self.function_scope_stack:
            name += "_{}".format(Utils.get_random_string(5))
        self.function_scope_stack.append(name)
        self.function_scopes[name] = {}

    def leave_function_scope(self):
        left_function_scope = self.function_scope_stack[-1]
        del self.function_scopes[left_function_scope]
        self.function_scope_stack.pop()
        self.scope_stack.pop()

    def add_variable(self, variable_name: str, variable_type: TypeInfo):
        scope: Scope = self._get_current_scope()
        if scope == Scope.MODULE:
            self.module_variables[variable_name] = variable_type
        elif scope == Scope.CLASS:
            self._set_class_variable(variable_name, variable_type)
        else:
            if self.function_scope_stack[-1] == "__init__" and self._get_previous_scope() == Scope.CLASS:
                self._set_class_variable(variable_name, variable_type)
            else:
                self._set_function_variable(variable_name, variable_type)

    def get_variable_type(self, variable_name: str, depth: int, subscript_index: int) -> TypeInfo:
        scope: Scope = self._get_current_scope()
        previous_scope: Scope = self._get_previous_scope()
        variable_type: TypeInfo = None
        if scope == Scope.FUNCTION:
            variable_type = self._get_function_variable(variable_name)
        
        if previous_scope == Scope.CLASS and variable_type is None:
            variable_type = self._get_class_variable(variable_name)
        
        if variable_type is None:
            variable_type = self.module_variables.get(variable_name, None)
        
        if variable_type is None:
            logger.warning("Could not find variable [{}] in cache of module {}"
            .format(variable_name, self.module_path))
            return None
        
        variable_type = variable_type.get_type(depth, subscript_index)

        if variable_type is None:
            logger.warning("Could not retrieve type of variable [{}] for depth {} and subscript index {}"
            .format(variable_name, depth, subscript_index))
            return None

        return variable_type
    
    def _get_inner_class_path(self, name: str) -> str:
        output: str = ""
        if name is not None:
            for key in self.class_scopes:
                output += "{}.".format(key)
            output += name
        return output
    
    def _get_current_scope(self) -> Scope:
        if len(self.scope_stack) == 0:
            return Scope.MODULE
        return self.scope_stack[-1]
    
    def _get_previous_scope(self) -> Scope:
        if len(self.scope_stack) < 2:
            return Scope.MODULE
        return self.scope_stack[-2]
    
    def _set_class_variable(self, variable_name: str, type_info: TypeInfo) -> None:
        current_class = self.class_scope_stack[-1]
        self.class_scopes[current_class][variable_name] = type_info
    
    def _get_class_variable(self, variable_name: str) -> TypeInfo:
        current_class = self.class_scope_stack[-1]
        return self.class_scopes[current_class].get(variable_name, None)
    
    def _get_function_variable(self, name: str) -> TypeInfo:
        for scope in reversed(self.function_scope_stack):
            variable = self.function_scopes[scope].get(name, None)
            if variable is not None:
                return variable
        return None

    def _set_function_variable(self, variable_name: str, variable_type: TypeInfo) -> None:
        current_function = self.function_scope_stack[-1]
        self.function_scopes[current_function][variable_name] = variable_type