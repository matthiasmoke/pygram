import os
from typing import List
import ast
import builtins
import types
import string
import random
from _ast import Attribute, Name, Subscript, Tuple

class Utils:

    def __init__(self) -> None:
        self.builtin_functions: List[str] = []

    def is_not_a_builtin_function(self, name: str) -> bool:
        if len(self.builtin_functions) == 0:
            self.builtin_functions = [name for name, obj in vars(builtins).items() if isinstance(obj, types.BuiltinFunctionType)]
        return name not in self.builtin_functions

    @staticmethod
    def get_random_string(length: int) -> str:
       return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    
    @staticmethod
    def get_name_from_subscript(node: Subscript) -> str:
        label: str = ""
        if isinstance(node.value, Name):
            label = node.value.id
        elif isinstance(node.value, Attribute):
            label = Utils.get_full_name_from_attribute_node(node.value)
        return label
    
    def get_names_from_tuple(node: Tuple, names: List[str]) -> List[str]:
        for child in node.elts:
            if isinstance(child, Tuple):
                Utils.get_names_from_tuple(child, names)
            else:
                names.append(child.id)

    @staticmethod
    def get_all_python_files_in_directory(path) -> List[str]:
        """
        Returns a list of all Python files in given directory and subdirectories
        """
        output: List[str] = []

        if (os.path.isdir(path)):
            for root, dirs, files in os.walk(path):
                if "/venv/" not in str(root):
                    for file in files:
                        if file.endswith(".py"):
                            output.append(os.path.join(root,file))
        else:
            raise NotADirectoryError("Given path does not exist or is not a directory")
        
        return output
    
    @staticmethod
    def load_syntax_tree(path: str, use_type_info: bool):
        if os.path.isfile(path):
            with open(path, "r") as source:
                tree = ast.parse(source.read(), type_comments=use_type_info)
                return tree
        return None
    
    @staticmethod
    def get_last_element_of_path(path: str) -> str:
        return os.path.basename(os.path.normpath(path))
    
    @staticmethod
    def get_only_project_path(path_to_project: str, complete_path: str) -> str:
        """
        Returns a path with its root being the currently analysed project.
        (Removes its absolute location, like /home/user/...)
        """
        path_to_remove: str = os.path.split(path_to_project)[0] + "/"
        result: str = complete_path.replace(path_to_remove, "")
        return result
    
    @staticmethod
    def generate_dotted_module_path(path: str) -> str:
        """
        Creates dotted module path from regular file path
        """
        # cut ending of python file
        path: str = path[0:(len(path) - 3)]
        # replace slashes with dots 
        path = path.replace("/", ".")
        return path

    
    @staticmethod
    def get_list_string(list: List[str]) -> str:
        output: str = "["

        for i in range(0, len(list)):
            value = list[i]
            if isinstance(value, int):
                value = str(value)
            output += value

            if i < len(list) - 1:
                output += ", "
        output += "]"
        return output
    
    @staticmethod
    def create_full_class_name(name_stack: List[str]) -> str:
        """
        Creates the full class name out of a list of nested classes. 
        For a list [Outer, Inner] the function returns Outer.Inner
        """
        output: str = ""
        for index, item in enumerate(name_stack):
            if index < len(name_stack) - 1:
                output += "{}.".format(item)
            else:
                output += item
        return output
    
    @staticmethod
    def get_full_name_from_attribute_node(node: Attribute) -> str:
        """
        Constructs the complete variable or function path from an attribute node.
        Is used for nested calls, e.g. for cases like os.path.abspath or self.SomeInnerClass
        """
        
        name: str = node.attr
        prefix: str = ""
        if isinstance(node.value, Name):
            prefix = node.value.id
        elif isinstance(node.value, Attribute):
            prefix = Utils.get_full_name_from_attribute_node(node.value)
        
        if prefix == "":
            return name
        else:
            return "{}.{}".format(prefix, name)

