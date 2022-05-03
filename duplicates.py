import ast
import os
from _ast import FunctionDef, ClassDef, AsyncFunctionDef
from typing import List
from typing import Dict
from src.utils import Utils

function_names: Dict[str, int] = {}
function_counter: int = 0

def analyse_file(filepath: str):
    tree = None
    if os.path.isfile(filepath):
        with open(filepath, "r") as source:
            tree = ast.parse(source.read())
    
    if tree is not None:
        for node in tree.body:
            if isinstance(node, FunctionDef) or isinstance(node, AsyncFunctionDef):
                process_function(node)
            if isinstance(node, ClassDef):
                analyse_class(node)

def process_function(function_def: FunctionDef):
    global function_names, function_counter
    name: str = function_def.name
    function_counter += 1

    if function_names.get(name, None) is None:
        function_names[name] = 0
    
    function_names[name] += 1

def analyse_class(class_def: ClassDef):
    for node in class_def.body:
        if isinstance(node, FunctionDef) or isinstance(node, AsyncFunctionDef):
            process_function(node)
        elif isinstance(node, ClassDef):
            analyse_class(node)

if __name__ == "__main__":
    path_to_project: str = "/home/matthias/Projects/pytest/src"
    files: List[str] = Utils.get_all_python_files_in_directory(path_to_project)

    for file in files:
        analyse_file(file)

    duplicate_counter: int = 0
    function_output: str = ""
    for key, value in function_names.items():
        if value > 1:

            if not key.startswith("__"):
                duplicate_counter += value
            function_output += "\t - {}: {}\n".format(key, str(value))
    
    output: str = "Total number of functions in the project: {}\n".format(function_counter)
    output += "Duplicate functions (total: {}):\n".format(duplicate_counter)
    output += function_output
    print(output)





