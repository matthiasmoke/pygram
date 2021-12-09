import argparse
import os
import sys

from tokenizer import Tokenizer


def create_parser():
    parser = argparse.ArgumentParser(prog="pygram",
                                    description="N-Gram code analysis")
    parser.add_argument("-f", help="Analyse single Python file")
    parser.add_argument("-d", help="Analyse directory")

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


def main():
    if not len(sys.argv[1:]):
        print("For usage information use -h parameter")
    else:
        arguments = create_parser().parse_args()

        if arguments.f is not None:
            path = os.path.abspath(arguments.f)
            if os.path.isfile(path) and path.endswith(".py"):
                tokenizer = Tokenizer(path)
                print(str(tokenizer))

        if arguments.d is not None:
            python_files = get_all_python_files_in_directory(arguments.d)
            for f in python_files:
                print(f) 


def test():
    sample_file = os.getcwd() + '/test_project/samples/try.py'
    tokenizer = Tokenizer(sample_file)
    print(str(tokenizer))

if __name__ == '__main__':
    main()
    #test()