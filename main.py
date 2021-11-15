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

def main():
    if not len(sys.argv[1:]):
        print("For usage information use -h parameter")
    else:
        arguments = create_parser().parse_args()

        if arguments.f is not None:
            path = os.path.abspath(arguments.f)
            if os.path.isfile(path) and path.endswith(".py"):
                tokenizer = Tokenizer(path)

        if arguments.d is not None:
            pass


def test():
    sample_file = os.getcwd() + '/test_project/samples/sample_file.py'
    tokenizer = Tokenizer(sample_file)
    print(str(tokenizer))

if __name__ == '__main__':
    test()