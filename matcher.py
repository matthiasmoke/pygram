from decimal import Decimal
import os
from typing import List, Tuple
from src.utils import Utils


def get_reports_in_folder(path: str) -> List[str]:
    output: List[str] = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".txt"):
                output.append(os.path.join(root,file))
    return output

def get_file_content(path: str) -> List[str]:
    content: List[str] = None
    with open(path, "r") as input:
        content = input.readlines()
    return content

def extract_parameter_info(line: str) -> List[int]:
    # WARNING, only works with single digits as parameters
    parameters: List[int] = []
    for i in range(0, len(line)):
        if line[i].isdigit():
            parameters.append(int(line[i]))
    return parameters

def extract_match_info(file_content: List[str]) -> List[Tuple[str, int]]:
    """
    Extracts the line number and module info of every sequence in the report
    """
    output: List[Tuple[str, int]] = []
    for line in file_content:
        if len(line) > 2 and line[-2] == "]":
            line = line.replace("\t\t", "")
            line_parts = line.rsplit("[", 1)

            module = line_parts[0].replace(" in line(s): ", "")
            line_number = line_parts[1].replace("]\n", "")

            print("Extracted ({}, {})".format(module, line_number))
            output.append((module, line_number))
    return output


def calculate_match_ratio(untyped_info, typed_info) -> float:
    matches: int = 0
    total: int = len(untyped_info)

    for tuple in typed_info:
        if tuple in untyped_info:
            matches += 1
    
    ratio: float = matches/total
    return ratio

if __name__ == "__main__":

    matching_result: str = "-------------------- Pygram Report Matchings --------------------"

    result_folder: str = "/home/matthias/BachelorThesis/Analysis/Pygram_Analysis_Pytest_7.1.1- 07.04"
    match_result_file: str = os.path.join(result_folder, "report_matching.txt")

    typed_report_folder: str = os.path.join(result_folder, "typed")
    untyped_report_folder: str = os.path.join(result_folder, "untyped")

    typed_reports: List[str] = get_reports_in_folder(typed_report_folder)
    untyped_reports: List[str] = get_reports_in_folder(untyped_report_folder)

    typed_reports.sort()
    untyped_reports.sort()


    for i in range(0, len(untyped_reports)):
        untyped_file: str = untyped_reports[i]
        untyped_file_name = Utils.get_last_element_of_path(untyped_file)
        typed_file: str = typed_reports[i]

        if untyped_file_name not in typed_file:
            raise RuntimeError("Files are not matching!!")
        
        typed_content: List[str] = get_file_content(typed_file)
        untyped_content: List[str] = get_file_content(untyped_file)
        # gram size, sequence length, min token occurrence
        parameter_info: List[int] = extract_parameter_info(typed_content[1])

        typed_match_info: List[Tuple[str, int]] = extract_match_info(typed_content)
        untyped_match_info: List[Tuple[str, int]] = extract_match_info(untyped_content)

        match_ratio: float = calculate_match_ratio(untyped_match_info, typed_match_info)
        match_ratio = round(match_ratio, 3) * 100

        matching_result += "\n Gram Size: {}, Sequence Length: {}, Min. Token Occurrence: {}  |  {}% \n".format(
            parameter_info[0], parameter_info[1], parameter_info[2], match_ratio)
    
    with open(match_result_file, "w") as outputfile:
        outputfile.write(matching_result)
        outputfile.close()

        




