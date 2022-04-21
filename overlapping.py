import os
from typing import List, Tuple, Dict
from src.utils import Utils
from matcher import get_file_content, get_reports_in_folder, extract_parameter_info


MINIMUM_OCCURRENCE: int = 1
report_sequences: Dict[str, List[Tuple[str, int, str, int]]] = {}

def find_overlapping_sequences() -> List[Tuple[str, int, str, int, int, List[str]]]:
    """
    Returns list of tuples (module, line_number, sequence, rank, length, reports)
    """
    result_sequences = []

    for report_name in report_sequences:

        current_sequence_list = report_sequences[report_name]

        for sequence_info in current_sequence_list:
            reports: List[str] = []
            overlap_counter = 0
            ranks = []
            lengths = []

            for report, sequence_list in report_sequences.items():
                
                # skip already processed reports
                if report in report_name:
                    continue

                match = get_matching_sequence_in_list(sequence_info, sequence_list)

                if match is not None:
                    reports.append(report)
                    ranks.append(sequence_info[-2])
                    lengths.append(sequence_info[-1])
                    overlap_counter += 1
            
            if overlap_counter > MINIMUM_OCCURRENCE:
                result_entry: Dict = {
                    "module": sequence_info[0],
                    "line": sequence_info[1],
                    "sequence": sequence_info[2],
                    "ranks": ranks,
                    "sequence_lengths": lengths,
                    "overlaps": overlap_counter,
                    "reports": reports
                }
                if not result_entry_exists(result_entry, result_sequences):
                    result_sequences.append(result_entry)
    return result_sequences


def result_entry_exists(entry, result) -> bool:
    for existing_entry in result:
        if entry["module"] == existing_entry["module"]:
            
            entry_exists = entry["sequence"] == existing_entry["sequence"]
            if entry_exists:
                return True

            entry_exists = entry["sequence"] in existing_entry["sequence"]
            if entry_exists:
                return True

            entry_exists = existing_entry["sequence"] in entry["sequence"]
            return entry_exists
    return False
        


def get_matching_sequence_in_list(sequence_info, list) -> Tuple[str, int, str, int]:
    
    output = None
    for info in list:
        if are_sequences_matching(sequence_info, info):
            
            if output is None:
                output = info
            else:
                print("Found duplicate overlap!!!\n {} | {}".
                format(info[0], info[2]))
    return output
        


def are_sequences_matching(sequence_info_1, sequence_info_2) -> bool:
    length = -1
    module = 0
    string = 2

    if (sequence_info_1[module] == sequence_info_2[module]):
        if sequence_info_1[length] < sequence_info_2[length]:
            return sequence_info_1[string] in sequence_info_2[string]
        else:
            return sequence_info_2[string] in sequence_info_1[string]

    return False

def create_sequence_info_list(file_content: List[str]) -> List[Tuple[str, int, str, int, int]]:
    """
    Extracts the module info, line number, string of every sequence, rank, sequence length in the report
    """
    output: List[Tuple[str, int, str, int, int]] = []
    sequence_line_tracker: int = 4
    current_sequence: str = ""
    current_rank: int = 1
    sequence_length: int = extract_parameter_info(file_content[1])[1]

    for index, line in enumerate(file_content):
        
        if index == sequence_line_tracker:
            current_sequence = line
            current_sequence.replace("\n", "")
            current_sequence.replace("\t", "")

            sequence_line_tracker += 7

        if len(line) > 2 and line[-2] == "]":
            line = line.replace("\t\t", "")
            line_parts = line.rsplit("[", 1)

            module = line_parts[0].replace(" in line(s): ", "")
            line_number = line_parts[1].replace("]\n", "")

            print("Extracted ({}, {})".format(module, line_number))
            output.append((module, line_number, current_sequence, current_rank, sequence_length))
            current_rank += 1
    return output


if __name__ == "__main__":
    result_folder: str = "/home/matthias/BachelorThesis/Analysis/Pygram_Analysis_Pytest_7.1.1- 07.04"
    match_result_file: str = os.path.join(result_folder, "overlapping.txt")

    report_folder: str = os.path.join(result_folder, "untyped")

    reports = get_reports_in_folder(report_folder)

    for report in reports:
        content: List[str] = get_file_content(report)
        report_name: str = Utils.get_last_element_of_path(report)
        sequence_info: List[Tuple[str, int, str, int, int]] = create_sequence_info_list(content)
        report_sequences[report_name] = sequence_info
    
    result = find_overlapping_sequences()

    for entry in result:
        rank_sum = 0

        for rank in entry["ranks"]:
            rank_sum += rank
        
        entry["rank_sum"] = rank_sum

    sorted_result = sorted(result, key=lambda d: d['rank_sum']) 
    sorted_result_2 = sorted(sorted_result, key=lambda d: d['overlaps'], reverse=True) 
    pass
    






