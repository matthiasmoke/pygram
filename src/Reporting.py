from decimal import Decimal
from typing import Dict, List, Tuple
from itertools import islice
from .utils import Utils
from .NGramModel import NGramModel


class ReportingService():

    def __init__(self, language_model: NGramModel, token_sequences: Dict, reporting_size: int) -> None:
        self.language_model: NGramModel = language_model
        self.reporting_size: int = reporting_size
        self.token_sequences: Dict = self._convert_token_sequences(token_sequences)
        self.report = []
    
    def __str__(self) -> str:
        if len(self.report) == 0:
            return "Report is empty"
        
        output = "-------------------- Pygram Report --------------------\n"
        for entry in self.report:
            output += entry[0]
            output += "\n"
            output += "\tProbability: {}\n".format(entry[1])
            output += "\tModules: {}\n".format(Utils.get_list_string(entry[2]))
            output += "-------------------------------------------------------\n"
        return output

    

    def generate_report(self) -> List[Tuple[str, Decimal, List[str]]]:
        report = []
        extracted_sequences: List[Tuple[str, Decimal]] = self._extract_sequences_with_lowest_probability()

        for value in extracted_sequences:
            corresponding_modules = self._get_corresponding_modules(value[0])
            report_entry = (value[0], value[1], corresponding_modules)
            report.append(report_entry)
        
        self.report = report
        return report

    
    def _get_corresponding_modules(self, sub_sequence: str) -> List[str]:
        """
        Returns the modules in which a sequence occurs
        """
        output = []
        for key in self.token_sequences:
            for sequence in self.token_sequences[key]:

                if sub_sequence in sequence:
                    output.append(key)
        return output

    def _extract_sequences_with_lowest_probability(self) -> List[Tuple[str, Decimal]]:
        """
        Sorts the dict of sequences by probability and returns the sequences with the lowest probability
        """
        sorted_by_probability: Dict = self._sort_by_probability(self.language_model.model)
        
        if (len(sorted_by_probability) <= self.reporting_size):
            return list(sorted_by_probability.items())
        else:
            return list(islice(sorted_by_probability.items(), self.reporting_size))

    
    def _sort_by_probability(self, probability_dict: Dict) -> Dict:
        return {k: v for k, v in sorted(probability_dict.items(), key=lambda item: item[1])}

    def _convert_token_sequences(self, token_sequences: Dict) -> Dict:
        """
        Converts a Dict which contains the sequences as List of tokens to a Dict
        which contains the sequences as strings
        """
        output: Dict = {}

        for key in token_sequences:
            output[key] = []

            for sequence in token_sequences[key]:
                output[key].append(Utils.get_sequence_string(sequence))

        return output