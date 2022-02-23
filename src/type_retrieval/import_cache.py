from typing import List, Dict
from _ast import ImportFrom, Import

class ImportCache():
    def __init__(self, module_path: str, available_modules: List[str]) -> None:
        self._module_path: str = module_path
        self._module_path_parts = module_path.split(".")
        self._module_level = len(self._module_path_parts) - 1
        self._imports: Dict[str, List[str]] = {}
        self._available_modules = available_modules
        # maps aliases to real class names. Ignores cases where the "as" directive names to types equally
        self._as_imports: Dict[str, str] = {}
    
    def get_module(self) -> str:
        return self._module_path
    
    def add_import(self, node: ImportFrom) -> None:
        if isinstance(node, ImportFrom):
            self._process_import_from(node)
        else:
            self._process_import(node)
            
    def get_module_imports_for_name(self, name: str) -> str:
        """
        Retruns the imported modules that contain the given class/function name
        """
        modules: List[str] = []

        # convert alias to original class name
        module: str = self._as_imports.get(name, None)
        if module is not None:
            name = module
        
        for key, value in self._imports.items():
            if name in value:
                modules.append(key)
        
        return modules
    
    def _process_import_from(self, node: ImportFrom):
        module: str = node.module
        level: int = node.level

        complete_path = self._generate_complete_path(module, level)
        classes: List[str] = []
        for name in node.names:
            classes.append(name.name)
            if name.asname is not None and name.asname != "None":
                self._as_imports[name.asname] = name.name
        
        self._imports[complete_path] = classes

    def _process_import(self, node: Import):
        for module in node.names:
            name: str = module.name
            self._imports[name] = [ name ]

            if module.asname:
                self._as_imports[module.asname] = name 

    def _generate_complete_path(self, module_path_postfix: str, level: int) -> str:
        """
        Generates the complete path out of the relative import path and level
        """
        prefix: str = ""
        complete_path: str = ""
        # if level equals 1, the imported module lies in the same directory as the currently processed module
        if level == 1:
            level = self._module_level

        for i in range (0, level):
            prefix += "{}.".format(self._module_path_parts[i])
        complete_path = "{}{}".format(prefix, module_path_postfix)

        if complete_path not in self._available_modules:
            # if the generated path is not present in the available modules, it is a native import
            return module_path_postfix
        return complete_path
        

        
