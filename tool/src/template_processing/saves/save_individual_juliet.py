import os
import json
import time

from src.java_processing.juliet_processor import JulietProcessor


class SaveIndividualJuliet:
    """
    Handles saving of LLM assessment results for the Juliet dataset.
    Mirrors SaveIndividual but uses the Juliet directory structure:

        {
          "s01": {
            "CWE89_SQL_Injection__Environment_executeBatch_01.java": {
              "bad":    "",
              "goodB2G": ""
            },
            ...
          },
          "s02": { ... },
          ...
        }
    """

    def __init__(self, root_folder: str, workdir: str):
        self.root_folder = root_folder
        self.workdir = workdir
        self.structure = {}
        self.filepaths = {}
        os.makedirs(self.workdir, exist_ok=True)

    def run(self):
        """Build the empty result structure and create the output JSON file."""
        self._build_structure()

        base_name = "template_practices_result_"
        existing = [
            f for f in os.listdir(self.workdir)
            if f.startswith(base_name) and f.endswith(".json")
        ]
        indices = []
        for fname in existing:
            try:
                indices.append(int(fname.replace(".json", "").split("_")[-1]))
            except ValueError:
                pass

        i = max(indices, default=0) + 1
        output_path = os.path.join(self.workdir, f"{base_name}{i}.json")
        self.filepaths["template_practices"] = output_path

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.structure, f, indent=4)

    def _build_structure(self):
        """
        Walk the Juliet CWE89 folder and build the skeleton JSON
        with empty strings for each (file, method) pair.
        """
        processor = JulietProcessor(self.root_folder)
        self.structure = {}

        for subfolder, filename, methods in processor.iter_files_and_methods():
            if subfolder not in self.structure:
                self.structure[subfolder] = {}
            self.structure[subfolder][filename] = {
                method_name: "" for method_name, _, _ in methods
            }

    def save_individual_practices(self, subfolder: str, filename: str,
                                   method_name: str, question_answers: dict):
        """Write the LLM result for a single method into the JSON file."""
        filepath = self.filepaths["template_practices"]

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if subfolder not in data:
            data[subfolder] = {}
        if filename not in data[subfolder]:
            raise KeyError(f"File {filename} not found in structure under {subfolder}")
        if method_name not in data[subfolder][filename]:
            raise KeyError(f"Method {method_name} not found in {filename}")

        data[subfolder][filename][method_name] = question_answers

        time.sleep(1)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
