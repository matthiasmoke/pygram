from typing import List, Dict
from _ast import ImportFrom

class ImportCache():
    def __init__(self, module_path: str) -> None:
        self._module_path: str = module_path
        self._module_path_parts = module_path.split(".")
        self._imports: Dict[str, List[str]] = {}
        # maps aliases to real class names. Ignores cases where the "as" directive names to types equally
        self._as_imports: Dict[str, str] = {}
    
    def get_module(self) -> str:
        return self._module_path
    
    def add_import(self, node: ImportFrom) -> None:
        module: str = node.module
        level: int = node.level

        complete_path = self._generate_complete_path(module, level)
        classes: List[str] = []
        for name in node.names:
            classes.append(name.name)
            if name.asname is not None and name.asname != "None":
                self._as_imports[name.asname] = name.name
        
        self._imports[complete_path] = classes
            
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

    def _generate_complete_path(self, module_path_postfix: str, level: int) -> str:
        prefix: str = ""
        for i in range (0, level):
            prefix += "{}.".format(self._module_path_parts[i])
        return "{}{}".format(prefix, module_path_postfix)
        

        
