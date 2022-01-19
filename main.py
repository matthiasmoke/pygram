import argparse
from ast import parse
import os
import sys
from typing import List

from Tokenizer import Tokenizer
from TokenCountModel import TokenCountModel

use_type_info: bool = True
tokenstream: List = []
gram_size: int = 3
sequence_length: int = 6
token_count_model: TokenCountModel = None


def create_parser():
    parser = argparse.ArgumentParser(prog="pygram",
                                    description="N-Gram code analysis")
    parser.add_argument("-f", help="Analyse single Python file")
    parser.add_argument("-d", help="Analyse directory")
    parser.add_argument("-m", help="Load model from file (.json)")
    parser.add_argument("-t", help="This flag enables processing of type annotations. The type information added to the tokens")

    return parser

def get_all_python_files_in_directory(path):
    output = []

    if (os.path.isdir(path)):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    output.append(os.path.join(root,file))
    else:
        raise NotADirectoryError("Given path does not exist or is not a directory")
    
    return output


def load_token_count_model_from_file(path):
    global token_count_model
    file_path = os.path.abspath(path)

    if os.path.isfile(file_path) and file_path.endswith(".json"):
        model = TokenCountModel.load_from_file(file_path)
        if model is None:
            print("Could not load file")
        else:
            token_count_model = model
    else:
        print("Not a .json file!")


def tokenize_project(directory):
    global tokenstream, use_type_info
    python_files = get_all_python_files_in_directory(directory)
    counter = len(python_files)
    print("Detected {} Python files".format(counter))

    for (index, file) in enumerate(python_files):
        print("[{}/{}] Processing \"{}\"".format(index + 1, counter, file))
        path = os.path.abspath(file)
        if os.path.isfile(path):
            tokenizer = Tokenizer(path, use_type_info)
            file_tokens = tokenizer.get_token_sequences()
            tokenstream += file_tokens
    print("Finished tokenizing project")


def main():
    global tokenstream, gram_size, sequence_length, use_type_info, token_count_model
    if not len(sys.argv[1:]):
        print("For usage information use -h parameter")
    else:
        arguments = create_parser().parse_args()

        if arguments.t is not None:
            use_type_info = True
        
        if arguments.m is not None:
            load_token_count_model_from_file(arguments.m)

        if arguments.f is not None:
            path = os.path.abspath(arguments.f)
            if os.path.isfile(path) and path.endswith(".py"):
                tokenizer = Tokenizer(path, use_type_info)
                print(str(tokenizer))

        if arguments.d is not None:
            tokenize_project(arguments.d)
            token_count_model = TokenCountModel(gram_size, tokenstream, name="Test Model")


def test():
    sample_file = os.getcwd() + '/test_project/samples/minimal.py'
    large_sample = "/home/matthias/Projects/RingABackend/play_sequence.py"
    sample_dir = "/home/matthias/Projects/RingABackend"
    tokenize_project(sample_file)
    model = TokenCountModel(gram_size, tokenstream, name="Test Model")
    model.save_to_file(os.path.abspath("/home/matthias/BachelorThesis/model.json"))


def test_file():
    global tokenstream
    sample_file = os.getcwd() + '/test_project/samples/minimal.py'
    tokenizer = Tokenizer(sample_file, consider_type=False)
    tokenstream = tokenizer.get_token_sequences()
    model = TokenCountModel(gram_size, tokenstream, name="Test Model")
    model.count_tokens()
    model.save_to_file(os.path.abspath("/home/matthias/BachelorThesis/model.json"))

def load_test():
    model_file = os.path.abspath("/home/matthias/BachelorThesis/model.json")
    model = TokenCountModel.load_from_file(model_file)

if __name__ == '__main__':
    #main()
    #test()
    load_test()