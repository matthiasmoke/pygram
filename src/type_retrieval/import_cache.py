from typing import List, Dict

class ImportCache():
    def __init__(self) -> None:
        self._imports: Dict[str, List[str]] = {}
        # maps aliases to real class names. Ignores cases where the "as" directive names to types equally
        self._as_imports: Dict[str, str] = {}

    def add_import(self, module_path: str, imported_entities: List[str]) -> None:
        if self._imports.get(module_path, None) is None:
            self._imports[module_path] = imported_entities
        else:
            self._imports[module_path] += imported_entities
    
    def add_import_alias(self, as_name: str, entity_name: str) -> None:
        self._as_imports[as_name] = entity_name
    
    def get_module_imports_for_name(self, name: str) -> List[str]:
        """
        Retruns the imported modules that contain the given class/function name.
        """
        modules: List[str] = []
        modules_found_for_name_part: List[str] = []

        # convert alias to original class name
        module: str = self._as_imports.get(name, None)
        if module is not None:
            name = module
        
        for module_path, modules_list in self._imports.items():
            # Check if name is in imported modules
            if name in modules_list:
                modules.append(module_path)
            elif self._name_has_part_of_imported_module(name, modules_list):
                modules_found_for_name_part.append(module_path)
        
        if len(modules) == 0:
            modules += modules_found_for_name_part
        
        return modules
    
    def _name_has_part_of_imported_module(self, name: str, modules: List[str]) -> bool:
        for module in modules:
            if module in name:
                return True
        return False

        

        
