#!/usr/bin/env python3
from joern_processor import JoernProcessor

def main():
    ip = "127.0.0.1:8080"
    project = "/home/cslab/thesis_olek_joern/Dataset/wsvd-bench/src/main/java/pt/uc/dei/wsvdbench"
    json = "/home/cslab/thesis_olek_joern/joern_processing/all_methods.json"
    output = "/home/cslab/thesis_olek_joern/joern_processing/output_joern/joern_results.json"

    processor = JoernProcessor(
        ip=ip,
        project_path=project,
        json_path=json,
        output_path=output,
    )
    processor.run()

if __name__ == "__main__":
    main()
