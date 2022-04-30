import ast
import os
from _ast import FunctionDef, ClassDef, AsyncFunctionDef
from typing import List
from typing import Dict
from src.utils import Utils

function_names: Dict[str, int] = {}

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
    global function_names
    name: str = function_def.name

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
    
    output = "Duplicate functions:\n"

    for key, value in function_names.items():
        if value > 1:
            output += "\t - {}: {}\n".format(key, str(value))
    
    print(output)





