import json
import re

def convert_practices_to_label_format(input_path, output_path):
    with open(input_path, "r") as f:
        data = json.load(f)

    converted = {}

    for key, value in data.items():
        if "::" not in key:
            continue

        class_file, method = key.split("::")

        # Remover extensão .java
        class_base = class_file.replace(".java", "")

        # Procurar padrão de versão no nome da classe
        match = re.match(r"(.+)_((Vx|vx)[A-Za-z0-9]+)", class_base)
        if match:
            file_name = match.group(1)
            version = match.group(2)
            new_key = f"{file_name}:{version}:{method}"
            converted[new_key] = value
        else:
            # Se não houver versão no nome da classe, ignora
            print(f"⚠️ WARNING: No version found for {key}, skipping this entry.")

    with open(output_path, "w") as f:
        json.dump(converted, f, indent=2)

    print(f"✅ practices_classification.json convertido para formato compatível em: {output_path}")

if __name__ == "__main__":
    input_path = "tool/src/classification/output/practices_classification_1_t1_V7.json"
    output_path = "tool/src/classification/output/practices_classification_labels_format_1_t1_V7.json"
    convert_practices_to_label_format(input_path, output_path)