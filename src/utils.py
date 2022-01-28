import os
from typing import List

class Utils:

    @staticmethod
    def get_all_python_files_in_directory(path) -> List:
        output: List = []

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
    def get_sub_path(starting_dir: str, path: str) -> str:
        parts: List = path.split(starting_dir)
        output: str = ""

        if len(parts) > 1:
            output += starting_dir
            output += parts[1]

            for index in range(2, len(parts) - 1):
                output += parts[index]
        return output
    
    @staticmethod
    def get_sequence_string(sequence: List[str]) -> str:
        output: str = ""
        for token in sequence:
            output += token
        return output
    
    @staticmethod
    def get_list_string(list: List[str]) -> str:
        output = "["

        for i in range(0, len(list)):
            output += list[i]

            if i < len(list) - 1:
                output += ", "
        output += "]"
        return output

