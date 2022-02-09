from asyncio.log import logger
from enum import Enum
from typing import Dict
from .type_info import TypeInfo

class Scope(Enum):
    MODULE = 1
    CLASS = 2
    CLASSFUNCTION = 3
    FUNCTION = 4

class VariableTypeCache:

    def __init__(self, module_path: str) -> None:
        self.module_path: str = module_path # TODO get fully qualified module name
        self.class_scope_name = ""
        self.function_scope_name = ""

        self.module_variables: Dict[str, TypeInfo] = {}
        self.class_variables: Dict[str, TypeInfo] = {}
        self.function_variables: Dict[str, TypeInfo] = {}
        self.previous_scope = Scope.MODULE
        self.current_scope: Scope = Scope.MODULE
    
    def set_class_scope(self, name: str) -> None:
        self.class_scope_name = name
        self.previous_scope = self.current_scope
        self.current_scope = Scope.CLASS

    def leave_class_scope(self):
        self.class_scope_name = ""
        self.previous_scope = Scope.CLASS
        self.current_scope = Scope.MODULE
        self.class_variables.clear()
    
    def set_class_function_scope(self, name):
        self.function_scope_name = name
        self.previous_scope = self.current_scope
        self.current_scope = Scope.CLASSFUNCTION
    
    def leave_class_function_scope(self):
        self.current_scope = self.previous_scope
        self.previous_scope = Scope.CLASSFUNCTION
        self.function_variables.clear()

    
    def set_function_scope(self, name: str):
        self.function_scope_name = name
        self.previous_scope = self.current_scope
        self.current_scope = Scope.FUNCTION

    def leave_function_scope(self):
        self.function_scope_name = ""
        self.function_variables.clear()
        self.current_scope = self.previous_scope
        self.previous_scope = Scope.FUNCTION

    def add_variable(self, variable_name: str, variable_type: TypeInfo):
        scope: Scope = self.current_scope
        if scope == Scope.MODULE:
            self.module_variables[variable_name] = variable_type
        elif scope == Scope.CLASS:
            self.class_variables[variable_name] = variable_type
        else:
            self.function_variables[variable_name] = variable_type


    def get_variable_type(self, variable_name: str, depth: int, subscript_index: int) -> TypeInfo:
        scope: Scope = self.current_scope
        previous_scope: Scope = self.previous_scope
        variable_type: TypeInfo = None
        if scope == Scope.FUNCTION:
            variable_type = self.function_variables.get(variable_name, None)
        
        if previous_scope == Scope.CLASS and variable_type is None:
            variable_type = self.class_variables.get(variable_name, None)
        
        if variable_type is None:
            variable_type = self.module_variables.get(variable_name, None)
        
        if variable_type is None:
            logger.error("Could not find variable [{}] in cache of module {}"
            .format(variable_name, self.module_path))
            return None
        
        variable_type = variable_type.get_type(depth, subscript_index)

        if variable_type is None:
            logger.error("Could not retrieve type of variable [{}] for depth {} and subscript index {}"
            .format(variable_name, depth, subscript_index))
            return None

        return variable_type
    



