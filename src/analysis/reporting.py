import logging
from decimal import Decimal
import os
from typing import Tuple
from typing import Dict
from typing import List
from itertools import islice
from ..utils import Utils
from .n_gram_model import NGramModel

logger = logging.getLogger("main")


class ReportingService():

    def __init__(
            self,
            language_model: NGramModel,
            token_sequences: Dict,
            reporting_size: int
    ) -> None:
        self.language_model: NGramModel = language_model
        self.reporting_size: int = reporting_size
        self.token_sequences: Dict[str, List[Tuple[str, int]]] = self._convert_token_sequences(token_sequences)
        self.report: List[Tuple[str, Decimal, List[str]]] = []

    def __str__(self) -> str:
        if len(self.report) == 0:
            return "Report is empty"

        output = "-------------------- Pygram Report --------------------\n"
        output += "Gram Size: {}, Sequence Length: {}, Minimum Token Occurrence: {}\n".format(
            self.language_model.gram_size,
            self.language_model.max_sequence_length,
            self.language_model.minimum_token_occurrence
        )
        output += "-------------------------------------------------------\n\n"
        for entry in self.report:
            output += entry[0]
            output += "\n"
            output += "\tProbability: {}\n".format(entry[1])
            output += "\tModules:\n"
            for key, starting_lines in entry[2].items():
                output += "\t\t{} in line(s): {}\n".format(key, Utils.get_list_string(starting_lines))
            output += "\n-------------------------------------------------------\n\n"
        return output

    def generate_report(self) -> List[Tuple[str, Decimal, List[str]]]:
        """
        Retruns a list that contains report entries in the form of a tuple in the form of 
        (sequence string, probability, corresponding modules).
        """
        report: List[Tuple[str, Decimal, List[str]]] = []
        extracted_sequences: List[Tuple[str, Decimal]] = self._extract_sequences_with_lowest_probability()

        for value in extracted_sequences:
            corresponding_modules = self._get_corresponding_modules(value[0])
            report_entry = (value[0], value[1], corresponding_modules)
            report.append(report_entry)

        self.report = report
        return report

    def save_to_file(self, destination: str, name: str) -> None:
        if os.path.isdir(destination):
            report_file = os.path.join(destination, "{}.txt".format(name))

            with open(report_file, "w") as outputfile:
                outputfile.write(str(self))
                outputfile.close()
        else:
            logger.error("Could not save report to destionation {}. Not a directory".format(destination))
            raise RuntimeError("Could not save report!")

    def _get_corresponding_modules(self, sub_sequence: str) -> List[Tuple[str, int, int]]:
        """
        Returns the modules in which a sequence occurs including occurrences and string line number.
        The format is module: [line number]
        """
        output: Dict[str, List[str]] = {}
        for key in self.token_sequences:
            for sequence in self.token_sequences[key]:
                if sub_sequence in sequence[0]:
                    if output.get(key, None) is None:
                        output[key] = [sequence[1]]
                    else:
                        output[key].append(sequence[1])
        return output

    def _extract_sequences_with_lowest_probability(self) -> List[Tuple[str, Decimal]]:
        """
        Sorts the dict of sequences by probability and returns the sequences with the lowest probability
        """
        sorted_by_probability: Dict = self._sort_by_probability(self.language_model.model)
        first_key = next(iter(sorted_by_probability))
        lowest_prob = sorted_by_probability[first_key]
        counter = 0
        for key, value in sorted_by_probability.items():
            if value == lowest_prob:
                counter += 1
            else:
                break

        if self.language_model.gram_size == self.language_model.max_sequence_length:
            return list(islice(sorted_by_probability.items(), 30))

        if len(sorted_by_probability) <= self.reporting_size:
            return list(sorted_by_probability.items())
        else:
            return list(islice(sorted_by_probability.items(), self.reporting_size))

    def _sort_by_probability(self, probability_dict: Dict) -> Dict:
        return {k: v for k, v in sorted(probability_dict.items(), key=lambda item: item[1])}

    def _convert_token_sequences(self, token_sequences: Dict) -> Dict[str, List[Tuple[str, int]]]:
        """
        Converts a Dict which contains the sequences as List of tokens to a Dict
        which contains tuples with the sequences as strings and the starting line number
        """
        output: Dict[str, List[Tuple[str, int]]] = {}

        for key in token_sequences:
            output[key] = []

            for sequence in token_sequences[key]:
                sequence_string = self._get_sequence_string(sequence)
                starting_line_number = sequence[0][1]
                output[key].append((sequence_string, starting_line_number))

        return output

    def _get_sequence_string(self, sequence: List[Tuple[str, int]]) -> str:
        output: str = ""
        for token in sequence:
            output += token[0]
        return output
