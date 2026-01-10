import pandas as pd
import os
import javalang
from pathlib import Path
from collections import defaultdict
import json


class DatasetProcessor:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent.parent
        self.data_root = self.root / "Dataset/wsvd-bench/src/main/java/pt/uc/dei/wsvdbench"
        self.csv_file = self.root / "src/classification/input/bm-lines.csv"
        self.method_labels = defaultdict(lambda: {"real": 0})
        self.df = None

    def load_csv(self):
        self.df = pd.read_csv(self.csv_file)
        print(f"Loaded DataFrame: {self.df}")

    @staticmethod
    def get_max_line(node):
        max_line = node.position.line if hasattr(node, "position") and node.position else 0
        for child in getattr(node, "children", []):
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, "position") and item.position:
                        max_line = max(max_line, item.position.line)
                    if hasattr(item, "children"):
                        max_line = max(max_line, DatasetProcessor.get_max_line(item))
            elif hasattr(child, "position") and child.position:
                max_line = max(max_line, child.position.line)
            elif hasattr(child, "children"):
                max_line = max(max_line, DatasetProcessor.get_max_line(child))
        return max_line

    @staticmethod
    def extract_methods_with_line_ranges(java_code):
        tree = javalang.parse.parse(java_code)
        method_positions = []
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if node.position:
                start_line = node.position.line
                end_line = getattr(node, 'body', None)
                end_line = node.body[-1].position.line if node.body and node.body[-1].position else start_line
                method_positions.append((node.name, start_line, end_line))
        return method_positions

    def process_dataset(self):
        for _, row in self.df.iterrows():
            parent_name = row["parent"]
            version = row["label"]
            service = row["name"]
            file_path = self.data_root / parent_name / "versions" / f"{service}_{version}.java"
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                continue

            line_number = row["line"]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                methods = self.extract_methods_with_line_ranges(code)
            except Exception as e:
                print(f"⚠️ Failed to parse {file_path}: {e}")
                continue

            for method_name, start, end in methods:
                if start <= line_number <= end:
                    key = f"{row['parent']}:{row['name']}:{row['label']}:{method_name}"
                    self.method_labels[key]["real"] = row["Review"]

    def save_results(self, output_file="tool/src/classification/output/method_labels.json"):
        with open(output_file, "w") as f:
            json.dump(self.method_labels, f, indent=2)
        print(f"✅ File {output_file} created successfully.")

    def run(self):
        print(f"Root directory: {self.root}")
        self.load_csv()
        self.process_dataset()
        self.save_results()


if __name__ == "__main__":
    processor = DatasetProcessor()
    processor.run()