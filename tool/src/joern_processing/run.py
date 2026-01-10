#!/usr/bin/env python3
from joern_processor import JoernProcessor
from config import VM_PATH as vm_path
from config import PROJECT_PATH as dataset_path


def main():
    ip = "127.0.0.1:8080"
    project = f"{vm_path}/{dataset_path}"
    json = f"{vm_path}/tool/src/joern_processing/all_methods.json"
    output = f"{vm_path}/tool/src/joern_processing/output_joern/joern_results.json"

    processor = JoernProcessor(
        ip=ip,
        project_path=project,
        json_path=json,
        output_path=output,
    )
    processor.run()

if __name__ == "__main__":
    main()
